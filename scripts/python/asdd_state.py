#!/usr/bin/env python3
"""Shared delivery state for the 15-phase Agentic Spec-Driven Delivery agents (issue #44).

The orchestrator and all 15 phase agents in `.claude/agents/` call this helper to record where a
feature is and what each phase handed off. Until now it did not exist, so the handoff mechanism
`.claude/agents/README.md` calls authoritative never ran and `asdd-orchestrator` could not complete
its first step.

The contract is not invented here: `docs/sdlc/agent-handoff-schema.md` (ADR-0058) already specifies
the state object, the handoff message, the validation rules and this command surface. This module
implements that specification.

  init           --feature ID --title T [--risk-class R] [--spec PATH]
  append-handoff --feature ID --status done|blocked --phase N --agent A --handoff-to H
                 [--artifacts a b ...] [--reason R] [--notes N] [--human-gate]
  show           --feature ID [--json]
  validate       --feature ID          exit 1 when the recorded state violates the schema

State lives at `.agent/delivery/<feature_id>/state.json`, which is gitignored: it is per-run
delivery state, not a repository artefact.

Fail-closed by design. Every validation rule in the schema is enforced on write, and a violation
exits non-zero rather than recording a malformed handoff — a corrupted state file would silently
break the pipeline it exists to make legible.

This script never runs git or gh. Version-control actions belong to scripts/bash/vcs.sh, which
enforces its own refusals (Constitution V; check-corpus C8 asserts no script here runs git).
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = "asdd_state_v2"
# v1 keyed `artifacts` by basename and stored the path as the value. v2 keys by path and stores
# the phase. The two are shaped alike — both are objects of strings — so a v1 file loaded as v2
# renders every artefact inverted and `validate` calls it valid. The version was not bumped when
# the meaning changed, which is the one thing a version exists for (R5-T6).
LEGACY_VERSIONS = ("asdd_state_v1",)
STATUSES = ("done", "blocked")
PHASE_MIN, PHASE_MAX = 0, 14
FEATURE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")


def repo_root():
    d = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    return os.environ.get("ASDD_ROOT", d)


def state_path(feature):
    return os.path.join(repo_root(), ".agent", "delivery", feature, "state.json")


def now():
    return datetime.now(timezone.utc).isoformat()


class SchemaError(Exception):
    pass


def check_feature(feature):
    if not feature or not FEATURE_RE.match(feature):
        raise SchemaError(f"feature id {feature!r} is not a safe identifier")
    return feature


def validate_handoff(h):
    """Every rule from docs/sdlc/agent-handoff-schema.md §Validation rules."""
    if h.get("status") not in STATUSES:
        raise SchemaError(f"status must be one of {STATUSES}, got {h.get('status')!r}")
    phase = h.get("phase")
    if not isinstance(phase, int) or isinstance(phase, bool) or not PHASE_MIN <= phase <= PHASE_MAX:
        raise SchemaError(f"phase must be an int in [{PHASE_MIN}, {PHASE_MAX}], got {phase!r}")
    if not h.get("agent"):
        raise SchemaError("agent is required and must be non-empty")
    if not isinstance(h.get("artifacts"), list):
        raise SchemaError("artifacts must be a list")
    if not h.get("handoff_to"):
        raise SchemaError("handoff_to is required (use 'none (terminal)' for the last phase)")
    if h["status"] == "blocked" and not (h.get("reason") or "").strip():
        raise SchemaError("reason is required when status is blocked")
    if not isinstance(h.get("human_gate"), bool):
        raise SchemaError("human_gate must be a boolean")
    return h


def validate_state(s):
    got = s.get("schema_version")
    if got in LEGACY_VERSIONS:
        raise SchemaError(
            f"this state was written by {got}, whose `artifacts` map was {{basename: path}}. "
            f"{SCHEMA_VERSION} keys it by {{path: phase}}, so the old file renders inverted and "
            f"would validate anyway. Convert it: asdd_state.py migrate --feature "
            f"{s.get('feature_id', '<ID>')}")
    if got != SCHEMA_VERSION:
        raise SchemaError(f"schema_version must be {SCHEMA_VERSION!r}, got {got!r}")
    check_feature(s.get("feature_id"))
    cur = s.get("current_phase")
    if not isinstance(cur, int) or not PHASE_MIN <= cur <= PHASE_MAX:
        raise SchemaError(f"current_phase out of range: {cur!r}")
    if not isinstance(s.get("blocked"), bool):
        raise SchemaError("blocked must be a boolean")
    if not isinstance(s.get("artifacts"), dict):
        raise SchemaError("artifacts must be an object keyed by path")
    if not isinstance(s.get("handoffs"), list):
        raise SchemaError("handoffs must be a list")
    for h in s["handoffs"]:
        validate_handoff(h)
    return s


def load(feature):
    p = state_path(check_feature(feature))
    if not os.path.isfile(p):
        raise SchemaError(f"no delivery state for {feature}. Run: asdd_state.py init --feature {feature} --title ...")
    with open(p, encoding="utf-8") as fh:
        return validate_state(json.load(fh))


def save(s):
    p = state_path(s["feature_id"])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    s["updated_at"] = now()
    validate_state(s)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, p)          # atomic: a crash mid-write never leaves a half-parsed state
    return p


def cmd_init(a):
    check_feature(a.feature)
    p = state_path(a.feature)
    if os.path.exists(p) and not a.force:
        print(f"delivery state already exists: {p} (use --force to reset)", file=sys.stderr)
        return 1
    s = {
        "schema_version": SCHEMA_VERSION,
        "feature_id": a.feature,
        "title": a.title,
        "risk_class": a.risk_class,
        "spec": a.spec,
        "current_phase": 0,
        "blocked": False,
        "started_at": now(),
        "updated_at": now(),
        "artifacts": {},
        "handoffs": [],
    }
    print(save(s))
    return 0


def cmd_append(a):
    s = load(a.feature)
    # Two guards, two flags. One `--force` cleared both, so an operator overriding a block also
    # silently rewound the phase order, and neither decision was recorded as its own (R5-T6).
    if s["blocked"] and not a.force_unblock:
        last = s["handoffs"][-1] if s["handoffs"] else {}
        print(f"pipeline is blocked at phase {last.get('phase')}: {last.get('reason')}\n"
              f"resolve it and re-run, or pass --force-unblock to override deliberately",
              file=sys.stderr)
        return 1
    # Against the HIGHEST phase ever recorded, not the last one. Comparing with the last gave the
    # guard an escape one entry deep: 5 → 3 (forced) → 4 replaced the yardstick with the forced
    # entry, so the unforced step back to 4 passed and `validate` called the result valid.
    high = max((h["phase"] for h in s["handoffs"]), default=None)
    if high is not None and a.phase <= high and not a.force_order:
        print(f"phase {a.phase} would not advance past phase {high}, the furthest already "
              f"recorded: the 15-phase lifecycle runs forward. A re-run of the same phase, or a "
              f"deliberate jump backwards, needs --force-order.", file=sys.stderr)
        return 1
    h = validate_handoff({
        "status": a.status,
        "phase": a.phase,
        "agent": a.agent,
        "artifacts": a.artifacts or [],
        "handoff_to": a.handoff_to,
        "reason": a.reason or "",
        "notes": a.notes or "",
        "human_gate": bool(a.human_gate),
        "timestamp": now(),
    })
    s["handoffs"].append(h)
    s["current_phase"] = h["phase"]
    s["blocked"] = h["status"] == "blocked"
    # Keyed by PATH. Keying by basename silently dropped artefacts: two phases each producing a
    # `spec.md` left only the later one, and the state is what the FINAL-REPORT reads.
    for art in h["artifacts"]:
        s["artifacts"][art] = h["phase"]
    save(s)
    gate = " [HUMAN GATE]" if h["human_gate"] else ""
    print(f"phase {h['phase']} {h['status']} — {h['agent']} → {h['handoff_to']}{gate}")
    if h["status"] == "blocked":
        print(f"BLOCKED: {h['reason']}", file=sys.stderr)
        return 2                # distinct exit code: the orchestrator halts rather than advancing
    return 0


def cmd_migrate(a):
    """Convert a v1 state to v2 without losing anything.

    The previous advice was `init --force`, which writes over `handoffs`, `artifacts` and
    `current_phase` — and the handoff list is what Constitution VII reads as traceability and what
    the final report consumes. Telling an adopter mid-delivery to destroy it was the more damaging
    of the two available outcomes, and the conversion was mechanical all along: every v1 handoff
    already carries its phase and the artefacts it produced, so {path: phase} is recoverable by
    walking the list (R6-T4)."""
    p = state_path(check_feature(a.feature))
    if not os.path.isfile(p):
        print(f"no delivery state for {a.feature}: {p}", file=sys.stderr)
        return 1
    with open(p, encoding="utf-8") as fh:
        s = json.load(fh)
    got = s.get("schema_version")
    if got == SCHEMA_VERSION:
        print(f"{a.feature}: already {SCHEMA_VERSION}; nothing to migrate")
        return 0
    if got not in LEGACY_VERSIONS:
        print(f"cannot migrate schema_version {got!r}: not a known earlier version", file=sys.stderr)
        return 1

    handoffs = s.get("handoffs")
    if not isinstance(handoffs, list):
        print("cannot migrate: `handoffs` is missing or not a list, so no phase can be "
              "attributed to any artefact", file=sys.stderr)
        return 1

    rebuilt = {}
    for h in handoffs:
        phase = h.get("phase")
        if not isinstance(phase, int):
            print(f"cannot migrate: a handoff carries no integer phase ({phase!r}); refusing to "
                  f"guess which phase produced its artefacts", file=sys.stderr)
            return 1
        for art in h.get("artifacts") or []:
            rebuilt[art] = phase

    # Cross-check against what v1 recorded. v1 lost artefacts to basename collisions, so the old
    # map can hold FEWER paths than the handoffs do; it must never hold one they do not.
    old_paths = set()
    if isinstance(s.get("artifacts"), dict):
        old_paths = {v for v in s["artifacts"].values() if isinstance(v, str)}
    orphans = sorted(old_paths - set(rebuilt))
    if orphans:
        print("cannot migrate: these artefacts are recorded in the v1 map but named by no handoff, "
              "so no phase can be attributed to them without guessing:", file=sys.stderr)
        for o in orphans:
            print(f"  {o}", file=sys.stderr)
        return 1

    recovered = len(rebuilt) - len(old_paths)
    s["artifacts"] = rebuilt
    s["schema_version"] = SCHEMA_VERSION
    save(s)
    print(f"{a.feature}: migrated {got} → {SCHEMA_VERSION}; "
          f"{len(handoffs)} handoff(s) kept, {len(rebuilt)} artefact(s) keyed by path"
          + (f" ({recovered} recovered that the old basename map had lost)" if recovered > 0 else ""))
    return 0


def cmd_show(a):
    s = load(a.feature)
    if a.json:
        json.dump(s, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return 0
    print(f"{s['feature_id']} — {s['title']}")
    print(f"  risk class:    {s.get('risk_class') or '(unset)'}")
    print(f"  spec:          {s.get('spec') or '(unset)'}")
    print(f"  current phase: {s['current_phase']}{'  BLOCKED' if s['blocked'] else ''}")
    print(f"  started:       {s['started_at']}")
    print(f"  handoffs:      {len(s['handoffs'])}")
    for h in s["handoffs"]:
        gate = " [HUMAN GATE]" if h["human_gate"] else ""
        line = f"    {h['phase']:>2}  {h['status']:<7} {h['agent']} → {h['handoff_to']}{gate}"
        print(line)
        if h["status"] == "blocked":
            print(f"        reason: {h['reason']}")
    if s["artifacts"]:
        print("  artifacts:")
        for path, phase in sorted(s["artifacts"].items()):
            print(f"    phase {phase}: {path}")
    return 0


def cmd_validate(a):
    load(a.feature)
    print(f"{a.feature}: delivery state valid ({SCHEMA_VERSION})")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="create the delivery state for a feature")
    i.add_argument("--feature", required=True)
    i.add_argument("--title", required=True)
    i.add_argument("--risk-class", default="")
    i.add_argument("--spec", default="")
    i.add_argument("--force", action="store_true")
    i.set_defaults(fn=cmd_init)

    h = sub.add_parser("append-handoff", help="record one phase's handoff")
    h.add_argument("--feature", required=True)
    h.add_argument("--status", required=True, choices=STATUSES)
    h.add_argument("--phase", required=True, type=int)
    h.add_argument("--agent", required=True)
    h.add_argument("--handoff-to", required=True, dest="handoff_to")
    h.add_argument("--artifacts", nargs="*", default=[])
    h.add_argument("--reason", default="")
    h.add_argument("--notes", default="")
    h.add_argument("--human-gate", action="store_true", dest="human_gate")
    h.add_argument("--force-order", action="store_true", dest="force_order",
                   help="record a phase that does not advance past the furthest already recorded")
    h.add_argument("--force-unblock", action="store_true", dest="force_unblock",
                   help="append even though the pipeline is blocked")
    h.set_defaults(fn=cmd_append)

    g = sub.add_parser("migrate", help="convert an earlier schema version in place, losing nothing")
    g.add_argument("--feature", required=True)
    g.set_defaults(fn=cmd_migrate)

    s = sub.add_parser("show", help="print the delivery state")
    s.add_argument("--feature", required=True)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_show)

    v = sub.add_parser("validate", help="validate the recorded state against the schema")
    v.add_argument("--feature", required=True)
    v.set_defaults(fn=cmd_validate)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except SchemaError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: delivery state is not valid JSON: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
