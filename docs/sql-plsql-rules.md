# SQL & PL/SQL Coding Standards

## File Naming Conventions

| File Type                              | Extension |
| -------------------------------------- | --------- |
| Package spec (and optionally body)     | `.pkg`    |
| Package body                           | `.pkb`    |
| Procedure                              | `.prc`    |
| Function                               | `.fnc`    |
| Object type spec (and optionally body) | `.typ`    |
| Object type body                       | `.tyb`    |
| Stored Java procedure                  | `.sjp`    |
| Stored Java function                   | `.sjf`    |
| Trigger                                | `.trg`    |
| Other PL/SQL                           | `.pls`    |
| Other SQL                              | `.sql`    |

**Rules:**

- Maintain code in text files — not via TOAD/SQL Developer direct edit. Enables version control.
- Package spec and body in **separate files** — minimises invalidation when body changes.

## Identifier Naming Conventions

Identifiers follow the pattern: `<Scope><Type><PrimaryIdentifier><Modifier><Suffix>`

Only **Scope** and **PrimaryIdentifier** are mandatory.
Use the **minimum** that is still unambiguous. Do not burden names with redundant metadata obtainable from context.

### Scope Prefixes

| Prefix | Meaning                            |
| ------ | ---------------------------------- |
| `g_`   | Global (package-level) variable    |
| `l_`   | Local variable (within subprogram) |
| `p_`   | Parameter                          |

### Type Prefixes

| Prefix | Type                   | Example          |
| ------ | ---------------------- | ---------------- |
| `k_`   | Constant               | `k_mailhost`     |
| `g_`   | Package-level variable | `g_loop_count`   |
| `l_`   | Local variable         | `l_loop_count`   |
| `c_`   | Cursor                 | `c_employees`    |
| `cp_`  | Cursor parameter       | `cp_employee_id` |
| `r_`   | Record                 | `r_employee`     |

### Parameter Suffixes (OUT/INOUT only; IN is default and needs no suffix)

| Suffix   | Direction |
| -------- | --------- |
| _(none)_ | `IN`      |
| `_out`   | `OUT`     |
| `_inout` | `IN OUT`  |

### Private Subprogram Suffix

All functions and procedures declared **only in the package body** (i.e. not exposed in the spec) must have a trailing underscore (`_`) appended to the name:

```sql
-- Public (declared in spec and body)
function get_account_balance(p_account_id accounts.account_id%type) return number;

-- Private (body only)
function get_account_balance_(p_account_id accounts.account_id%type) return number;
procedure validate_credit_(p_account_id accounts.account_id%type);
```

**Rules:**

- The trailing `_` is the sole distinguishing marker — do not add any other prefix or suffix to signal privacy.
- Forward declarations (local module stubs at the top of the body) must also carry the `_` suffix, since they exist only to resolve forward references among private subprograms.
- Never apply the `_` suffix to public subprograms, package-level variables, constants, types, or exceptions — only to private functions and procedures.

### Naming Rules

- **Primary identifier is paramount.** All prefixes/suffixes are secondary.
- No random abbreviations. If `flgtdt` isn't obviously `flight_date`, don't use it.
- If a name feels too long, think harder — don't truncate vowels. `ODI_LOE_BY_AC_PD_L1` is not acceptable.
- Use plurals for cursors and collections (they represent sets); use singular for records.
- Never name a cursor `c1`. If you're numbering cursors, you haven't named them.

## Specific Identifier Patterns

### Cursors

```sql
-- Named after the table/view being processed, plural
c_customers
c_new_accounts

-- Ref cursor passed as parameter
pc_old_accounts  -- or p_old_accounts is acceptable
```

### Records

```sql
lr_account        -- formal local record
r_account         -- informal
pr_account        -- parameter record
gr_last_account   -- global record
r_new_account     -- with modifier
```

### Loop Index

```sql
for i in 1..12 loop          -- acceptable for simple loops
for i_month in 1..12 loop    -- more descriptive
for r in c_discrepancies loop
for r_emp in c_emp loop
```

Never use `r1` — use a descriptive name.

### Collection Type

Use `_tt` suffix for collection ("table") types:

```sql
type account_tt is table of accounts%rowtype;
l_accounts account_tt;
l_new_accounts account_tt;
l_old_accounts account_tt;
```

Distinguish collection subtypes only when necessary:

- `_aatt` — associative array
- `_vatt` — varray
- `_ntt` — nested table
- `_tt` — generic (use this unless distinction matters)

### PL/SQL Record Type

```sql
type g_address_rectype is record (...);  -- formal
type address_rectype is record (...);    -- informal
type address is record (...);            -- acceptable when unambiguous
```

### Schema-Level Object Type

