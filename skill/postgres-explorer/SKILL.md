---
name: postgres-explorer
description: Explore the connected PostgreSQL database through the Postgres Explorer MCP. Use to discover available data, inspect tables and join keys, or answer questions with read-only SQL.
---

# Explore PostgreSQL with MCP

Use the connected **Postgres Explorer** server. When asked what data is available, start with `list_schemas`, then call `list_tables` for the relevant schemas. Inspect representative tables with `describe_table` before suggesting questions the data could answer. Use `query` when the user needs values from the database. If the server is unavailable, explain that the query could not be run and label any SQL you provide as unexecuted.

## `list_schemas`

Call with `{}` when the schema is unknown or the user asks for an overview. The result gives the names of schemas with readable tables or views.

## `list_tables`

Pass the exact `schema` name to list its readable tables and views. Each result gives `name` and `kind`. If the question spans several schemas, call once per relevant schema and keep each result associated with the schema from its call.

## `describe_table`

Use this before writing SQL when column names, types, nullability, or join keys are uncertain. Pass the `schema` used to call `list_tables` and a returned `name` as `table`. The response gives `columns` and `keys`. Inspect both sides of an unfamiliar join and use every column in a composite key. Check whether the join adds multiple rows per entity before counting or summing.

## `query`

Pass `sql` as one PostgreSQL `SELECT`. A CTE can start with `WITH`. Qualify table names with their schemas and use double quotes when an identifier requires them. `max_rows` defaults to 25 and accepts values from 1 to 100. Each statement has a five-second timeout.

- Match each value in a row to its position in `columns`. Exact PostgreSQL `numeric` values arrive as strings.
- Use explicit ordering for rankings and previews. If `truncated` is true, report the result as partial or use a query that filters or aggregates to the scope the user asked for.
- For relative dates, check the relevant date column’s minimum and maximum. State the period used, including whether it is based on the calendar or the data’s coverage.
- On a timeout, narrow the date range or simplify the query before retrying. For an unknown table or column, go back to `list_tables` or `describe_table` to verify the identifier.

Give the answer first, along with any date range, metric definition, or partial coverage that materially affects it. Include the SQL when asked or when it helps explain the result.
