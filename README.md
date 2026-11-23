# Postgres Explorer MCP

A one-file Python MCP server for discovering and querying a connected PostgreSQL database. [server.py](server.py) contains the server instructions, three tool functions, and the Streamable HTTP entry point. Each `@mcp.tool` decorator exposes a Python function. FastMCP uses its type hints and docstring to describe that tool to clients.

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

The first build downloads and verifies the sample dataset. Postgres loads it when it initializes a fresh volume. The MCP endpoint on your machine is `http://127.0.0.1:8765/mcp`. Compose publishes it only on loopback and keeps Postgres on the Docker network. The MCP connects using a database role with `SELECT` grants and starts each transaction in read-only mode. The MCP annotations describe the tools to clients, while Postgres enforces the database permissions.

To explore another PostgreSQL database, set `DATABASE_URL` for the MCP process to a connection string for a read-only role on that database.

Stop the demo with `docker compose down`. The database volume is retained for the next run.

## Connect the MCP and load the skill

The [Postgres Explorer skill](skill/postgres-explorer/SKILL.md) teaches the agent how to discover the available data and when to use each tool. Use the same `skill/postgres-explorer` folder in your chosen host.

### Claude Code

From the repository root, register the server and copy the skill folder under `.claude/skills/`. Invoke `/postgres-explorer` in a Claude Code session opened in this repository or ask a matching question. [MCP setup](https://code.claude.com/docs/en/mcp) · [Claude Code skills](https://code.claude.com/docs/en/skills)

```sh
claude mcp add --transport http postgres-explorer http://127.0.0.1:8765/mcp
```

### Codex and ChatGPT desktop

Register the server with the Codex CLI or add it in the ChatGPT desktop app under **Settings → MCP servers** as a Streamable HTTP server. For a local Codex session in this repository, copy the skill folder under `.agents/skills/` and invoke `$postgres-explorer` or ask a matching question. Eligible ChatGPT workspaces can also upload the skill. [MCP setup](https://learn.chatgpt.com/docs/extend/mcp) · [Codex skills](https://learn.chatgpt.com/docs/build-skills) · [ChatGPT skill uploads](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)

```sh
codex mcp add postgres-explorer --url http://127.0.0.1:8765/mcp
```

### Claude Desktop

Upload a ZIP containing the skill folder under **Customize → Skills**. If you connect the MCP as a custom connector, use an endpoint reachable from Anthropic’s servers. The Compose URL is loopback-only, so use Claude Code for the local setup above. [Claude skill uploads](https://support.claude.com/en/articles/12512180-use-skills-in-claude) · [Claude custom connectors](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp)

## Questions you can ask

Once the MCP and skill are available in your host, start by asking it to discover the data.

> What data can you see? Summarize the available schemas and suggest three questions I could ask based on the tables you find.

### Try the bundled dataset

The Docker demo loads AdventureWorks, a fictional bicycle wholesaler database. Try these questions after exploring the schema.

- “What tables and views in the sales schema relate to orders?”
- “Which columns join sales orders to their line items and sales territories? Show me the foreign keys.”
- “How many orders were assigned to each sales territory? Sort from most to fewest.”
- “Which product category had the highest merchandise sales in each territory in the last complete calendar year in the dataset? Use discounted line totals before tax and freight.”
- “Which five products generated the most merchandise sales in the Southwest territory in 2024? Use discounted line totals before tax and freight, and show the SQL you ran.”

For the demo, ask the agent to name the MCP tools it called and explain how it chose the join keys. The order-count prompt should cover **31,465 orders across 10 territories**. The category-ranking prompt should use **2024**, the last complete year in the sample.

AdventureWorks data comes from [Microsoft SQL Server Samples](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/adventure-works) and is loaded with the [AdventureWorks for Postgres port](https://github.com/lorint/AdventureWorks-for-Postgres/tree/b474991f0df1c4bf55ca4735eb0254ca0709eed2).
