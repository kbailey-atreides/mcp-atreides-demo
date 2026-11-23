# Postgres Explorer MCP

A one-file Python MCP server for discovering and querying a connected PostgreSQL database. [server.py](server.py) contains the server instructions, four tool functions, and the Streamable HTTP entry point. Each `@mcp.tool` decorator exposes a Python function. FastMCP uses its type hints and docstring to describe that tool to clients.

<table>
  <thead>
    <tr>
      <th>Tool</th>
      <th>What you learn</th>
      <th>Example input</th>
      <th>Example output</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>list_schemas</code></td>
      <td>Which schemas contain readable tables or views.</td>
      <td>
        <details>
          <summary>Show input</summary>
          <p>This tool takes zero arguments.</p>
          <pre><code>{}</code></pre>
        </details>
      </td>
      <td>
        <details>
          <summary>Show output</summary>
          <pre><code>{
  "result": ["humanresources", "person", "production", "purchasing", "sales"]
}</code></pre>
        </details>
      </td>
    </tr>
    <tr>
      <td><code>list_tables</code></td>
      <td>Which tables and views you can read in one schema.</td>
      <td>
        <details>
          <summary>Show input</summary>
          <p><code>schema</code> is a required string. Use a name returned by <code>list_schemas</code>.</p>
          <pre><code>{"schema": "purchasing"}</code></pre>
        </details>
      </td>
      <td>
        <details>
          <summary>Show output</summary>
          <pre><code>{
  "result": [
    {"name": "productvendor", "kind": "BASE TABLE"},
    {"name": "purchaseorderdetail", "kind": "BASE TABLE"},
    {"name": "purchaseorderheader", "kind": "BASE TABLE"},
    {"name": "shipmethod", "kind": "BASE TABLE"},
    {"name": "vendor", "kind": "BASE TABLE"},
    {"name": "vvendorwithaddresses", "kind": "VIEW"},
    {"name": "vvendorwithcontacts", "kind": "VIEW"}
  ]
}</code></pre>
        </details>
      </td>
    </tr>
    <tr>
      <td><code>describe_table</code></td>
      <td>Column names, types, nullability, and keys.</td>
      <td>
        <details>
          <summary>Show input</summary>
          <p><code>schema</code> and <code>table</code> are required strings.</p>
          <pre><code>{"schema": "purchasing", "table": "shipmethod"}</code></pre>
        </details>
      </td>
      <td>
        <details>
          <summary>Show output</summary>
          <pre><code>{
  "schema": "purchasing",
  "table": "shipmethod",
  "columns": [
    {"name": "shipmethodid", "type": "integer", "nullable": false},
    {"name": "name", "type": "public.\"Name\"", "nullable": false},
    {"name": "shipbase", "type": "numeric", "nullable": false},
    {"name": "shiprate", "type": "numeric", "nullable": false},
    {"name": "rowguid", "type": "uuid", "nullable": false},
    {"name": "modifieddate", "type": "timestamp without time zone", "nullable": false}
  ],
  "keys": [
    {"name": "PK_ShipMethod_ShipMethodID", "definition": "PRIMARY KEY (shipmethodid)"}
  ]
}</code></pre>
        </details>
      </td>
    </tr>
    <tr>
      <td><code>query</code></td>
      <td>Results from a read-only SQL query.</td>
      <td>
        <details>
          <summary>Show input</summary>
          <p><code>sql</code> is one PostgreSQL <code>SELECT</code> with a five-second timeout. <code>max_rows</code> is an optional integer from 1–100 and defaults to 25.</p>
          <pre><code>{
  "sql": "SELECT shipmethodid, name FROM purchasing.shipmethod ORDER BY shipmethodid",
  "max_rows": 2
}</code></pre>
        </details>
      </td>
      <td>
        <details>
          <summary>Show output</summary>
          <p>Each row follows <code>columns</code> order. <code>truncated</code> indicates that more rows were available.</p>
          <pre><code>{
  "columns": ["shipmethodid", "name"],
  "rows": [[1, "XRQ - TRUCK GROUND"], [2, "ZY - EXPRESS"]],
  "truncated": true
}</code></pre>
        </details>
      </td>
    </tr>
  </tbody>
</table>

The harness discovers tools and their input schemas with `tools/list`. It sends `name` and `arguments` with `tools/call` and receives `structuredContent`. The examples follow the discovery flow in the bundled AdventureWorks data.

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
