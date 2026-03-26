---
name: oracle-local
description: "Use this skill whenever a task requires querying, testing, or validating against the local Oracle database. Triggers: any mention of SQL, PL/SQL, Oracle, sqlplus, schema inspection, unit test data, or database-backed logic. Also triggers when a previous sqlplus invocation produced ORA- or SP2- errors. Do NOT skip this skill and improvise sqlplus invocations — the correct invocation pattern is non-obvious and errors are silent by default."
compatibility: "opencode, Claude Code — any agentic surface with shell access on the local dev machine"
---

# Local Oracle Database

## Credentials — env vars only

Credentials are **exclusively** sourced from environment variables. Never
hardcode, echo, or interpolate them into strings that appear in shell history,
log files, or source control. Never guess or substitute defaults.

| Variable          | Contains              |
|-------------------|-----------------------|
| `ORACLE_SERVER`   | `host:port/service`   |
| `ORACLE_USER`     | Database username      |
| `ORACLE_PASSWORD` | Database password      |

### Mandatory pre-flight: verify all three are set

Run this before every sqlplus invocation. **Abort and report to the user if
any variable is unset or empty.**

```bash
: "${ORACLE_SERVER:?ORACLE_SERVER is not set}"
: "${ORACLE_USER:?ORACLE_USER is not set}"
: "${ORACLE_PASSWORD:?ORACLE_PASSWORD is not set}"
```

The `${var:?msg}` form exits the shell with a non-zero code and prints the
message if the variable is unset or empty. Use it verbatim.

If any check fails, stop immediately and tell the user which variable is
missing. Do not proceed.

---

## Execution patterns

### Rule: always use a here-doc, never inline SQL

Inline SQL in `-c` flags or bare `echo | sqlplus` pipelines produces broken
output and swallows errors. Use the patterns below verbatim.

The connection string is always `"${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}"`.
This form never exposes credentials in shell history when used inside a here-doc.

### Pattern A — single query, stdout only

```bash
sqlplus -s "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}" << 'SQL'
SET PAGESIZE 50000
SET LINESIZE 32767
SET FEEDBACK OFF
SET HEADING ON
SET SERVEROUTPUT ON SIZE UNLIMITED
SET TRIMSPOOL ON

-- your SQL here
SELECT SYSDATE FROM DUAL;

EXIT SQL.SQLCODE;
SQL
```

`EXIT SQL.SQLCODE` propagates ORA- errors to the shell exit code. Always include it.

### Pattern B — PL/SQL block with output

```bash
sqlplus -s "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}" << 'SQL'
SET SERVEROUTPUT ON SIZE UNLIMITED
SET FEEDBACK OFF

DECLARE
    l_result VARCHAR2(4000);
BEGIN
    -- your PL/SQL here
    l_result := 'ok';
    DBMS_OUTPUT.PUT_LINE(l_result);
END;
/

EXIT SQL.SQLCODE;
SQL
```

### Pattern C — run a .sql file

```bash
sqlplus -s "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}" \
  @/absolute/path/to/file.sql
echo "Exit code: $?"
```

### Pattern D — capture exit code and fail loudly

```bash
output=$(sqlplus -s "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}" << 'SQL'
SET SERVEROUTPUT ON SIZE UNLIMITED
SET FEEDBACK OFF
SELECT 1 FROM DUAL;
EXIT SQL.SQLCODE;
SQL
)
rc=$?
echo "$output"
if [[ $rc -ne 0 ]]; then
  echo "ORACLE ERROR: exit code $rc" >&2
  exit $rc
fi
```

---

## SET directives reference

Always include these at the top of every sqlplus session:

| Directive                            | Purpose                                           |
|--------------------------------------|---------------------------------------------------|
| `SET PAGESIZE 50000`                 | Prevent page breaks cutting output                |
| `SET LINESIZE 32767`                 | Prevent line wrapping corrupting columnar output  |
| `SET FEEDBACK OFF`                   | Suppress "N rows selected" noise                  |
| `SET SERVEROUTPUT ON SIZE UNLIMITED` | Required for DBMS_OUTPUT in PL/SQL blocks         |
| `SET TRIMSPOOL ON`                   | Remove trailing spaces from spool output          |
| `EXIT SQL.SQLCODE`                   | Propagate ORA- errors as non-zero shell exit codes|

Missing `EXIT SQL.SQLCODE` is the single most common source of silent failures.

---

## When the database is unreachable

On any connection failure (ORA-12541, ORA-01034, ORA-27101, or sqlplus exits
non-zero without output):

1. **Tell the user exactly what failed** — include the ORA- code or exit code.
2. **Ask the user to start the database** if it is not running, and wait for
   confirmation before retrying. Example prompt:

   > "Connection to `${ORACLE_SERVER}` failed (ORA-12541: no listener).
   > Please start the Oracle listener and database instance, then let me know
   > when it is ready and I will retry."

3. **Once the user confirms**, retry the original operation — do not re-run
   diagnostics or ask again unless the retry also fails.
4. **On a second consecutive failure**, stop and report. Do not loop.

For wrong credentials (`ORA-01017` / `ORA-01005`):

