<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# Batch run wrapper — template (ADR-0101)

Under the `batch-data` profile, every run of a pipeline is wrapped so that its record is appended
to the run history **whatever the outcome**. The wrapper is `scripts/python/run_record.py`, stdlib
only. The record's shape is `docs/sre/slo/schema/run-record.schema.json`.

## What the wrapper guarantees

1. **An ID and a commit before the first step.** The run ID is `<pipeline>-<UTC start,
YYYYMMDDTHHMMSSZ>`. `git rev-parse HEAD` and whether the tree was clean are recorded before
   anything runs. Outside a git repository there is no commit to record, so the run does not start.
2. **A production run from a dirty tree is refused.** The refusal is recorded as an `aborted` run
   with no steps. A non-production run from a dirty tree runs and is marked `dirty: true`.
3. **One line per run, appended even on failure.** The status is `succeeded`, `failed` or `aborted`,
   and each step that started has its status, duration and row counts.
4. **Counts and identifiers only.** The record has no field for a data value, and
   `run_record.py check` rejects one.

## Where the history lives

**Outside the working tree, or in a gitignored path.** A history committed or left untracked in the
tree makes the tree dirty, and the next production run is refused. Keep it append-only: the
evidence ledger of ADR-0102 copies it write-once at the end of the run.

## Python pipeline

```python
from run_record import Run  # scripts/python/run_record.py

with Run("o2c", history="/var/lib/o2c/history.jsonl", production=True) as run:
    print(run.run_id)  # put it in every log line and output file name of this run
    with run.step("extract") as step:
        rows, rejected = extract(period="2026-10")
        step.count(rows_in=len(rows) + len(rejected), rows_out=len(rows), rows_rejected=len(rejected))
    with run.step("load") as step:
        step.count(rows_in=len(rows), rows_out=load(rows))
```

An exception in a step marks the step and the run `failed`. An interrupt marks them `aborted`. In
both cases the record is appended and the exception propagates.

## Shell pipeline

```sh
python3 scripts/python/run_record.py exec \
    --pipeline o2c --history /var/lib/o2c/history.jsonl --production \
    --step extract="./steps/extract.sh --period 2026-10" \
    --step load=./steps/load.sh
```

The steps run in order, without a shell, and the run stops at the first one that exits non-zero.
Each step sees `RUN_ID` and `RUN_STEP_COUNTS` in its environment. It reports its counts by
writing to that file:

```sh
echo "rows_in=$read"          >  "$RUN_STEP_COUNTS"
echo "rows_out=$written"      >> "$RUN_STEP_COUNTS"
echo "rows_rejected=$dropped" >> "$RUN_STEP_COUNTS"
```

Exit codes: `0` succeeded, `1` failed, `2` refused, `130` interrupted.

## In CI and at Phase 11

```sh
python3 scripts/python/run_record.py check /var/lib/o2c/history.jsonl
```

It fails on a malformed line, a run ID that does not match its start time, a duplicate run ID (a
rerun must be a new run), a production run from a dirty tree that ran, or a `succeeded` run with a
step that did not succeed. Phase 11 reads it under `batch-data` (`phase-gates.yaml` ›
`profile_readings`). The run SLOs the history feeds are declared under `pipelines:` in
`docs/sre/slo/slo.yaml`.
