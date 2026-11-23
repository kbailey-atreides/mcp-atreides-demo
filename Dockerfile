FROM postgres:17-alpine AS seed

RUN apk add --no-cache curl ruby unzip
WORKDIR /seed
RUN curl -fsSL --retry 3 \
      https://github.com/microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks-oltp-install-script.zip \
      -o adventureworks.zip \
    && echo '58962e94ea386ef7cd3d8a08211bfd42a79d9b81bdd68fd4b6b0051de6c5bd42  adventureworks.zip' | sha256sum -c - \
    && unzip -q adventureworks.zip '*.csv' \
    && rm adventureworks.zip
ADD --chmod=644 --checksum=sha256:27f71c99365aa5f44dba5d3b7ca092a654fcf50e6931c4dbe96ba2a13f8b7e0e https://raw.githubusercontent.com/lorint/AdventureWorks-for-Postgres/b474991f0df1c4bf55ca4735eb0254ca0709eed2/install.sql install.sql
ADD --checksum=sha256:f9c2575c21f1fc68ac9af655cb47d59ffbc1a85c1ae1b75312bb29994defa2b2 https://raw.githubusercontent.com/lorint/AdventureWorks-for-Postgres/b474991f0df1c4bf55ca4735eb0254ca0709eed2/update_csvs.rb update_csvs.rb
RUN ruby update_csvs.rb && rm update_csvs.rb

FROM postgres:17-alpine AS database
COPY --from=seed /seed /seed
COPY --chmod=755 init-db.sh /docker-entrypoint-initdb.d/01-adventureworks.sh

FROM python:3.13-slim AS mcp
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py .
COPY skill/ skill/
USER 10001
CMD ["python", "server.py"]
