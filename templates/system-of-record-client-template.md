<!-- adopter-paths: names paths or commands provided by the adopting product repository — see docs/reference/adopter-provided-paths.md -->

# System-of-record client — contract and test template (ADR-0100)

Code in the adopting repository reaches each system of record declared in
`docs/governance/systems-of-record.yaml` through **one client**, and that client is read-only
by default. This is the main control. The high-risk-action guard sees only the command strings
an agent types. It cannot see a write made inside a script, an SDK call or a program the agent
runs, so it is defence in depth and nothing more.

## Contract

1. **One entry point per system.** All production and script code reaches the system through
   `<system>_client(...)`, for example `src/clients/erp.py`. No other module opens a connection
   to it, and a reviewer can grep for that.
2. **Read-only by default.** The default constructor returns a client that can only read. Where
   the system supports it, use a read-only account, role or token. Where it does not, the client
   refuses the operation itself: no `INSERT` / `UPDATE` / `DELETE` / `MERGE` / DDL, and no
   non-GET HTTP verb.
3. **Writes are explicit and in one reviewed place.** A write needs a separate constructor, for
   example `<system>_write_client(reason=...)`. It is called only from the module that owns the
   write path, and that module is listed in `.github/CODEOWNERS` with the system's owner as
   reviewer. Each write records the caller and the reason through the audit logger.
4. **No credentials in code or in the declaration.** Connection secrets come from the secret
   store or the environment (CLAUDE.md §3.2). The declaration names systems and patterns only.
5. **Development sessions get the read-only client.** A dev or agent environment is never given
   write credentials for a system of record. If a task needs a write, a person runs it, and the
   guard's `ask` is where that decision happens.

## Test template

Copy this into the adopting repository's test suite and adapt the names. It runs in CI and keeps
the contract true as the code changes. The template is in Python; the four assertions carry over
to any language.

```python
"""Contract tests for the <system> client (ADR-0100). Adapt names; keep all four assertions."""
import pathlib
import re

import pytest

from src.clients.erp import erp_client, ReadOnlyViolation  # adopter-provided

WRITES = [
    "INSERT INTO orders VALUES (1)",
    "UPDATE orders SET status = 'x'",
    "DELETE FROM orders",
    "SELECT 1; DELETE FROM orders",  # a read followed by a write is a write
    "WITH d AS (DELETE FROM orders RETURNING *) SELECT * FROM d",
    "DROP TABLE orders",
]


@pytest.mark.parametrize("sql", WRITES)
def test_the_default_client_refuses_a_write(sql):
    with pytest.raises(ReadOnlyViolation):
        erp_client().execute(sql)


def test_the_default_client_reads():
    erp_client().execute("SELECT 1")  # against the test double or a read replica


def test_only_the_owning_module_builds_a_write_client():
    """One reviewed place: a second caller of the write constructor fails CI."""
    allowed = {pathlib.Path("src/clients/erp_writes.py")}
    callers = {
        p for p in pathlib.Path("src").rglob("*.py")
        if re.search(r"\berp_write_client\(", p.read_text(encoding="utf-8"))
        and p != pathlib.Path("src/clients/erp.py")
    }
    assert callers <= allowed, f"write client built outside its owner: {sorted(callers - allowed)}"


def test_no_module_bypasses_the_client():
    """Nothing but the client opens a connection to the system."""
    pattern = re.compile(r"erp\.example\.internal|ERP_DATABASE_URL")
    offenders = [
        p for p in pathlib.Path("src").rglob("*.py")
        if pattern.search(p.read_text(encoding="utf-8")) and p.parent != pathlib.Path("src/clients")
    ]
    assert not offenders, f"direct connection outside the client: {offenders}"
```

A database-side read-only role is stronger than a client-side check, so use it where the system
offers one. The client-side refusal is what remains when it does not, or when the account is
shared.
