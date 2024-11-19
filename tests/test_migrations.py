import os
import tempfile
from pathlib import Path
import pytest
from sqlalchemy import inspect, MetaData, create_engine, text
from sqlmodel import SQLModel

from ell.stores.sql import init_or_migrate_database, get_alembic_config
from alembic import command
from alembic.config import Config

def get_table_metadata(engine, exclude_tables=None):
    """Helper to get table metadata in a consistent format"""
    inspector = inspect(engine)
    metadata = {}
    exclude_tables = exclude_tables or set()
    
    for table_name in inspector.get_table_names():
        if table_name in exclude_tables:
            continue
            
        columns = {col['name']: {
            'type': str(col['type']),
            'nullable': col['nullable'],
            'default': col['default'],
            'primary_key': col['primary_key']
        } for col in inspector.get_columns(table_name)}
        
        foreign_keys = [
            {'referred_table': fk['referred_table'],
             'referred_columns': fk['referred_columns'],
             'constrained_columns': fk['constrained_columns']}
            for fk in inspector.get_foreign_keys(table_name)
        ]
        
        indexes = [
            {'name': idx['name'],
             'columns': idx['column_names'],
             'unique': idx['unique']}
            for idx in inspector.get_indexes(table_name)
        ]

        # Add unique constraints
        unique_constraints = [
            {'name': const['name'],
             'columns': const['column_names']}
            for const in inspector.get_unique_constraints(table_name)
        ]
        
        metadata[table_name] = {
            'columns': columns,
            'foreign_keys': foreign_keys,
            'indexes': indexes,
            'unique_constraints': unique_constraints
        }
    
    return metadata

@pytest.fixture
def temp_db_url():
    """Create a temporary SQLite database URL""" 
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield f"sqlite:///{db_path}"

def test_empty_db_migration(temp_db_url):
    """Test migrating an empty database creates same schema as SQLModel metadata"""
    # Create engine for empty database
    engine = create_engine(temp_db_url)
    
    # Initialize database using migrations
    init_or_migrate_database(engine)
    
    # Get schema created by migrations, excluding alembic version table
    migrated_metadata = get_table_metadata(engine, exclude_tables={'ell_alembic_version'})
    
    # Create new empty database
    engine2 = create_engine(temp_db_url.replace("test.db", "test2.db"))
    
    # Create schema using SQLModel metadata
    SQLModel.metadata.create_all(engine2)
    
    # Get schema created by SQLModel
    sqlmodel_metadata = get_table_metadata(engine2)
    
    # Compare schemas
    assert migrated_metadata == sqlmodel_metadata

def test_existing_tables_no_alembic(temp_db_url):
    """Test database with existing tables but no alembic version table"""
    engine = create_engine(temp_db_url)
    
    # Create tables using SQLModel
    SQLModel.metadata.create_all(engine)
    
    # Initialize/migrate database
    init_or_migrate_database(engine)
    
    # Verify alembic version table exists and has correct version
    inspector = inspect(engine)
    assert 'ell_alembic_version' in inspector.get_table_names()
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM ell_alembic_version"))
        version = result.scalar()
        assert version == "4524fb60d23e"  # Initial migration version

def test_multiple_migrations(temp_db_url):
    """Test running multiple migrations in sequence"""
    engine = create_engine(temp_db_url)
    
    # Get alembic config
    alembic_cfg = get_alembic_config(str(engine.url))
    
    # Start with empty database
    init_or_migrate_database(engine)
    
    # Verify we're at head revision
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM ell_alembic_version"))
        version = result.scalar()
        assert version
    
    # Downgrade to base
    command.downgrade(alembic_cfg, "base")
    
    # Verify no version
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM ell_alembic_version"))
        first_version = result.scalar()
        assert first_version is None
    
    # Upgrade to head again
    command.upgrade(alembic_cfg, "head")
    
    # Verify back at head
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM ell_alembic_version"))
        new_version = result.scalar()
        assert version == new_version

def test_migration_idempotency(temp_db_url):
    """Test that running migrations multiple times is idempotent"""
    engine = create_engine(temp_db_url)
    
    # Initial migration
    init_or_migrate_database(engine)
    initial_metadata = get_table_metadata(engine)
    
    # Run migration again
    init_or_migrate_database(engine)
    final_metadata = get_table_metadata(engine)
    
    # Verify schemas are identical
    assert initial_metadata == final_metadata

def test_pure_migration_matches_metadata(temp_db_url):
    """
    Test that running just the initial migration (without SQLModel.metadata) 
    creates the same schema as SQLModel.metadata
    """
    # Create first empty database for migration
    engine1 = create_engine(temp_db_url)
    
    # Get alembic config and run just the initial migration
    alembic_cfg = get_alembic_config(str(engine1.url))
    command.upgrade(alembic_cfg, "4524fb60d23e")  # Run initial migration only
    # Upgrade to head to ensure we're on latest version
    command.upgrade(alembic_cfg, "head")
    
    # Get schema created by migration
    migration_metadata = get_table_metadata(engine1, exclude_tables={'ell_alembic_version'})
    
    # Create second empty database for SQLModel metadata
    engine2 = create_engine(temp_db_url.replace("test.db", "test2.db"))
    
    # Create tables using SQLModel metadata
    SQLModel.metadata.create_all(engine2)
    
    # Get schema created by SQLModel
    sqlmodel_metadata = get_table_metadata(engine2)
    
    assert migration_metadata == sqlmodel_metadata
