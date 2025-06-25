"""
Database Maintenance - Automated maintenance tasks and health checks
"""
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .database import DatabaseManager


class MaintenanceScheduler:
    """Handles automated database maintenance tasks"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
        self.running = False
        
        # Maintenance configuration
        self.config = {
            'auto_backup': {
                'enabled': True,
                'frequency': 'daily',
                'time': '02:00',
                'retention_days': 30
            },
            'auto_archive': {
                'enabled': True,
                'frequency': 'weekly',
                'day': 'sunday',
                'time': '03:00'
            },
            'performance_check': {
                'enabled': True,
                'frequency': 'daily',
                'time': '01:00'
            },
            'cleanup': {
                'enabled': True,
                'frequency': 'monthly',
                'day': 1,
                'time': '04:00'
            }
        }
        
        self.logger.info("Maintenance scheduler initialized")
    
    def start_scheduler(self):
        """Start the maintenance scheduler"""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self._schedule_tasks()
        self.running = True
        self.logger.info("Maintenance scheduler started")
        
        # Run scheduler in background
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the maintenance scheduler"""
        self.running = False
        schedule.clear()
        self.logger.info("Maintenance scheduler stopped")
    
    def _schedule_tasks(self):
        """Schedule all maintenance tasks"""
        # Auto backup
        if self.config['auto_backup']['enabled']:
            schedule.every().day.at(self.config['auto_backup']['time']).do(
                self._run_auto_backup
            )
        
        # Auto archive
        if self.config['auto_archive']['enabled']:
            getattr(schedule.every(), self.config['auto_archive']['day']).at(
                self.config['auto_archive']['time']
            ).do(self._run_auto_archive)
        
        # Performance check
        if self.config['performance_check']['enabled']:
            schedule.every().day.at(self.config['performance_check']['time']).do(
                self._run_performance_check
            )
        
        # Monthly cleanup
        if self.config['cleanup']['enabled']:
            schedule.every().month.do(self._run_cleanup)
        
        self.logger.info("Maintenance tasks scheduled")
    
    def _run_auto_backup(self):
        """Run automatic backup"""
        try:
            self.logger.info("Starting automatic backup")
            
            # Create backup
            backup_path = self.db.create_backup(
                backup_name=f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                compress=True
            )
            
            # Cleanup old backups
            removed_count = self.db.backup_manager.cleanup_old_backups(
                self.config['auto_backup']['retention_days']
            )
            
            self.logger.info(f"Auto backup completed: {backup_path}, removed {removed_count} old backups")
            
        except Exception as e:
            self.logger.error(f"Auto backup failed: {e}")
    
    def _run_auto_archive(self):
        """Run automatic data archiving"""
        try:
            self.logger.info("Starting automatic archiving")
            
            result = self.db.archive_old_data()
            
            self.logger.info(
                f"Auto archive completed: {result['archived_records']} archived, "
                f"{result['deleted_records']} deleted"
            )
            
        except Exception as e:
            self.logger.error(f"Auto archive failed: {e}")
    
    def _run_performance_check(self):
        """Run performance health check"""
        try:
            self.logger.info("Starting performance check")
            
            alerts = self.db.check_performance_alerts()
            
            if alerts:
                self.logger.warning(f"Performance alerts detected: {len(alerts)} issues")
                for alert in alerts:
                    self.logger.warning(f"Alert: {alert['type']} - {alert['message']}")
            else:
                self.logger.info("Performance check passed - no issues detected")
                
        except Exception as e:
            self.logger.error(f"Performance check failed: {e}")
    
    def _run_cleanup(self):
        """Run monthly cleanup tasks"""
        try:
            self.logger.info("Starting monthly cleanup")
            
            # Optimize database
            optimization_result = self.db.performance_monitor.optimize_database_settings()
            
            # Run vacuum and analyze
            vacuum_result = self.db.archive_manager.optimize_database()
            
            self.logger.info(f"Monthly cleanup completed: {optimization_result}, {vacuum_result}")
            
        except Exception as e:
            self.logger.error(f"Monthly cleanup failed: {e}")
    
    def run_manual_maintenance(self, tasks: List[str] = None) -> Dict[str, Any]:
        """Run maintenance tasks manually"""
        if tasks is None:
            tasks = ['backup', 'archive', 'performance_check', 'cleanup']
        
        results = {}
        
        for task in tasks:
            try:
                if task == 'backup':
                    self._run_auto_backup()
                    results['backup'] = 'success'
                elif task == 'archive':
                    self._run_auto_archive()
                    results['archive'] = 'success'
                elif task == 'performance_check':
                    self._run_performance_check()
                    results['performance_check'] = 'success'
                elif task == 'cleanup':
                    self._run_cleanup()
                    results['cleanup'] = 'success'
                else:
                    results[task] = f'unknown_task'
                    
            except Exception as e:
                results[task] = f'failed: {e}'
        
        return results
    
    def get_maintenance_status(self) -> Dict[str, Any]:
        """Get current maintenance status"""
        return {
            'scheduler_running': self.running,
            'configuration': self.config,
            'next_runs': self._get_next_scheduled_runs(),
            'last_maintenance_check': datetime.now().isoformat()
        }
    
    def _get_next_scheduled_runs(self) -> Dict[str, str]:
        """Get next scheduled run times"""
        next_runs = {}
        
        for job in schedule.jobs:
            job_name = job.job_func.__name__.replace('_run_', '')
            next_run = job.next_run
            if next_run:
                next_runs[job_name] = next_run.isoformat()
        
        return next_runs
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update maintenance configuration"""
        self.config.update(new_config)
        
        # Reschedule tasks if scheduler is running
        if self.running:
            schedule.clear()
            self._schedule_tasks()
        
        self.logger.info(f"Maintenance configuration updated: {new_config}")


class HealthChecker:
    """Performs comprehensive database health checks"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'recommendations': [],
            'critical_issues': []
        }
        
        # Database integrity check
        health_report['checks']['integrity'] = self._check_database_integrity()
        
        # Performance check
        health_report['checks']['performance'] = self._check_performance()
        
        # Storage check
        health_report['checks']['storage'] = self._check_storage()
        
        # Backup check
        health_report['checks']['backup'] = self._check_backup_status()
        
        # Archive check
        health_report['checks']['archive'] = self._check_archive_status()
        
        # Determine overall status
        health_report['overall_status'] = self._determine_overall_status(health_report['checks'])
        
        # Generate recommendations
        health_report['recommendations'] = self._generate_recommendations(health_report['checks'])
        
        return health_report
    
    def _check_database_integrity(self) -> Dict[str, Any]:
        """Check database integrity"""
        try:
            # Run integrity check
            result = self.db.execute_single("PRAGMA integrity_check")
            
            return {
                'status': 'pass' if result and result.get('integrity_check') == 'ok' else 'fail',
                'details': result.get('integrity_check', 'Unknown') if result else 'No result'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'details': str(e)
            }
    
    def _check_performance(self) -> Dict[str, Any]:
        """Check performance metrics"""
        try:
            alerts = self.db.check_performance_alerts()
            
            return {
                'status': 'pass' if not alerts else 'warning',
                'alert_count': len(alerts),
                'alerts': alerts
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'details': str(e)
            }
    
    def _check_storage(self) -> Dict[str, Any]:
        """Check storage usage"""
        try:
            stats = self.db.get_archive_statistics()
            
            total_size_mb = (stats['total_main_size'] + stats['total_archive_size']) / 1024
            
            return {
                'status': 'pass' if total_size_mb < 1000 else 'warning',  # 1GB threshold
                'total_size_mb': total_size_mb,
                'main_size_mb': stats['total_main_size'] / 1024,
                'archive_size_mb': stats['total_archive_size'] / 1024
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'details': str(e)
            }
    
    def _check_backup_status(self) -> Dict[str, Any]:
        """Check backup status"""
        try:
            backups = self.db.list_backups()
            
            if not backups:
                return {
                    'status': 'warning',
                    'details': 'No backups found'
                }
            
            latest_backup = backups[0]
            backup_age = datetime.now() - datetime.fromisoformat(latest_backup['created_at'])
            
            return {
                'status': 'pass' if backup_age.days < 2 else 'warning',
                'latest_backup_age_days': backup_age.days,
                'total_backups': len(backups)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'details': str(e)
            }
    
    def _check_archive_status(self) -> Dict[str, Any]:
        """Check archive status"""
        try:
            recommendations = self.db.archive_manager.get_archive_recommendations()
            
            total_archivable = sum(r['archivable_records'] for r in recommendations)
            
            return {
                'status': 'pass' if total_archivable < 10000 else 'warning',
                'archivable_records': total_archivable,
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'details': str(e)
            }
    
    def _determine_overall_status(self, checks: Dict[str, Any]) -> str:
        """Determine overall health status"""
        statuses = [check.get('status', 'unknown') for check in checks.values()]
        
        if 'error' in statuses:
            return 'unhealthy'
        elif 'fail' in statuses:
            return 'critical'
        elif 'warning' in statuses:
            return 'warning'
        else:
            return 'healthy'
    
    def _generate_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on check results"""
        recommendations = []
        
        # Storage recommendations
        storage = checks.get('storage', {})
        if storage.get('status') == 'warning':
            recommendations.append("Consider archiving old data to reduce database size")
        
        # Backup recommendations
        backup = checks.get('backup', {})
        if backup.get('status') == 'warning':
            recommendations.append("Create a recent backup of the database")
        
        # Performance recommendations
        performance = checks.get('performance', {})
        if performance.get('alert_count', 0) > 0:
            recommendations.append("Review performance alerts and optimize queries")
        
        # Archive recommendations
        archive = checks.get('archive', {})
        if archive.get('archivable_records', 0) > 5000:
            recommendations.append("Run data archiving to improve performance")
        
        return recommendations
