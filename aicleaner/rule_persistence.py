"""
RulePersistence - Handles persistence of ignore rules to storage
Component-based design following TDD principles
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class RulePersistence:
    """
    Handles persistence of ignore rules to file storage.
    
    This component is responsible for saving and loading ignore rules
    to/from persistent storage with proper error handling and atomic operations.
    """
    
    def __init__(self, zone_name: str, data_dir: str = '/data'):
        """
        Initialize the rule persistence handler.
        
        Args:
            zone_name: Name of the zone for file naming
            data_dir: Directory to store rule files
        """
        self.zone_name = zone_name
        self.data_dir = Path(data_dir)
        self.rules_file = self.data_dir / f'ignore_rules_{zone_name}.json'
        self.backup_file = self.data_dir / f'ignore_rules_{zone_name}.backup.json'
        
        # Ensure data directory exists
        self._ensure_data_directory()
        
        logger.info(f"RulePersistence initialized for zone: {zone_name}")
    
    def save_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """
        Save rules to persistent storage using atomic write operation.
        
        Args:
            rules: List of rule dictionaries to save
            
        Returns:
            bool: True if rules were saved successfully, False otherwise
        """
        try:
            # Create backup of existing file if it exists
            if self.rules_file.exists():
                self._create_backup()
            
            # Use atomic write (write to temp file, then rename)
            temp_file = self.rules_file.with_suffix('.tmp')
            
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.rename(self.rules_file)
            
            logger.info(f"Saved {len(rules)} ignore rules for zone {self.zone_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving ignore rules for zone {self.zone_name}: {e}")
            
            # Clean up temp file if it exists
            temp_file = self.rules_file.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            
            return False
    
    def load_rules(self) -> List[Dict[str, Any]]:
        """
        Load rules from persistent storage.
        
        Returns:
            list: List of rule dictionaries, empty list if no rules or error
        """
        try:
            if not self.rules_file.exists():
                logger.info(f"No ignore rules file found for zone {self.zone_name}")
                return []
            
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            # Validate loaded data
            if not isinstance(rules, list):
                logger.error(f"Invalid rules file format for zone {self.zone_name}: expected list")
                return self._try_load_backup()
            
            # Validate each rule
            valid_rules = []
            for rule in rules:
                if self._validate_rule_structure(rule):
                    valid_rules.append(rule)
                else:
                    logger.warning(f"Skipping invalid rule in zone {self.zone_name}: {rule}")
            
            logger.info(f"Loaded {len(valid_rules)} ignore rules for zone {self.zone_name}")
            return valid_rules
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error loading rules for zone {self.zone_name}: {e}")
            return self._try_load_backup()
        
        except Exception as e:
            logger.error(f"Error loading ignore rules for zone {self.zone_name}: {e}")
            return []
    
    def _ensure_data_directory(self) -> None:
        """Ensure the data directory exists."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating data directory {self.data_dir}: {e}")
    
    def _create_backup(self) -> None:
        """Create a backup of the current rules file."""
        try:
            if self.rules_file.exists():
                import shutil
                shutil.copy2(self.rules_file, self.backup_file)
                logger.debug(f"Created backup for zone {self.zone_name}")
        except Exception as e:
            logger.warning(f"Error creating backup for zone {self.zone_name}: {e}")
    
    def _try_load_backup(self) -> List[Dict[str, Any]]:
        """Try to load rules from backup file."""
        try:
            if not self.backup_file.exists():
                return []
            
            with open(self.backup_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            if isinstance(rules, list):
                logger.info(f"Loaded {len(rules)} rules from backup for zone {self.zone_name}")
                return rules
            
        except Exception as e:
            logger.error(f"Error loading backup rules for zone {self.zone_name}: {e}")
        
        return []
    
    def _validate_rule_structure(self, rule: Any) -> bool:
        """
        Validate that a rule has the expected structure.
        
        Args:
            rule: Rule object to validate
            
        Returns:
            bool: True if rule structure is valid, False otherwise
        """
        if not isinstance(rule, dict):
            return False
        
        required_fields = ['id', 'text', 'created_at']
        for field in required_fields:
            if field not in rule:
                return False
            if not isinstance(rule[field], str):
                return False
        
        return True
    
    def delete_rules_file(self) -> bool:
        """
        Delete the rules file (for cleanup/reset).
        
        Returns:
            bool: True if file was deleted or didn't exist, False on error
        """
        try:
            if self.rules_file.exists():
                self.rules_file.unlink()
                logger.info(f"Deleted rules file for zone {self.zone_name}")
            
            if self.backup_file.exists():
                self.backup_file.unlink()
                logger.info(f"Deleted backup file for zone {self.zone_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting rules file for zone {self.zone_name}: {e}")
            return False
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        Get information about the rules file.
        
        Returns:
            dict: File information including size, modification time, etc.
        """
        info = {
            'zone_name': self.zone_name,
            'rules_file': str(self.rules_file),
            'backup_file': str(self.backup_file),
            'rules_file_exists': self.rules_file.exists(),
            'backup_file_exists': self.backup_file.exists()
        }
        
        try:
            if self.rules_file.exists():
                stat = self.rules_file.stat()
                info.update({
                    'file_size': stat.st_size,
                    'modified_time': stat.st_mtime,
                    'readable': os.access(self.rules_file, os.R_OK),
                    'writable': os.access(self.rules_file, os.W_OK)
                })
        except Exception as e:
            info['file_error'] = str(e)
        
        return info
    
    def is_configured(self) -> bool:
        """
        Check if persistence is properly configured.
        
        Returns:
            bool: True if persistence is configured and accessible
        """
        try:
            # Check if data directory is accessible
            if not self.data_dir.exists():
                return False
            
            # Check if we can write to the directory
            test_file = self.data_dir / f'test_write_{self.zone_name}.tmp'
            try:
                test_file.write_text('test')
                test_file.unlink()
                return True
            except:
                return False
                
        except Exception:
            return False
    
    def export_rules(self, export_path: str, rules: List[Dict[str, Any]]) -> bool:
        """
        Export rules to a specified file path.
        
        Args:
            export_path: Path to export the rules to
            rules: Rules to export
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'zone_name': self.zone_name,
                'export_timestamp': json.dumps(datetime.now().isoformat()),
                'rules_count': len(rules),
                'rules': rules
            }
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(rules)} rules for zone {self.zone_name} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting rules for zone {self.zone_name}: {e}")
            return False
    
    def import_rules(self, import_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Import rules from a specified file path.
        
        Args:
            import_path: Path to import the rules from
            
        Returns:
            list: Imported rules, or None if import failed
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.error(f"Import file not found: {import_path}")
                return None
            
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if isinstance(import_data, dict) and 'rules' in import_data:
                rules = import_data['rules']
            elif isinstance(import_data, list):
                rules = import_data
            else:
                logger.error(f"Invalid import file format: {import_path}")
                return None
            
            # Validate imported rules
            valid_rules = []
            for rule in rules:
                if self._validate_rule_structure(rule):
                    valid_rules.append(rule)
            
            logger.info(f"Imported {len(valid_rules)} rules for zone {self.zone_name} from {import_path}")
            return valid_rules
            
        except Exception as e:
            logger.error(f"Error importing rules for zone {self.zone_name}: {e}")
            return None
