# AdventureWorks Postgres MCP

A one-file Python MCP server for exploring the fictional AdventureWorks sales database. [server.py](server.py) contains the server instructions, three tool functions, and the Streamable HTTP entry point. Each `@mcp.tool` decorator exposes a Python function. FastMCP uses its type hints and docstring to describe that tool to clients.

| Tool | What you learn |
| --- | --- |
| `list_tables` | Which tables and views you can read. Filter by schema or a substring of the name. |
| `describe_table` | Column names, types, nullability, and primary, unique, and foreign keys. |
| `query` | Results from one PostgreSQL `SELECT`, which can include CTEs. The default is 25 rows, with a maximum of 100 and a five-second statement timeout. |

## Run locally

With Docker running and the Compose plugin installed, run this from the repository root.

```sh
docker compose up --build --wait
```

The first build downloads and verifies the pinned AdventureWorks source files. Postgres loads the sample when it initializes a fresh volume. The MCP endpoint on your machine is `http://127.0.0.1:8765/mcp`. Compose publishes it only on loopback and keeps Postgres on the Docker network. The MCP connects using a database role with `SELECT` grants and starts each transaction in read-only mode. The MCP annotations describe the tools to clients, while Postgres enforces the database permissions.

## Walk through a question

**Which product category had the highest merchandise sales in each territory in the last complete calendar year in the dataset?**

Use the Python FastMCP client to discover the tools, find relevant tables, inspect their join keys, and run the query. The shell command runs the client inside the MCP container so the demo only requires Docker. The client connects to the server over HTTP. For a client running on your host, install `fastmcp==4.2.5` and change the URL to `http://127.0.0.1:8765/mcp`.

```sh
docker compose exec -T mcp python - <<'PY'
import asyncio

from fastmcp import Client


async def main():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        for tool in await client.list_tools():
            print(tool.name, tool.description.splitlines()[0])

        for schema, search in [("sales", "salesorder"), ("production", "product")]:
            result = await client.call_tool("list_tables", {"schema": schema, "search": search})
            print(schema, [table["name"] for table in result.data])

        for schema, table in [
            ("sales", "salesorderheader"),
            ("sales", "salesorderdetail"),
            ("production", "product"),
            ("production", "productsubcategory"),
        ]:
            result = await client.call_tool("describe_table", {"schema": schema, "table": table})
            print(f"\n{schema}.{table}")
            for key in result.data["keys"]:
                print(" ", key["definition"])

        result = await client.call_tool("query", {"sql": """
            WITH year_start AS (
                SELECT date_trunc('year', max(orderdate)) - interval '1 year' AS start_date
                FROM sales.salesorderheader
            ), category_sales AS (
                SELECT extract(year FROM y.start_date)::int AS sales_year,
                       t.name AS territory, c.name AS category,
                       sum(d.orderqty * d.unitprice * (1 - d.unitpricediscount)) AS sales
                FROM sales.salesorderheader AS h
                JOIN sales.salesorderdetail AS d USING (salesorderid)
                JOIN sales.salesterritory AS t USING (territoryid)
                JOIN production.product AS p USING (productid)
                JOIN production.productsubcategory AS s USING (productsubcategoryid)
                JOIN production.productcategory AS c USING (productcategoryid)
                CROSS JOIN year_start AS y
                WHERE h.orderdate >= y.start_date
                  AND h.orderdate < y.start_date + interval '1 year'
                GROUP BY y.start_date, t.name, c.name
            ), ranked AS (
                SELECT *, dense_rank() OVER (PARTITION BY territory ORDER BY sales DESC) AS rank
                FROM category_sales
            )
            SELECT sales_year, territory, category, round(sales, 2) AS merchandise_sales
            FROM ranked
            WHERE rank = 1
            ORDER BY territory, category
        """})
        print("\n", result.data["columns"])
        for row in result.data["rows"]:
            print(row)


asyncio.run(main())
PY
```

The sample ends in June 2025, so the query uses 2024 and returns one row per territory. Bikes leads in all ten territories, including Southwest at `7596427.39`. Merchandise sales sum the discounted line prices before tax and freight. PostgreSQL `numeric` amounts arrive as strings to preserve their decimal precision.

The script makes each tool call explicitly. A model-powered host can instead pass the tool descriptions and input schemas to a model, then run the calls the model requests. For a graph MCP, the same sequence becomes discovering node and edge types, inspecting their properties and connections, then running a read query.

## Use the companion skill

The [AdventureWorks skill](skill/adventureworks-postgres/SKILL.md) teaches an agent when to use each tool, which arguments to pass, and how to interpret the results. It uses the shared [Agent Skills format](https://agentskills.io/specification).

| Host | Load the same `adventureworks-postgres` folder |
| --- | --- |
| Claude Code | Copy it under `.claude/skills/` at the repository root. Invoke it with `/adventureworks-postgres` or ask a matching question. [Claude Code skills](https://code.claude.com/docs/en/skills) |
| Codex | Copy it under `.agents/skills/` at the repository root. Invoke it with `$adventureworks-postgres` or ask a matching question. [Codex skills](https://learn.chatgpt.com/docs/build-skills) |

Connect the host to the MCP endpoint separately. FastMCP also serves the skill at `skill://adventureworks-postgres/SKILL.md`. In the Python walkthrough’s `async with` block, `await client.read_skill("skill://adventureworks-postgres/SKILL.md")` reads the published skill. [FastMCP skill resources](https://gofastmcp.com/docs/servers/skills)

Claude can accept a ZIP containing the skill folder, and eligible ChatGPT workspaces can upload skills. A hosted agent needs an MCP endpoint reachable from its environment. The Compose endpoint is local to the machine running Docker. [Claude uploads](https://support.claude.com/en/articles/12512180-use-skills-in-claude) · [ChatGPT uploads](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)

Stop the demo with `docker compose down`. The database volume is retained for the next run.

AdventureWorks data comes from [Microsoft SQL Server Samples](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works) and is loaded with the [AdventureWorks for Postgres port](https://github.com/lorint/AdventureWorks-for-Postgres/tree/b474991f0df1c4bf55ca4735eb0254ca0709eed2).
