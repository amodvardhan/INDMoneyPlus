"""Alembic environment configuration"""
from logging.config import fileConfig
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from alembic import context
from app.core.config import settings
from app.models.instrument import Base

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url with settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Convert async URL to sync URL for Alembic
    sync_url = settings.database_url.replace("+asyncpg", "")
    connectable = create_engine(
        sync_url,
        poolclass=NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
            
            # Try to enable TimescaleDB extension and convert price_points to hypertable
            try:
                from sqlalchemy import text
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
                # Check if price_points table exists and is not already a hypertable
                result = connection.execute(
                    text("SELECT EXISTS (SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_name = 'price_points')")
                )
                is_hypertable = result.scalar()
                
                if not is_hypertable:
                    # Convert price_points to hypertable
                    connection.execute(
                        text("SELECT create_hypertable('price_points', 'timestamp', if_not_exists => TRUE)")
                    )
                    connection.commit()
                    print("✓ TimescaleDB hypertable created for price_points")
            except Exception as e:
                # If TimescaleDB is not available, continue with regular Postgres
                print(f"⚠ TimescaleDB not available, using regular Postgres: {e}")

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

