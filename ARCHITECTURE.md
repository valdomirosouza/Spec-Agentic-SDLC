<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Architecture of this corpus

> This describes **this repository** — the corpus itself. Two neighbouring documents describe the
> repository that *adopts* it: [`docs/architecture.md`](docs/architecture.md) is the adopting
> system's architecture, and [`docs/repo-structure.md`](docs/repo-structure.md) is the adopting
> repository's tree. Until this file existed, the corpus described everyone's structure but its own,
> and the answer to "what is the source of this file and what is a copy of it?" lived in four places
> at once (#111).
>
> It is deliberately **not** in any adoption layer, for the same reason as
> [`.corpus-origin`](SETUP.md): it is about the corpus, and an adopter who copies it inherits a
> description of somebody else's repository.

## The one rule that explains the layout

A corpus that is copied has to answer, for every file, whether it is a **source** or a **copy of a
source** — because a copy edited in place is a fork nobody declared. Every directory here is one or
the other, and the copies are all generated and all checked.

### Sources

| Path | Holds | Authority |
| --- | --- | --- |
| [`memory/constitution.md`](memory/constitution.md) | nine articles; five protected | **root of authority** — where this and `CLAUDE.md` diverge, the article wins |
| [`CLAUDE.md`](CLAUDE.md) | the behavioural contract, condensing the articles | normative for agents, amended with the constitution |
| [`.claude/skills/sdd-*/SKILL.md`](.claude/skills) | the spec-kit-style commands | **the render source** — never edit a rendered copy |
| [`skills/`](skills) | domain skills (SRE, privacy, security, compliance) | loaded at most two per task (ADR-0060) |
| [`templates/`](templates) | the forms every SDD artefact starts as | indexed by [`templates/README.md`](templates/README.md), closed both ways |
| [`docs/adr/`](docs/adr) | binding decisions | an ADR binds until a newer one supersedes it |
| [`docs/process/gates/phase-gates.yaml`](docs/process/gates/phase-gates.yaml) | gate **data** | arbiter for the data (ADR-0095 §2) |
| [`docs/process/WORKFLOW.md`](docs/process/WORKFLOW.md) | gate **narrative** | arbiter for the intent (ADR-0095 §2) |
| [`specs/`](specs) | the specs the corpus governs itself by | `docs/governance/spec-registry.md` regenerates from them |

### Copies, and what generates them

Nothing in this column is edited by hand. Each is regenerated from the source beside it, and
`check-corpus.sh` fails if a copy and its source disagree.

| Copy | Generated from | By |
| --- | --- | --- |
| `.github/skills/<name>/SKILL.md` | `.claude/skills/sdd-*/SKILL.md` | `scripts/python/render_commands.py` |
| `.cursor/skills/<name>/SKILL.md` | the same | the same |
| `.agents/skills/<name>/SKILL.md` | the same | the same |
| `.gemini/commands/<name>.toml` | the same | the same |
| [`docs/governance/spec-registry.md`](docs/governance/spec-registry.md) | `specs/**` | `scripts/python/build_spec_registry.py` |
| `docs/sre/corpus-metrics-*.md` | the repository itself | `scripts/python/corpus_metrics.py` |

**Why four copies instead of one shared directory.** Each tool discovers the path it knows and no
other; a neutral directory would be a fifth copy, not a replacement for the four. The cost of the
duplication is paid by `render_commands.py --check`, which proves every copy is byte-identical to a
fresh render of its source.

## Adoption layers

`scripts/bash/adopt.sh` copies one of three layers into a product repository. A layer is closed
under reference — no file it copies may point at a file it omits — and a fresh adoption of every
layer is exercised on each full run (`scripts/python/check_adoption.py`).

| Layer | Carries | Deliberately excludes |
| --- | --- | --- |
| `minimal` | the commands, constitution, templates, hooks, scripts | governance — and therefore `check-corpus.sh`, which verifies governance |
| `governed` | minimal + the lifecycle, ADRs, control matrices, the verifier | the compliance evidence corpus |
| `full` | governed + privacy, compliance, SRE, audit, runbooks | nothing |

`.corpus-origin` marks this repository as the corpus and is never copied: the verifier reads it to
decide whether a check that audits the corpus governing itself applies where it is running.

## How the corpus verifies itself

`scripts/bash/check-corpus.sh` is the single entry point; `.github/workflows/corpus-check.yml` runs
it. Each check is named, and the name is the contract: `tests/scripts/test_check_corpus.py` injects
the defect a check exists to catch and requires **that** check to fail. A check nothing can make
fail is vacuous, and this corpus shipped five of those before the harness existed.

`scripts/python/mutation_coverage.py` ratchets how much of the verifier is proved able to fail.
Every check that contains logic must be proved; a line that only runs a test suite need not be,
because its suite is the guard.

<!-- generated: check_architecture_doc.py --update — do not edit by hand -->
| Measured | Value |
| --- | --- |
| Named checks in the verifier | 61 |
| Of those, proved able to fail | 48 |
| Checks containing logic, all proved | 43 |
| `sdd-*` commands rendered to four tools | 10 |
| Files in the `minimal` layer | 79 |
| Files in the `governed` layer | 364 |
| Files in the `full` layer | 601 |
<!-- /generated -->

## What this corpus is not

It ships no application code, no `Makefile`, no service registry and no CI for a product. Files
that name such paths carry the `adopter-paths` marker, and `scripts/python/adopter_paths.py`
fails the build for one that does not — the corpus states what it does not provide rather than
letting a reader assume it does.