Use `_OT` suffix:

```sql
create or replace type customer_OT as object (...);
```

### Schema-Level Collection Type

Define generic reusable types:

```sql
create or replace type number_tt    as table of number(38,10);
create or replace type integer_tt   as table of integer;
create or replace type date_tt      as table of date;
create or replace type varchar2_tt  as table of varchar2(4000);
create or replace type timestamp_tt as table of timestamp;
```

## Package Structure

A package consists of two files: the spec (`.pkg`) and the body (`.pkb`). Structure both files in the fixed section order below. Never reorder sections.

### Package Spec

```sql
create or replace
package my_package is

------------
--  OVERVIEW
--
--  One paragraph describing what this package does and why it exists.
--

-----------
--  EXAMPLE
--
--  Minimal runnable usage example.
--

-------------
--  RESOURCES
--
--  Links to design docs, tickets, related packages.
--

----------------------------------------------------------
--	GLOBAL PUBLIC EXCEPTIONS
----------------------------------------------------------

----------------------------------------------------------
--	GLOBAL PUBLIC TYPES
----------------------------------------------------------

----------------------------------------------------------
--	GLOBAL PUBLIC CONSTANTS
----------------------------------------------------------

----------------------------------------------------------
--	GLOBAL PUBLIC MODULES
----------------------------------------------------------

/**
*	One-line description.
*	@param p_parameter  description
*	@return             description
*/
function my_public(p_parameter in varchar2) return varchar2;

end my_package;
/
```

**Rules:**

- Every package spec must open with OVERVIEW, EXAMPLE, and RESOURCES comment blocks.
- Public subprograms must be documented with JSDoc-style block comments (`/** ... */`) immediately above the signature — one `@param` line per parameter, one `@return` line.
- Sections appear in the order shown; omit a section's content if empty but keep the header.

### Package Body

```sql
create or replace
package body my_package is

----------------------------------------------------------
--	PRIVATE EXCEPTIONS
----------------------------------------------------------

----------------------------------------------------------
--	PRIVATE TYPES
----------------------------------------------------------

----------------------------------------------------------
--	PRIVATE CONSTANTS
----------------------------------------------------------

----------------------------------------------------------
--	PRIVATE VARIABLES
----------------------------------------------------------

----------------------------------------------------------
--	LOCAL MODULES
----------------------------------------------------------

-- Forward declarations: only needed when a private subprogram
-- is called before its full definition appears in this file.
function my_private_(p_parameter in varchar2) return varchar2;

----------------------------------------------------------
--	GLOBAL MODULES
----------------------------------------------------------

/*
*	Implementation of public subprograms first,
*	then full definitions of private subprograms.
*/
function my_public(p_parameter in varchar2) return varchar2
is
begin
	return my_private_(p_parameter => p_parameter);
end my_public;


function my_private_(p_parameter in varchar2) return varchar2
is
begin
	return p_parameter;
end my_private_;

end my_package;
/
```

**Rules:**

- Section order is fixed: private exceptions → private types → private constants → private variables → local modules → global modules.
- LOCAL MODULES contains only forward declarations (stubs). Full implementations go in GLOBAL MODULES.
- Add a forward declaration only when required to resolve a forward reference — do not declare all private subprograms upfront as a matter of habit.
- Within GLOBAL MODULES, place public subprogram implementations first, private implementations after. This makes the public interface immediately visible when reading the body.
- Use `/*  */` block comments (not JSDoc) for implementation notes inside the body; JSDoc belongs only on the spec signatures.
- The `end <subprogram_name>;` label is mandatory on every subprogram — match the name exactly, including the trailing `_` for private subprograms.

### Standalone Procedure/Function Structure

For standalone `.prc` / `.fnc` files the same section discipline applies, collapsed into a single unit:

```sql
create or replace
procedure my_procedure
    ( p_account_id  accounts.account_id%type
    , p_result_out  varchar2 )
is
	-- constants
	k_max_retries constant pls_integer := 3;

	-- types

	-- variables
	l_attempt pls_integer := 0;

	-- cursors

	-- local (private) subprograms
	procedure validate_(p_id in accounts.account_id%type) is
	begin
		...
	end validate_;

begin
	...
end my_procedure;
/
```

**Rules:**

- Declaration block order: constants → types → variables → cursors → local subprograms.
- Local subprograms within a standalone unit also follow the trailing `_` private naming convention.
- No section-header comments are required in standalone units — the declaration block is small enough to read without them. Add them only if the declaration block exceeds ~30 lines.

## Code Formatting

### Core Principle

> Format to show **logical structure**. Not for aesthetics. Structure should be visible — if it looks bad, that's information.

### Indentation

