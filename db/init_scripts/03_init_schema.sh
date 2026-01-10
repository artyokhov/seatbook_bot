#!/bin/bash
set -e

echo "=== Creating schema seatbook if not exists ==="

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" <<-EOSQL
DO \$\$
BEGIN
   IF NOT EXISTS (
       SELECT 1 FROM information_schema.schemata WHERE schema_name = 'seatbook'
   ) THEN
       EXECUTE 'CREATE SCHEMA seatbook AUTHORIZATION ${DB_USER}';
   END IF;
END
\$\$;
EOSQL
