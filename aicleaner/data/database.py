"""
Database connection and management for Roo AI Cleaning Assistant v2.0
"""
import sqlite3
import logging
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from pathlib import Path


class DatabaseManager:
    """Manages SQLite database connections and migrations"""
    
    def __init__(self, db_path: str = "/data/roo.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._ensure_database_directory()
        self._initialize_database()
    
    def _ensure_database_directory(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            self.logger.info(f"Created database directory: {db_dir}")
    
    def _initialize_database(self):
        """Initialize database with schema if it doesn't exist"""
        if not os.path.exists(self.db_path):
            self.logger.info("Database doesn't exist, creating new database")
            self._create_database()
        else:
            self.logger.info(f"Using existing database: {self.db_path}")
            self._check_and_migrate()
    
    def _create_database(self):
        """Create new database with initial schema"""
        try:
            with self.get_connection() as conn:
                # Read and execute the initial schema
                schema_path = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
                if schema_path.exists():
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                    conn.executescript(schema_sql)
                    conn.commit()
                    self.logger.info("Database created successfully with initial schema")
                else:
                    self.logger.error(f"Schema file not found: {schema_path}")
                    raise FileNotFoundError(f"Schema file not found: {schema_path}")
        except Exception as e:
            self.logger.error(f"Failed to create database: {e}")
            raise
    
    def _check_and_migrate(self):
        """Check database version and apply migrations if needed"""
        try:
            with self.get_connection() as conn:
                # Check if we have a version table
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_version'
                """)
                
                if not cursor.fetchone():
                    # This is a v1.0 database or new database, apply migrations
                    self.logger.info("Applying database migrations")
                    self._apply_migrations(conn)
                else:
                    # Check current version and apply any pending migrations
                    current_version = self._get_schema_version(conn)
                    self.logger.info(f"Current database version: {current_version}")
                    self._apply_pending_migrations(conn, current_version)
        except Exception as e:
            self.logger.error(f"Failed to check/migrate database: {e}")
            raise
    
    def _apply_migrations(self, conn: sqlite3.Connection):
        """Apply all migrations to the database"""
        # Create version table first
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Apply initial schema if tables don't exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='zones'
        """)
        
        if not cursor.fetchone():
            schema_path = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                
                # Mark as version 1
                conn.execute("INSERT INTO schema_version (version) VALUES (1)")
                conn.commit()
                self.logger.info("Applied initial schema migration")
    
    def _apply_pending_migrations(self, conn: sqlite3.Connection, current_version: int):
        """Apply any pending migrations"""
        migrations_dir = Path(__file__).parent.parent / "migrations"
        migration_files = sorted([f for f in migrations_dir.glob("*.sql") if f.name.startswith("00")])
        
        for migration_file in migration_files:
            # Extract version number from filename (e.g., "002_add_metrics.sql" -> 2)
            try:
                file_version = int(migration_file.name.split('_')[0])
                if file_version > current_version:
                    self.logger.info(f"Applying migration: {migration_file.name}")
                    with open(migration_file, 'r') as f:
                        migration_sql = f.read()
                    conn.executescript(migration_sql)
                    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (file_version,))
                    conn.commit()
                    self.logger.info(f"Applied migration {file_version}")
            except (ValueError, IndexError):
                self.logger.warning(f"Skipping invalid migration file: {migration_file.name}")
    
    def _get_schema_version(self, conn: sqlite3.Connection) -> int:
        """Get current schema version"""
        cursor = conn.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def execute_single(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute a SELECT query and return single result"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the new row ID"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def execute_batch(self, queries: List[tuple]) -> None:
        """Execute multiple queries in a transaction"""
        with self.get_connection() as conn:
            for query, params in queries:
                conn.execute(query, params)
            conn.commit()
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            with self.get_connection() as source:
                backup_conn = sqlite3.connect(backup_path)
                source.backup(backup_conn)
                backup_conn.close()
            self.logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        try:
            with self.get_connection() as conn:
                # Get table counts
                tables = ['zones', 'tasks', 'task_history', 'ignore_rules', 'performance_metrics']
                for table in tables:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Get database size
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()[0]
                
                # Get schema version
                stats['schema_version'] = self._get_schema_version(conn)
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            stats['error'] = str(e)
        
        return stats
    
    def vacuum_database(self) -> bool:
        """Optimize database by running VACUUM"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
            self.logger.info("Database vacuumed successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to vacuum database: {e}")
            return False


# Global database instance
_db_manager: Optional[DatabaseManager] = None


def get_database() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        db_path = os.environ.get('DATABASE_PATH', '/data/roo.db')
        _db_manager = DatabaseManager(db_path)
    return _db_manager


def initialize_database(db_path: str = "/data/roo.db") -> DatabaseManager:
    """Initialize the global database manager"""
    global _db_manager
    _db_manager = DatabaseManager(db_path)
    return _db_manager