- Use **tabs**, not spaces.
- Left-align blocks to create a clear vertical line at each level.

### Case Convention

Options (pick one and be consistent):

1. Uppercase keywords, lowercase everything else _(traditional)_
2. **Lowercase everything**

### Procedure/Function Declarations

First parameter on new line; one parameter per line; closing paren on last parameter line:

```sql
function invoice_address
    ( p_account_id  accounts.account_id%type
    , p_date        date )
    return address;

procedure do_stuff_rather_long_name
    ( p_first_parameter   boolean default false
    , p_second_parameter  service_agreement.agreement_status%type default 2
    , p_third_parameter   currency_amount default 0 );
```

### Variable Assignments

One statement per line. Space around operators:

```sql
-- Bad
l_firstname := 'Dimitri'; l_lastname := 'Papadopoulos';
l_firstname:='Dimitri';

-- Good
l_firstname := 'Dimitri';
l_lastname  := 'Papadopoulos';

-- Preferred: assign at declaration
l_firstname employees.firstname%type := 'Dimitri';
```

### Multi-Line Statements

Indent continuation lines. Each parameter on its own line when formal layout is required:

```sql
upload_sales
( p_company_id
, p_last_year_date
, p_rollup_type
, p_total );
```

## Commenting Style

### Rules

- **Comment as you code** — not after.
- **Explain why, not how.** Don't document what the code plainly says.
- Use `--` line comments, not `/* ... */` blocks — easier to comment out sections when debugging.
- Indent comments at the same level as the code they describe.
- No decorative ASCII art. It creates maintenance burden.

```sql
-- Bad
/*********************************************************/
/* Delete all the customers and fire the employees.      */
/*********************************************************/

-- Good
-- Delete all customers and fire all employees:
```

## PL/SQL Programming Guidelines

### Conditional Statements

Brackets are optional — PL/SQL has `then` to terminate conditions:

```sql
-- Bad
if ((x = 1) and (y = 2)) then

-- Good
if (x = 1) then
if x = 1 then
if x = 1 and y = 2 then
if (x = 1 and y = 2) then
```

Boolean operators (`and`/`or`) go at the **start** of the line, not end:

```sql
-- Bad
if to_char(sysdate,'D') > 1 and
   mypackage.myprocedure(1,2,3,4) not between 1 and 99 then

-- Good
if to_char(sysdate,'D') > 1
and mypackage.myprocedure(1,2,3,4) not between 1 and 99
then
```

Mixed OR/AND — align bracketed conditions vertically:

```sql
if a = 1
and (   b = 2
     or c = 3
     or d = 4 )
then
```

### Loops

- `FOR`/`WHILE` loops should not use explicit `EXIT` — use them when you know the iteration count.
- **Cursor FOR loop** is preferred over `OPEN-FETCH-EXIT-CLOSE` in nearly all cases.
- Anonymous cursor FOR loops are acceptable:

```sql
for r in (
    select e.employee_id, e.first_name
    from   employees e
    order by 1
)
loop
    ...
end loop;
```

Use `OPEN-FETCH-EXIT-CLOSE` only when:

- Working with a weak ref cursor (runtime-typed).
- You need to retain the record after loop completion (rare).

### Booleans

Use boolean expressions directly — do not use IF to assign TRUE/FALSE:

```sql
-- Bad
if hiredate < sysdate then
    date_in_past := true;
else
    date_in_past := false;
end if;

-- Good
date_in_past := hiredate < sysdate;

-- Bad (function return)
if total_sal > 10000 then
    return true;
else
    return false;
end if;

-- Good
return total_sal > 10000;
```

Use boolean variables to name complex conditions:

```sql
eligible_for_raise :=
    total_sal between 10000 and 50000
    and emp_status(emp_rec.empno) = 'N'
    and months_between(emp_rec.hiredate, sysdate) > 10;

if eligible_for_raise then
    give_raise(emp_rec.empno);
end if;
```

### Prefer SQL Over PL/SQL

SQL is almost always faster. Replace PL/SQL loops with single SQL statements when possible:

```sql
-- Bad: 20 INSERT statements
for i_year in 1..20 loop
    insert into table1
    select * from table2
    where  starting_year = i_year;
end loop;

-- Good: 1 INSERT statement
insert into table1
select * from table2
where  starting_year between 1 and 20;
```

### Constants

- No magic numbers or literals in code. Declare named constants (`k_` prefix).
- Each constant defined in exactly one place.
- If a variable never changes, convert it to a constant.

```sql
k_ship_express  constant varchar2(10) := 'EXPRESS';
k_ship_standard constant varchar2(10) := 'STANDARD';
```

### Variable Discipline

