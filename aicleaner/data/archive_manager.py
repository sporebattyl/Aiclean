"""
Archive Manager - Handles data archiving and cleanup for performance optimization
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from .database import DatabaseManager


class ArchiveManager:
    """Manages data archiving and cleanup operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        
        # Archive configuration
        self.archive_rules = {
            'task_history': {
                'retention_days': 90,
                'archive_after_days': 30,
                'batch_size': 1000
            },
            'notifications_log': {
                'retention_days': 60,
                'archive_after_days': 14,
                'batch_size': 500
            },
            'performance_metrics': {
                'retention_days': 365,
                'archive_after_days': 90,
                'batch_size': 100
            },
            'tasks': {
                'retention_days': 180,  # Keep completed tasks for 6 months
                'archive_after_days': 30,
                'batch_size': 1000,
                'status_filter': ['completed', 'auto_completed', 'ignored']
            }
        }
        
        self.logger.info("Archive manager initialized")
    
    def archive_old_data(self, table_name: str = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Archive old data based on configured rules
        
        Args:
            table_name: Specific table to archive, None for all
            dry_run: If True, only report what would be archived
            
        Returns:
            Dictionary with archiving results
        """
        results = {
            'archived_records': 0,
            'deleted_records': 0,
            'tables_processed': [],
            'errors': [],
            'dry_run': dry_run
        }
        
        tables_to_process = [table_name] if table_name else list(self.archive_rules.keys())
        
        for table in tables_to_process:
            if table not in self.archive_rules:
                self.logger.warning(f"No archive rules defined for table: {table}")
                continue
            
            try:
                table_result = self._archive_table_data(table, dry_run)
                results['archived_records'] += table_result['archived']
                results['deleted_records'] += table_result['deleted']
                results['tables_processed'].append({
                    'table': table,
                    'archived': table_result['archived'],
                    'deleted': table_result['deleted']
                })
                
            except Exception as e:
                error_msg = f"Failed to archive {table}: {e}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
        
        self.logger.info(f"Archive operation complete: {results}")
        return results
    
    def _archive_table_data(self, table_name: str, dry_run: bool = False) -> Dict[str, int]:
        """Archive data for a specific table"""
        rules = self.archive_rules[table_name]
        archive_cutoff = datetime.now() - timedelta(days=rules['archive_after_days'])
        retention_cutoff = datetime.now() - timedelta(days=rules['retention_days'])
        
        archived_count = 0
        deleted_count = 0
        
        # Create archive table if it doesn't exist
        archive_table = f"{table_name}_archive"
        if not dry_run:
            self._create_archive_table(table_name, archive_table)
        
        # Archive old data (move to archive table)
        archived_count = self._move_to_archive(
            table_name, archive_table, archive_cutoff, rules, dry_run
        )
        
        # Delete very old data from archive
        deleted_count = self._delete_old_archive_data(
            archive_table, retention_cutoff, rules, dry_run
        )
        
        return {
            'archived': archived_count,
            'deleted': deleted_count
        }
    
    def _create_archive_table(self, source_table: str, archive_table: str):
        """Create archive table with same structure as source table"""
        try:
            # Get source table schema
            schema_query = f"""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='{source_table}'
            """
            result = self.db.execute_single(schema_query)
            
            if result:
                # Modify CREATE statement for archive table
                create_sql = result['sql'].replace(
                    f"CREATE TABLE {source_table}",
                    f"CREATE TABLE IF NOT EXISTS {archive_table}"
                )
                
                # Add archive-specific columns
                if 'archived_at' not in create_sql:
                    create_sql = create_sql.rstrip(')') + ', archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
                
                self.db.execute_query(create_sql)
                self.logger.debug(f"Created archive table: {archive_table}")
                
        except Exception as e:
            self.logger.error(f"Failed to create archive table {archive_table}: {e}")
            raise
    
    def _move_to_archive(self, source_table: str, archive_table: str, 
                        cutoff_date: datetime, rules: Dict[str, Any], 
                        dry_run: bool = False) -> int:
        """Move old records to archive table"""
        try:
            # Build WHERE clause based on table-specific rules
            where_clause = self._build_archive_where_clause(source_table, cutoff_date, rules)
            
            if dry_run:
                # Count records that would be archived
                count_query = f"SELECT COUNT(*) as count FROM {source_table} WHERE {where_clause}"
                result = self.db.execute_single(count_query)
                return result['count'] if result else 0
            
            # Get column names (excluding archive-specific columns)
            columns_query = f"PRAGMA table_info({source_table})"
            columns_result = self.db.execute_query(columns_query)
            columns = [col['name'] for col in columns_result]
            columns_str = ', '.join(columns)
            
            # Move data in batches
            batch_size = rules.get('batch_size', 1000)
            total_moved = 0
            
            while True:
                # Insert into archive
                insert_query = f"""
                    INSERT INTO {archive_table} ({columns_str})
                    SELECT {columns_str} FROM {source_table}
                    WHERE {where_clause}
                    LIMIT {batch_size}
                """
                
                rows_inserted = self.db.execute_insert(insert_query)
                
                if rows_inserted == 0:
                    break
                
                # Delete from source
                delete_query = f"""
                    DELETE FROM {source_table}
                    WHERE rowid IN (
                        SELECT rowid FROM {source_table}
                        WHERE {where_clause}
                        LIMIT {batch_size}
                    )
                """
                
                self.db.execute_query(delete_query)
                total_moved += rows_inserted
                
                self.logger.debug(f"Moved {rows_inserted} records from {source_table} to {archive_table}")
            
            self.logger.info(f"Archived {total_moved} records from {source_table}")
            return total_moved
            
        except Exception as e:
            self.logger.error(f"Failed to move data to archive: {e}")
            raise
    
    def _delete_old_archive_data(self, archive_table: str, cutoff_date: datetime, 
                                rules: Dict[str, Any], dry_run: bool = False) -> int:
        """Delete very old data from archive table"""
        try:
            where_clause = f"archived_at < '{cutoff_date.isoformat()}'"
            
            if dry_run:
                count_query = f"SELECT COUNT(*) as count FROM {archive_table} WHERE {where_clause}"
                result = self.db.execute_single(count_query)
                return result['count'] if result else 0
            
            # Delete in batches
            batch_size = rules.get('batch_size', 1000)
            total_deleted = 0
            
            while True:
                delete_query = f"""
                    DELETE FROM {archive_table}
                    WHERE rowid IN (
                        SELECT rowid FROM {archive_table}
                        WHERE {where_clause}
                        LIMIT {batch_size}
                    )
                """
                
                rows_deleted = self.db.execute_query(delete_query)
                if rows_deleted == 0:
                    break
                
                total_deleted += rows_deleted
                self.logger.debug(f"Deleted {rows_deleted} old records from {archive_table}")
            
            self.logger.info(f"Deleted {total_deleted} old records from {archive_table}")
            return total_deleted
            
        except Exception as e:
            self.logger.error(f"Failed to delete old archive data: {e}")
            raise
    
    def _build_archive_where_clause(self, table_name: str, cutoff_date: datetime, 
                                   rules: Dict[str, Any]) -> str:
        """Build WHERE clause for archiving based on table-specific rules"""
        base_clause = f"created_at < '{cutoff_date.isoformat()}'"
        
        # Add table-specific conditions
        if table_name == 'tasks' and 'status_filter' in rules:
            status_list = "', '".join(rules['status_filter'])
            base_clause += f" AND status IN ('{status_list}')"
        
        return base_clause
    
    def get_archive_statistics(self) -> Dict[str, Any]:
        """Get statistics about archived data"""
        stats = {
            'tables': {},
            'total_archive_size': 0,
            'total_main_size': 0
        }
        
        for table_name in self.archive_rules.keys():
            archive_table = f"{table_name}_archive"
            
            # Get main table stats
            main_count = self._get_table_count(table_name)
            main_size = self._get_table_size(table_name)
            
            # Get archive table stats
            archive_count = self._get_table_count(archive_table)
            archive_size = self._get_table_size(archive_table)
            
            stats['tables'][table_name] = {
                'main_records': main_count,
                'main_size_kb': main_size,
                'archive_records': archive_count,
                'archive_size_kb': archive_size,
                'total_records': main_count + archive_count
            }
            
            stats['total_archive_size'] += archive_size
            stats['total_main_size'] += main_size
        
        return stats
    
    def _get_table_count(self, table_name: str) -> int:
        """Get record count for a table"""
        try:
            result = self.db.execute_single(f"SELECT COUNT(*) as count FROM {table_name}")
            return result['count'] if result else 0
        except:
            return 0
    
    def _get_table_size(self, table_name: str) -> int:
        """Get approximate size of table in KB"""
        try:
            # Get page count and page size
            page_count_result = self.db.execute_single(f"SELECT COUNT(*) as pages FROM pragma_page_list('{table_name}')")
            page_size_result = self.db.execute_single("PRAGMA page_size")
            
            if page_count_result and page_size_result:
                pages = page_count_result['pages']
                page_size = page_size_result['page_size']
                return (pages * page_size) // 1024  # Convert to KB
            
            return 0
        except:
            return 0
    
    def optimize_database(self) -> Dict[str, Any]:
        """Optimize database performance after archiving"""
        results = {
            'vacuum_completed': False,
            'analyze_completed': False,
            'reindex_completed': False,
            'size_before_kb': 0,
            'size_after_kb': 0
        }
        
        try:
            # Get database size before optimization
            results['size_before_kb'] = self._get_database_size()
            
            # Run VACUUM to reclaim space
            self.db.execute_query("VACUUM")
            results['vacuum_completed'] = True
            self.logger.info("Database VACUUM completed")
            
            # Update statistics
            self.db.execute_query("ANALYZE")
            results['analyze_completed'] = True
            self.logger.info("Database ANALYZE completed")
            
            # Reindex for performance
            self.db.execute_query("REINDEX")
            results['reindex_completed'] = True
            self.logger.info("Database REINDEX completed")
            
            # Get database size after optimization
            results['size_after_kb'] = self._get_database_size()
            
            space_saved = results['size_before_kb'] - results['size_after_kb']
            self.logger.info(f"Database optimization complete. Space saved: {space_saved} KB")
            
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def _get_database_size(self) -> int:
        """Get current database size in KB"""
        try:
            import os
            return os.path.getsize(self.db.db_path) // 1024
        except:
            return 0
    
    def configure_archive_rules(self, table_name: str, rules: Dict[str, Any]):
        """Update archive rules for a specific table"""
        if table_name in self.archive_rules:
            self.archive_rules[table_name].update(rules)
            self.logger.info(f"Updated archive rules for {table_name}: {rules}")
        else:
            self.archive_rules[table_name] = rules
            self.logger.info(f"Created new archive rules for {table_name}: {rules}")
    
    def get_archive_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for archiving based on current data"""
        recommendations = []
        
        for table_name, rules in self.archive_rules.items():
            try:
                # Count records that could be archived
                archive_cutoff = datetime.now() - timedelta(days=rules['archive_after_days'])
                where_clause = self._build_archive_where_clause(table_name, archive_cutoff, rules)
                
                count_query = f"SELECT COUNT(*) as count FROM {table_name} WHERE {where_clause}"
                result = self.db.execute_single(count_query)
                archivable_count = result['count'] if result else 0
                
                if archivable_count > 0:
                    recommendations.append({
                        'table': table_name,
                        'archivable_records': archivable_count,
                        'archive_after_days': rules['archive_after_days'],
                        'estimated_space_saved_kb': archivable_count * 2  # Rough estimate
                    })
                    
            except Exception as e:
                self.logger.error(f"Failed to get recommendations for {table_name}: {e}")
        
        return recommendations
