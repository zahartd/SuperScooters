CREATE SCHEMA IF NOT EXISTS partman;
CREATE EXTENSION IF NOT EXISTS pg_partman WITH SCHEMA partman;

CREATE TABLE IF NOT EXISTS user_summary (
    user_id TEXT PRIMARY KEY,
    rides_count INTEGER NOT NULL DEFAULT 0,
    current_debt INTEGER NOT NULL DEFAULT 0,
    last_payment_status TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID NOT NULL,
    user_id TEXT NOT NULL,
    scooter_id TEXT NOT NULL,
    zone_id TEXT NOT NULL,
    price_per_minute INTEGER NOT NULL,
    price_unlock INTEGER NOT NULL,
    deposit INTEGER NOT NULL,
    total_amount INTEGER NOT NULL DEFAULT 0,
    start_time TIMESTAMPTZ NOT NULL,
    finish_time TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (created_at, id)
) PARTITION BY RANGE (created_at);

CREATE INDEX IF NOT EXISTS idx_orders_id ON orders (id);

SET search_path TO partman, public;
SELECT partman.create_parent(
    p_parent_table := 'public.orders',
    p_control := 'created_at',
    p_interval := '1 day',
    p_premake := 7,
    p_automatic_maintenance := 'on'
)
WHERE NOT EXISTS (SELECT 1 FROM partman.part_config WHERE parent_table = 'public.orders');