- One variable, one purpose. Never reuse a variable for two different things.
- Remove unused variables. Use PL/SQL compile-time warnings and PL/Scope to detect them.

### Use `%TYPE`

Always anchor variable types to column definitions:

```sql
-- Bad
procedure format_customer ( p_customer_id integer )
is
    l_first_name  varchar2(30);
    l_last_name   varchar2(30);

-- Good
procedure format_customer ( p_customer_id customers.cst_id%type )
is
    l_first_name  customers.cst_first_name%type;
    l_last_name   customers.cst_last_name%type;
```

Benefits: stays in sync with schema changes; self-documents the relationship to DB columns.

### Use `%ROWTYPE` for Records

```sql
r_employee employees%rowtype;
```

### Subtypes

Create subtypes to document business intent, not technical detail:

```sql
-- Bad subtype (just adds noise)
subtype emp240_rtyp is c_emp240%rowtype;

-- Good subtype (documents business concept)
subtype money is stock_items.unit_price%type;
subtype room_number is rooms.room_number%type;
```

Consider a dedicated package containing only standard subtypes, constants, and variable declarations.

## Exception Handling

### Prefer `RAISE_APPLICATION_ERROR` Over Named Exceptions

Named exceptions carry no explanatory message:

```sql
-- Bad: no diagnostic info
raise errorpkg.fatal_error;

-- Good: stack trace + context
raise_application_error
( errorpkg.k_fatal_error
, 'Credit check failed for account ' || r_acc.acc_id
, true );
```

### Error Code Strategy

For most applications, one error code per package (or even one for the whole application) is sufficient:

```sql
k_error_code constant pls_integer := -20042;
```

Then use `k_error_code` in all `raise_application_error` calls within that package.

### Log and Raise Pattern

```sql
-- Log and raise in one call via utility procedure:
l_error_text := 'Invalid account ' || r_acc.acc_id;
error_pkg.log_and_raise(errorpkg.k_invalid_account, l_error_text);
```

Only log at the topmost error-handling level; propagate via `raise_application_error` with `true` (preserve stack).

### Keep It Simple

Avoid a proliferation of application-specific named exceptions that callers have to test for. The calling procedure usually doesn't care _why_ the callee failed — it just failed. Put cleanup logic inside the procedure that fails, not in every caller.

## SQL Layout Guidelines

### Left-Align Everything

Use the same left-alignment rules as PL/SQL. The "right-gutter" alignment style is rejected:

```sql
-- Bad (right-gutter)
select last_name, first_name
  from employees
 where department_id = 15
   and hire_date < sysdate;

-- Good (left-aligned)
select last_name, first_name
from   employees
where  department_id = 15
and    hire_date < sysdate;
```

### One Expression Per Line

```sql
select e.last_name
     , c.name
     , max(sh.salary) best_salary_ever
from   employees e
       join companies c
            on  c.company_id = e.company_id
       join salary_history sh
            on  sh.employee_id = e.employee_id
where  e.hire_date > add_months(sysdate, -60)
and    exists
       ( select 1
         from   some_other_table ot
         where  ot.employee_id = e.employee_id )
group by e.last_name, c.name
order by e.last_name, c.name;
```

### INSERT Column List

```sql
insert into employees
( emp_id
, emp_firstname
, emp_lastname )
values
( emp_seq.nextval
, r_emp.firstname
, r_emp.lastname );
```

### UPDATE

```sql
update employees
set    salary = salary * l_raise_factor
where  department_id = l_department_id
and    termination_date is null;
```

### Blank Lines

- Max **one** blank line within a subprogram body.
- **Two** blank lines between subprograms in a package or type body.

### Table Aliases

Use **meaningful abbreviations** based on the table name — not `a`, `b`, `c`:

```sql
-- Bad
from employees a join companies b on b.com_id = a.emp_com_id

-- Good
from employees emp join companies com on com.com_id = emp.emp_com_id
```

Consistent alias length (e.g. 3 chars) is fine; clarity is the goal.

### ANSI Join Syntax

Use explicit `JOIN ... ON` syntax. Implicit comma joins are not acceptable:

```sql
-- Bad (implicit join)
from employees e, departments d
where d.department_id = e.department_id

-- Good (ANSI)
from employees e
     join departments d
          on  d.department_id = e.department_id
```

Two spaces after `on` so that `and` conditions align with the `on` column:

```sql
join departments d
     on  d.department_id = e.department_id
     and d.active_flag = 'Y'
```

Join conditions should flow in the same left-to-right order as the FROM clause.

## Summary: The Two Non-Negotiables

If nothing else, enforce these:

1. **Give everything meaningful names.**
2. **If anything is not obvious, change it so it is — and if you can't, explain it with a comment.**
