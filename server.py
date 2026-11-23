import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any

import psycopg
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.skills.provider import SkillsDirectoryProvider
from psycopg.rows import dict_row
from pydantic import Field
from pydantic_core import to_json


mcp = FastMCP(
    "AdventureWorks Postgres",
    providers=[SkillsDirectoryProvider(Path(__file__).resolve().parent / "skill")],
    instructions=(
        "Answer questions about AdventureWorks. Use list_tables to discover tables, "
        "describe_table to find columns and join keys, and query to run a read-only "
        "PostgreSQL SELECT. Use schema-qualified table names. The data is historical, "
        "so check the date range when answering questions about recent periods."
    ),
)

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False}


@contextmanager
def database():
    # Each tool call gets its own transaction and closes its connection afterward.
    try:
        with psycopg.connect(
            os.environ["DATABASE_URL"],
            connect_timeout=5,
            options="-c statement_timeout=5000 -c search_path=pg_catalog",
        ) as connection:
            connection.read_only = True
            yield connection
    except psycopg.Error as exc:
        raise ToolError(exc.diag.message_primary or "PostgreSQL is unavailable.") from exc


@mcp.tool(tags={"postgres", "metadata"}, annotations=READ_ONLY)
def list_tables(schema: str | None = None, search: str = "") -> list[dict[str, str]]:
    """Find readable tables and views by schema or case-insensitive name substring."""
    with database() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT table_schema AS schema, table_name AS name, table_type AS kind
            FROM information_schema.tables
            WHERE table_schema = coalesce(%s, table_schema)
              AND table_schema NOT IN ('information_schema', 'pg_catalog')
              AND table_schema !~ '^pg_'
              AND table_type IN ('BASE TABLE', 'VIEW', 'FOREIGN')
              AND has_table_privilege(
                  format('%%I.%%I', table_schema, table_name), 'SELECT'
              )
              AND strpos(lower(table_name), lower(%s)) > 0
            ORDER BY table_schema, table_name
            """,
            (schema, search),
        )
        return cursor.fetchall()


@mcp.tool(tags={"postgres", "metadata"}, annotations=READ_ONLY)
def describe_table(schema: str, table: str) -> dict[str, Any]:
    """Show column types, nullability, and primary, unique, and foreign keys."""
    with database() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            """
            SELECT c.oid AS relation_id, a.attname AS name,
                   format_type(a.atttypid, a.atttypmod) AS type,
                   NOT (a.attnotnull OR t.typnotnull) AS nullable
            FROM pg_namespace AS n
            JOIN pg_class AS c ON c.relnamespace = n.oid
            JOIN pg_attribute AS a ON a.attrelid = c.oid
            JOIN pg_type AS t ON t.oid = a.atttypid
            WHERE n.nspname = %s AND c.relname = %s
              AND n.nspname <> 'information_schema' AND n.nspname !~ '^pg_'
              AND c.relkind IN ('r', 'p', 'v', 'f')
              AND a.attnum > 0 AND NOT a.attisdropped
              AND has_table_privilege(c.oid, 'SELECT')
            ORDER BY a.attnum
            """,
            (schema, table),
        )
        columns = cursor.fetchall()
        if not columns:
            raise ToolError(f"No readable table or view with columns named {schema}.{table}.")

        relation_id = columns[0]["relation_id"]
        for column in columns:
            del column["relation_id"]

        cursor.execute(
            """
            SELECT conname AS name, pg_get_constraintdef(oid) AS definition
            FROM pg_constraint
            WHERE conrelid = %s AND contype IN ('p', 'u', 'f')
            ORDER BY contype, conname
            """,
            (relation_id,),
        )
        return {"schema": schema, "table": table, "columns": columns, "keys": cursor.fetchall()}


@mcp.tool(tags={"postgres", "query"}, annotations=READ_ONLY)
def query(
    sql: str,
    max_rows: Annotated[int, Field(ge=1, le=100)] = 25,
) -> dict[str, Any]:
    """Run one PostgreSQL SELECT, optionally with a CTE. Use schema-qualified names.

    Returns column names and positional rows, with a flag if more rows were available.
    Use ORDER BY for a predictable preview. PostgreSQL times out statements after 5 seconds.
    """
    with database() as connection, connection.cursor(name="demo_query") as cursor:
        # A PostgreSQL server-side cursor accepts one row-producing SELECT and
        # lets us cap the rows fetched from the database.
        cursor.execute(sql)
        columns = [column.name for column in cursor.description]
        rows = cursor.fetchmany(max_rows + 1)
        # Normalize PostgreSQL types, including bytea and non-finite floats, for MCP JSON.
        encoded_rows = to_json(
            rows[:max_rows], bytes_mode="base64", inf_nan_mode="strings", fallback=str
        )
        return {
            "columns": columns,
            "rows": json.loads(encoded_rows),
            "truncated": len(rows) > max_rows,
        }


if __name__ == "__main__":
    mcp.run(transport="http", host=os.getenv("MCP_HOST", "127.0.0.1"), port=8000)