1. Report the exact ORA- code.
2. Ask the user to correct `ORACLE_USER` or `ORACLE_PASSWORD`.
3. Do not retry more than once with the same values.

---

## Error code quick reference

| Code      | Meaning                                        | Action                                          |
|-----------|------------------------------------------------|-------------------------------------------------|
| ORA-01017 | Invalid username/password                      | Ask user to fix `ORACLE_USER`/`ORACLE_PASSWORD` |
| ORA-01005 | Null password given; logon denied              | `ORACLE_PASSWORD` is unset or empty             |
| ORA-12541 | TNS: no listener                               | Listener is down — follow §Unreachable          |
| ORA-12162 | TNS: net service name incorrectly specified    | `ORACLE_SERVER` format wrong                    |
| ORA-12154 | TNS: could not resolve the connect identifier  | `ORACLE_HOME` / tnsnames.ora misconfigured      |
| ORA-01034 | ORACLE not available                           | Instance is down — follow §Unreachable          |
| ORA-27101 | Shared memory realm does not exist             | Instance is down — follow §Unreachable          |
| SP2-0640  | Not connected                                  | Always use explicit DSN, never `/nolog` alone   |
| ORA-00942 | Table or view does not exist                   | Wrong schema or missing synonym                 |
| ORA-04063 | Object has errors (invalid PL/SQL)             | Recompile: `ALTER PROCEDURE x COMPILE;`         |
| ORA-06512 | At line N (PL/SQL stack line)                  | Scroll up for root ORA- code                    |

`SP2-*` errors come from sqlplus itself, not Oracle. They almost always mean
the session was not connected when the SQL ran. Never ignore `SP2-0640`.

---

## Safety rules — mandatory

1. **Never hardcode credentials.** Only `${ORACLE_USER}`, `${ORACLE_PASSWORD}`,
   and `${ORACLE_SERVER}` are permitted. Any literal credential in generated
   code is a blocker — stop and rewrite.
2. **Never run DDL (CREATE, DROP, ALTER, TRUNCATE) without showing the
   statement to the user and receiving explicit approval first.**
3. **Never run DELETE or UPDATE without a WHERE clause.** If the task
   genuinely requires a full-table delete, show row count first:
   ```sql
   SELECT COUNT(*) FROM schema.table;
   ```
   Then ask for confirmation.
4. **Never run COMMIT inside a script unless the task explicitly requires
   persisting data.** Use `ROLLBACK` at the end of exploratory scripts.
5. **Never use `CONNECT / AS SYSDBA` for application queries.** SYS access
   is only for instance startup/shutdown and emergency DBA operations.
6. **Always capture and display the sqlplus exit code.** A zero exit with
   ORA- text in stdout still indicates a logic error — parse stdout for
   `ORA-` and `SP2-` prefixes even when `$?` is 0.
7. **Validate output is non-empty before declaring success.** An empty
   result set from a probe query (e.g. `SELECT 1 FROM DUAL`) is a red flag.

---

## Schema inspection patterns

```bash
sqlplus -s "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}" << 'SQL'
SET PAGESIZE 50000
SET LINESIZE 200
SET FEEDBACK OFF
SELECT table_name, num_rows, last_analyzed
  FROM user_tables
 ORDER BY table_name;
EXIT SQL.SQLCODE;
SQL

sqlplus -s "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}" << 'SQL'
SET FEEDBACK OFF
DESCRIBE my_table
EXIT SQL.SQLCODE;
SQL

sqlplus -s "${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_SERVER}" << 'SQL'
SET PAGESIZE 1000
SET FEEDBACK OFF
SELECT object_type, object_name, status
  FROM user_objects
 WHERE status <> 'VALID'
 ORDER BY object_type, object_name;
EXIT SQL.SQLCODE;
SQL
```

---

## JSON date/timestamp — known issue

`JSON_OBJECT_T.get_date()` and `.get_timestamp()` require the string to match
`NLS_DATE_FORMAT` / `NLS_TIMESTAMP_FORMAT` of the session — ISO-8601 with a `Z`
suffix often fails with `ORA-40573` or silently returns NULL.

**Safe pattern:**

```sql
DECLARE
    l_obj  JSON_OBJECT_T;
    l_raw  VARCHAR2(100);
    l_ts   TIMESTAMP WITH TIME ZONE;
BEGIN
    l_obj := JSON_OBJECT_T('{"mydate": "2025-03-26T14:30:15.123Z"}');
    l_raw := l_obj.get_string('mydate');
    -- Parse ISO-8601 Z suffix explicitly; do not rely on session NLS
    l_ts  := TO_TIMESTAMP_TZ(l_raw, 'YYYY-MM-DD"T"HH24:MI:SS.FF3TZR');
    DBMS_OUTPUT.PUT_LINE(TO_CHAR(l_ts, 'YYYY-MM-DD HH24:MI:SS.FF3 TZH:TZM'));
END;
/
```

Do not use `get_date()` / `get_timestamp()` on ISO-8601 strings without
verifying session NLS settings first:

```sql
SELECT VALUE FROM NLS_SESSION_PARAMETERS
 WHERE PARAMETER IN ('NLS_DATE_FORMAT','NLS_TIMESTAMP_FORMAT');
```
