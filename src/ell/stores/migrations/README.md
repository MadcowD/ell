# ell Database Migrations

This directory contains the database migration utilities for ell's SQL storage backend. The migration system uses Alembic to handle schema changes and version control for the database.

## Overview

The migration system handles:
- Initial schema creation
- Schema updates and changes
- Version tracking of database changes
- Automatic migration detection and application

## Key Components

- `versions/`: Contains individual migration scripts
- `env.py`: Alembic environment configuration
- `script.py.mako`: Template for generating new migrations
- `make.py`: Utility script for creating new migrations

## Usage

### Creating a New Migration
```bash
python -m ell.stores.migrations.make "your migration message"
```

This will:
1. Create a temporary SQLite database
2. Detect schema changes
3. Generate a new migration file in the versions directory

### Applying Migrations

Migrations are automatically handled by the `init_or_migrate_database()` function in `ell.stores.sql`. When initializing an ell store, it will:

1. Check for existing tables
2. Apply any pending migrations
3. Initialize new databases with the latest schema

## Migration Files

Each migration file contains:
- Unique revision ID
- Dependencies on other migrations
- `upgrade()` function for applying changes
- `downgrade()` function for reverting changes

For examples, see the existing migrations in the `versions/` directory.