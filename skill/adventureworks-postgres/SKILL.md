---
name: adventureworks-postgres
description: Answer questions about the fictional AdventureWorks database using the AdventureWorks Postgres MCP. Use for schema discovery, join planning, and read-only SQL analysis of AdventureWorks sales, products, purchasing, people, or employees.
---

# Query AdventureWorks with MCP

Use the connected **AdventureWorks Postgres** server. For data questions, discover tables and inspect schema when needed, then call `query` to answer from the data. A schema question can end with the metadata result. If the server is unavailable, explain that the query could not be run and label any SQL you provide as unexecuted.

## `list_tables`

Use this when you need to find a table or view, identify its schema, or explore what is available. Both arguments are optional. `schema` matches the schema name exactly, and `search` matches a literal substring of the relation name without regard to case. Call with `{}` to browse all readable tables and views. Each result gives `schema`, `name`, and `kind`.

```json
{"schema": "sales", "search": "salesorder"}
```

If a search returns no matches, try a shorter term or omit the schema filter. Use the exact names returned by the tool in subsequent calls.

## `describe_table`

Use this before writing SQL when column names, types, nullability, or join keys are uncertain. Pass the exact `schema` and `table` as separate arguments. The response gives `columns` and `keys`. Read the foreign-key definitions to find the target table and all columns in the relationship. For example, `sales.salesorderheader.territoryid` references `sales.salesterritory.territoryid`.

```json
{"schema": "sales", "table": "salesorderheader"}
```

Inspect both sides of an unfamiliar join. When joining orders to line items, use the grain requested by the user. Counting joined rows counts line items, while counting distinct order IDs counts orders.

## `query`

Use this when the answer requires values from the database. Pass `sql` as one PostgreSQL `SELECT`. A CTE can start with `WITH`. Qualify table names with their schemas. `max_rows` defaults to 25 and accepts values from 1 to 100. Each statement has a five-second timeout.

This call answers “How many orders are assigned to each territory?”

```json
{"sql": "SELECT t.name AS territory, count(*) AS order_count FROM sales.salesorderheader AS h JOIN sales.salesterritory AS t USING (territoryid) GROUP BY t.name ORDER BY order_count DESC, territory", "max_rows": 15}
```

- Match each value in a row to its position in `columns`. Exact PostgreSQL `numeric` values arrive as strings.
- Use explicit ordering for rankings and previews. If `truncated` is true, report the result as partial or use a query that filters or aggregates to the scope the user asked for.
- For relative dates, check the relevant date column’s minimum and maximum first. If you use the latest complete year in the sample, state the calendar year you used.
- On a timeout, narrow the date range or simplify the query before retrying. For an unknown table or column, go back to `list_tables` or `describe_table` to verify the identifier.

Give the answer first, along with any date range, metric definition, or partial coverage that materially affects it. Include the SQL when asked or when it helps explain the result.
