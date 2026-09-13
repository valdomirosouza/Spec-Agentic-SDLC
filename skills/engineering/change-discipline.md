<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Skill — Change Discipline

**Owner:** Tech Lead | **Reviewer:** Tech Lead | **Status:** Active | **Last updated:** 2026-09-13
**Source:** [Karpathy guidelines](https://x.com/karpathy/status/2015883857489522876) (MIT) ·
**Load when:** writing, reviewing or refactoring code — especially when editing code you did not write.

> **What this adds, and what it does not.** Two of the four principles below are already binding
> elsewhere and are kept here as pointers, not as second copies: **Simplicity First** is
> Constitution Article VIII, and **Goal-Driven Execution** is Article II plus the FR→AC→test
> traceability the spec template enforces. Restating them would create two places to drift.
> **Surgical Changes** had no equivalent anywhere in the corpus, and is the reason this skill
> exists. **Think Before Coding** extends Article IX from grounding a claim to surfacing the
> alternatives you did not pick.
>
> **Tradeoff, stated by the source:** these bias toward caution over speed. For a trivial task,
> use judgement.

---

## 1. Think Before Coding — extends Constitution IX

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Article IX already forbids inventing an API, a path or a behaviour. This adds the step before it:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — do not pick silently. Picking silently is how
  a design decision becomes invisible to review.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what is confusing, and ask.

In this corpus the escalation block of `CLAUDE.md` §14 is where an unresolvable ambiguity goes.
Everything short of that threshold still gets named in the PR, not resolved in silence.

## 2. Simplicity First — this is Constitution VIII

`memory/constitution.md` Article VIII already binds: implement what the spec says and nothing more;
extra abstraction or projects need a justification in the plan's Complexity Tracking table. The
source adds two tests worth keeping in mind:

- No error handling for impossible scenarios.
- If you wrote 200 lines and it could be 50, rewrite it.

Ask: would a senior engineer call this overcomplicated? If yes, simplify.

## 3. Surgical Changes — the rule the corpus did not have

**Touch only what you must. Clean up only your own mess.**

When editing existing code or documents:

- Do not improve adjacent code, comments or formatting.
- Do not refactor what is not broken.
- Match the existing style, even where you would do it differently.
- If you notice unrelated dead code, mention it — do not delete it.

When your change creates orphans:

- Remove the imports, variables and functions **your** change made unused.
- Do not remove pre-existing dead code unless asked.

**The test: every changed line traces directly to the request.**

### Why this one earned its place here

The maturity audit of 2026-09-13 found three failures of exactly this discipline in work done the
same week, each of which passed review:

- A check written to forbid a productivity ratio matched an unrelated ADR about how fast a package
  manager is, because the pattern was broadened beyond the request.
- A change that claimed to consolidate the coverage floor into one place edited some of the
  occurrences and left two, so the corpus still stated three numbers.
- Adjacent edits rode along with fixes, which is why several commits touch files their issue never
  mentioned.

None was caught by a test, because scope is not a property a test can assert. It is a property of
review, which is why it is a checklist item in `CLAUDE.md` §7 rather than a gate.

## 4. Goal-Driven Execution — this is Constitution II

Article II already requires tests that fail before the implementation exists and reference the
requirement they prove. The source adds the framing:

- "Add validation" → "write tests for invalid inputs, then make them pass".
- "Fix the bug" → "write a test that reproduces it, then make it pass".
- "Refactor X" → "ensure tests pass before and after".

For a multi-step task, state the plan with its verification before starting:

```text
1. [step] → verify: [check]
2. [step] → verify: [check]
```

Strong success criteria let an agent loop independently. Weak criteria ("make it work") force
constant clarification, which is the cost this corpus pays in human gate time.

---

## Related

- [`../../memory/constitution.md`](../../memory/constitution.md) — Articles II, VIII and IX
- [`testing-strategy.md`](testing-strategy.md) — how the tests in §4 are written here
- [`../sdlc/spec-lifecycle.md`](../sdlc/spec-lifecycle.md) — where a scope change becomes a spec change
