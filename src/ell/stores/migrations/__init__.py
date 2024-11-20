
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select
import logging

logger = logging.getLogger(__name__)

def get_alembic_config(engine_url: str) -> Config:
    """Create Alembic config programmatically"""
    alembic_cfg = Config()
    migrations_dir = Path(__file__).parent
    
    alembic_cfg.set_main_option("script_location", str(migrations_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", str(engine_url))
    alembic_cfg.set_main_option("version_table", "ell_alembic_version")
    alembic_cfg.set_main_option("timezone", "UTC")
    
    return alembic_cfg

def init_or_migrate_database(engine) -> None:
    """Initialize or migrate database with ELL schema
    
    Handles three cases:
    1. Existing database with our tables but no Alembic -> stamp with initial migration
    2. Database with Alembic -> upgrade to head
    3. New/empty database or database without our tables -> create tables and stamp with head
    
    Args:
        engine_or_url: SQLAlchemy engine or database URL string
    """ 
    inspector = inspect(engine)
    
    # Check database state
    our_tables_v1 = {'serializedlmp', 'invocation', 'invocationcontents', 
                  'invocationtrace', 'serializedlmpuses'}
    our_tables_v2 = {'evaluationlabeler', 'evaluationresultdatapoint', 'evaluationrunlabelersummary', 'evaluationlabel'}
    existing_tables = set(inspector.get_table_names())
    has_our_tables = bool(our_tables_v1 & existing_tables)  # Intersection
    has_alembic = 'ell_alembic_version' in existing_tables

    alembic_cfg = get_alembic_config(engine.url.render_as_string(hide_password=False))
    try:
        if has_our_tables and not has_alembic:
            # Case 1: Existing database with our tables but no Alembic
            # This is likely a database from version <= 0.14
            logger.debug("Found existing tables but no Alembic - stamping with initial migration")
            is_v1 = has_our_tables and not bool(our_tables_v2 & existing_tables)
            command.stamp(alembic_cfg, "4524fb60d23e" if is_v1 else "head")
         
            # Verify table was created
            after_tables = set(inspect(engine).get_table_names())
            logger.debug(f"Tables after stamp: {after_tables}")
            if is_v1:
                # Check if version table has our stamp
                with engine.connect() as connection:
                    version_result = connection.execute(text("SELECT version_num FROM ell_alembic_version")).first()
                    if not version_result or version_result[0] != "4524fb60d23e":
                        raise RuntimeError("Failed to stamp database - version table empty or incorrect version")
                    logger.debug(f"Successfully stamped database with version {version_result[0]}")

            has_alembic = True

        if has_alembic:
            # Case 2: Database has Alembic - run any pending migrations
            logger.debug("Running any pending Alembic migrations")
            command.upgrade(alembic_cfg, "head")
            
        else:
            # Case 3: New database or database without our tables
            logger.debug("New database detected - creating schema and stamping with latest migration")
            # Create all tables according to current schema
            SQLModel.metadata.create_all(engine)
            # Stamp with latest migration
            command.stamp(alembic_cfg, "head")
            
    except Exception as e:
        logger.error(f"Failed to initialize/migrate database: {e}")
        raise
