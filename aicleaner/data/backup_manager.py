"""
Backup Manager - Handles database backup, restore, and archiving operations
"""
import os
import shutil
import sqlite3
import gzip
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path


class BackupManager:
    """Manages database backups, restoration, and data archiving"""
    
    def __init__(self, db_path: str, backup_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.backup_dir = Path(backup_dir or os.path.join(os.path.dirname(db_path), 'backups'))
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup configuration
        self.max_backups = 30  # Keep 30 days of backups
        self.compression_enabled = True
        self.auto_backup_enabled = True
        self.backup_interval_hours = 24
        
        self.logger.info(f"Backup manager initialized: {self.backup_dir}")
    
    def create_backup(self, backup_name: Optional[str] = None, compress: Optional[bool] = None) -> str:
        """
        Create a backup of the database
        
        Args:
            backup_name: Custom backup name, defaults to timestamp
            compress: Whether to compress the backup, defaults to config
            
        Returns:
            Path to the created backup file
        """
        try:
            if compress is None:
                compress = self.compression_enabled
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if backup_name is None:
                backup_name = f"roo_backup_{timestamp}"
            
            # Create backup filename
            backup_filename = f"{backup_name}.db"
            if compress:
                backup_filename += ".gz"
            
            backup_path = self.backup_dir / backup_filename
            
            # Create the backup
            if compress:
                self._create_compressed_backup(backup_path)
            else:
                self._create_simple_backup(backup_path)
            
            # Add metadata
            self._create_backup_metadata(backup_path, {
                'created_at': datetime.now().isoformat(),
                'original_size': os.path.getsize(self.db_path),
                'backup_size': os.path.getsize(backup_path),
                'compressed': compress,
                'version': '2.0'
            })
            
            self.logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    def _create_simple_backup(self, backup_path: Path):
        """Create a simple file copy backup"""
        shutil.copy2(self.db_path, backup_path)
    
    def _create_compressed_backup(self, backup_path: Path):
        """Create a compressed backup"""
        with open(self.db_path, 'rb') as f_in:
            with gzip.open(backup_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _create_backup_metadata(self, backup_path: Path, metadata: Dict[str, Any]):
        """Create metadata file for backup"""
        metadata_path = backup_path.with_suffix(backup_path.suffix + '.meta')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def restore_backup(self, backup_path: str, confirm: bool = False) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_path: Path to backup file
            confirm: Confirmation flag for safety
            
        Returns:
            True if restoration was successful
        """
        if not confirm:
            raise ValueError("Restoration requires explicit confirmation")
        
        try:
            backup_path_obj = Path(backup_path)
            if not backup_path_obj.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path_obj}")

            # Create a backup of current database before restoration
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            self.logger.info(f"Created pre-restoration backup: {current_backup}")

            # Restore the backup
            if backup_path_obj.suffix == '.gz':
                self._restore_compressed_backup(backup_path_obj)
            else:
                self._restore_simple_backup(backup_path_obj)
            
            # Verify the restored database
            if self._verify_database_integrity():
                self.logger.info(f"Database successfully restored from: {backup_path_obj}")
                return True
            else:
                # Restore the pre-restoration backup if verification fails
                self._restore_simple_backup(Path(current_backup))
                raise Exception("Restored database failed integrity check, reverted to original")
                
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            raise
    
    def _restore_simple_backup(self, backup_path: Path):
        """Restore from a simple backup file"""
        shutil.copy2(backup_path, self.db_path)
    
    def _restore_compressed_backup(self, backup_path: Path):
        """Restore from a compressed backup file"""
        with gzip.open(backup_path, 'rb') as f_in:
            with open(self.db_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _verify_database_integrity(self) -> bool:
        """Verify database integrity after restoration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            return result[0] == 'ok'
            
        except Exception as e:
            self.logger.error(f"Database integrity check failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.db*"):
            if backup_file.suffix in ['.db', '.gz']:
                metadata_file = backup_file.with_suffix(backup_file.suffix + '.meta')
                
                backup_info = {
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': os.path.getsize(backup_file),
                    'created_at': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                }
                
                # Load metadata if available
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        backup_info.update(metadata)
                    except Exception as e:
                        self.logger.warning(f"Failed to load metadata for {backup_file}: {e}")
                
                backups.append(backup_info)
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    def cleanup_old_backups(self, max_age_days: Optional[int] = None) -> int:
        """
        Remove old backup files
        
        Args:
            max_age_days: Maximum age in days, defaults to config
            
        Returns:
            Number of backups removed
        """
        if max_age_days is None:
            max_age_days = self.max_backups
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob("*.db*"):
            if backup_file.suffix in ['.db', '.gz']:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    try:
                        # Remove backup file
                        backup_file.unlink()
                        
                        # Remove metadata file if exists
                        metadata_file = backup_file.with_suffix(backup_file.suffix + '.meta')
                        if metadata_file.exists():
                            metadata_file.unlink()
                        
                        removed_count += 1
                        self.logger.info(f"Removed old backup: {backup_file}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to remove backup {backup_file}: {e}")
        
        self.logger.info(f"Cleanup complete: {removed_count} backups removed")
        return removed_count
    
    def export_data(self, export_path: str, format: str = 'json',
                   include_tables: Optional[List[str]] = None) -> str:
        """
        Export database data to various formats
        
        Args:
            export_path: Path for export file
            format: Export format ('json', 'csv', 'sql')
            include_tables: List of tables to include, None for all
            
        Returns:
            Path to exported file
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            if format == 'json':
                return self._export_json(conn, export_path, include_tables)
            elif format == 'csv':
                return self._export_csv(conn, export_path, include_tables)
            elif format == 'sql':
                return self._export_sql(conn, export_path, include_tables)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            raise
        finally:
            conn.close()
    
    def _export_json(self, conn: sqlite3.Connection, export_path: str,
                    include_tables: Optional[List[str]] = None) -> str:
        """Export data to JSON format"""
        cursor = conn.cursor()
        
        # Get all table names if not specified
        if include_tables is None:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            include_tables = [row[0] for row in cursor.fetchall()]
        
        export_data = {
            'export_info': {
                'created_at': datetime.now().isoformat(),
                'version': '2.0',
                'tables': include_tables
            },
            'data': {}
        }
        
        for table in include_tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            export_data['data'][table] = [dict(row) for row in rows]
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(f"Data exported to JSON: {export_path}")
        return export_path
    
    def _export_csv(self, conn: sqlite3.Connection, export_path: str,
                   include_tables: Optional[List[str]] = None) -> str:
        """Export data to CSV format (creates multiple files)"""
        import csv
        
        cursor = conn.cursor()
        export_dir = Path(export_path)
        export_dir.mkdir(exist_ok=True)
        
        # Get all table names if not specified
        if include_tables is None:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            include_tables = [row[0] for row in cursor.fetchall()]
        
        for table in include_tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if rows:
                csv_path = export_dir / f"{table}.csv"
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow([description[0] for description in cursor.description])
                    # Write data
                    writer.writerows(rows)
        
        self.logger.info(f"Data exported to CSV: {export_dir}")
        return str(export_dir)
    
    def _export_sql(self, conn: sqlite3.Connection, export_path: str,
                   include_tables: Optional[List[str]] = None) -> str:
        """Export data to SQL format"""
        with open(export_path, 'w') as f:
            for line in conn.iterdump():
                if include_tables is None:
                    f.write(f"{line}\n")
                else:
                    # Filter for specific tables
                    for table in include_tables:
                        if f"'{table}'" in line or f'"{table}"' in line:
                            f.write(f"{line}\n")
                            break
        
        self.logger.info(f"Data exported to SQL: {export_path}")
        return export_path
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup system status"""
        backups = self.list_backups()
        
        return {
            'backup_dir': str(self.backup_dir),
            'total_backups': len(backups),
            'latest_backup': backups[0] if backups else None,
            'total_backup_size': sum(b['size'] for b in backups),
            'auto_backup_enabled': self.auto_backup_enabled,
            'compression_enabled': self.compression_enabled,
            'max_backups': self.max_backups,
            'backup_interval_hours': self.backup_interval_hours
        }
