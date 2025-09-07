"""Database utilities for automatic migrations and version management."""

import os
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text
from config import settings


def get_alembic_config():
    """Get Alembic configuration."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini_path = os.path.join(project_root, 'alembic.ini')
    
    # Create Alembic config
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))
    
    return alembic_cfg


def get_current_db_revision():
    """Get the current database revision from alembic_version table."""
    try:
        # Create database engine
        db_url = settings.get_db_url
        engine = create_engine(db_url)
        
        # Connect to database and query alembic_version table
        with engine.connect() as connection:
            # Check if alembic_version table exists
            result = connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'alembic_version'"))
            if result.fetchone() is None:
                # If table doesn't exist, this is a fresh database
                return None
                
            # Get current revision
            result = connection.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            if row:
                return row[0]
            else:
                return None
    except Exception as e:
        print(f"Error getting current database revision: {e}")
        return None


def get_latest_migration_revision():
    """Get the latest migration revision from alembic/versions directory."""
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        # Get the head revision (latest migration)
        return script.get_current_head()
    except Exception as e:
        print(f"Error getting latest migration revision: {e}")
        return None


def run_migrations():
    """Run migrations if database is not up to date."""
    try:
        # Get current database revision
        current_revision = get_current_db_revision()
        
        # Get latest migration revision
        latest_revision = get_latest_migration_revision()
        
        # If revisions don't match, run migrations
        if current_revision != latest_revision:
            print(f"Database is not up to date. Current: {current_revision}, Latest: {latest_revision}")
            print("Running migrations...")
            
            # Get Alembic config
            alembic_cfg = get_alembic_config()
            
            # Run migrations to head
            command.upgrade(alembic_cfg, "head")
            
            print("Migrations completed successfully.")
            return True
        else:
            print("Database is already up to date.")
            return True
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


if __name__ == "__main__":
    # Run migrations when script is executed directly
    run_migrations()