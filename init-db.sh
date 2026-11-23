#!/bin/sh
set -eu

cd /seed
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set ON_ERROR_STOP=1 \
    --set database="$POSTGRES_DB" --single-transaction --file install.sql --file - <<'SQL'
CREATE ROLE mcp_reader LOGIN PASSWORD 'demo-reader';
ALTER ROLE mcp_reader SET default_transaction_read_only = on;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE TEMPORARY ON DATABASE :"database" FROM PUBLIC;
GRANT USAGE ON SCHEMA humanresources, person, production, purchasing, sales TO mcp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA humanresources, person, production, purchasing, sales TO mcp_reader;
SQL
