import argparse
from sqlalchemy import create_engine
from ell.stores.migrations import get_alembic_config
from alembic import command

def main():
    parser = argparse.ArgumentParser(description='Create a new database migration')
    parser.add_argument('message', help='Migration message/description')
    
    args = parser.parse_args()
    
    # Create temporary directory for SQLite database
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "temp.db"
        engine = create_engine(f"sqlite:///{db_path}")
        alembic_cfg = get_alembic_config(str(engine.url))

        # First, upgrade to head to get to latest migration state
        command.upgrade(alembic_cfg, "head")

        # Now generate new migration 
        command.revision(alembic_cfg,
                        message=args.message,
                    autogenerate=True)
    
    print(f"✨ Created new migration with message: {args.message}")

if __name__ == '__main__':
    main() 