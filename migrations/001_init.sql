-- Extensions for partitioning and scheduling
CREATE EXTENSION IF NOT EXISTS pg_partman;
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Base tables
CREATE TABLE IF NOT EXISTS user_summary (
    user_id TEXT PRIMARY KEY,
    rides_count INTEGER NOT NULL DEFAULT 0,
    current_debt INTEGER NOT NULL DEFAULT 0,
    last_payment_status TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    scooter_id TEXT NOT NULL,
    zone_id TEXT NOT NULL,
    price_per_minute INTEGER NOT NULL,
    price_unlock INTEGER NOT NULL,
    deposit INTEGER NOT NULL,
    total_amount INTEGER NOT NULL DEFAULT 0,
    start_time TIMESTAMPTZ NOT NULL,
    finish_time TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

-- Configure pg_partman to manage daily partitions for orders
SELECT partman.create_parent(
    p_parent_table := 'public.orders',
    p_control := 'created_at',
    p_type := 'native',
    p_interval := 'daily',
    p_premake := 7,
    p_automatic_maintenance := 'off'
)
WHERE NOT EXISTS (SELECT 1 FROM partman.part_config WHERE parent_table = 'public.orders');

-- Schedule regular maintenance for partitions
SELECT cron.schedule(
    'partman_maint_orders',
    '*/15 * * * *',
    $$SELECT partman.run_maintenance()$$
)
WHERE NOT EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'partman_maint_orders');
