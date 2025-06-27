"""
IgnoreRulesManager - Main orchestrator for the ignore rules system
Component-based design following TDD principles
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
try:
    from .rule_validator import RuleValidator
    from .rule_matcher import RuleMatcher
    from .rule_persistence import RulePersistence
except ImportError:
    # Fallback for standalone execution
    from rule_validator import RuleValidator
    from rule_matcher import RuleMatcher
    from rule_persistence import RulePersistence

logger = logging.getLogger(__name__)


class IgnoreRulesManager:
    """
    Main ignore rules manager that orchestrates rule validation, matching, and persistence.
    
    This component follows the Single Responsibility Principle and coordinates
    between the validator, matcher, and persistence components.
    """
    
    def __init__(self, zone_name: str):
        """
        Initialize the ignore rules manager for a specific zone.
        
        Args:
            zone_name: Name of the zone this manager handles
        """
        self.zone_name = zone_name
        self.rules: List[Dict[str, Any]] = []
        
        # Initialize components
        self.validator = RuleValidator()
        self.matcher = RuleMatcher()
        self.persistence = RulePersistence(zone_name)
        
        logger.info(f"IgnoreRulesManager initialized for zone: {zone_name}")
    
    def add_rule(self, rule_text: str) -> bool:
        """
        Add a new ignore rule after validation.
        
        Args:
            rule_text: The rule text to add
            
        Returns:
            bool: True if rule was added successfully, False otherwise
        """
        try:
            # Validate the rule
            validation_result = self.validator.validate_rule(rule_text, self.rules)
            
            if not validation_result['valid']:
                logger.warning(f"Invalid rule rejected: {validation_result.get('error', 'Unknown error')}")
                return False
            
            # Create the rule object
            rule = {
                'id': str(uuid.uuid4()),
                'text': validation_result['normalized'],
                'created_at': datetime.now().isoformat(),
                'zone': self.zone_name
            }
            
            # Add to rules list
            self.rules.append(rule)
            
            # Persist the rules
            if self.persistence.save_rules(self.rules):
                logger.info(f"Added ignore rule for zone {self.zone_name}: {rule['text']}")
                return True
            else:
                # Remove from list if persistence failed
                self.rules.remove(rule)
                logger.error(f"Failed to persist ignore rule for zone {self.zone_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding ignore rule for zone {self.zone_name}: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove an ignore rule by ID.
        
        Args:
            rule_id: ID of the rule to remove
            
        Returns:
            bool: True if rule was removed successfully, False otherwise
        """
        try:
            # Find the rule
            rule_to_remove = None
            for rule in self.rules:
                if rule['id'] == rule_id:
                    rule_to_remove = rule
                    break
            
            if rule_to_remove is None:
                logger.warning(f"Rule not found for removal: {rule_id}")
                return False
            
            # Remove from list
            self.rules.remove(rule_to_remove)
            
            # Persist the updated rules
            if self.persistence.save_rules(self.rules):
                logger.info(f"Removed ignore rule for zone {self.zone_name}: {rule_to_remove['text']}")
                return True
            else:
                # Add back to list if persistence failed
                self.rules.append(rule_to_remove)
                logger.error(f"Failed to persist rule removal for zone {self.zone_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing ignore rule for zone {self.zone_name}: {e}")
            return False
    
    def should_ignore_task(self, task_description: str) -> bool:
        """
        Check if a task should be ignored based on current rules.
        
        Args:
            task_description: Description of the task to check
            
        Returns:
            bool: True if task should be ignored, False otherwise
        """
        try:
            if not self.rules:
                return False
            
            result = self.matcher.matches_any_rule(task_description, self.rules)
            
            if result:
                logger.debug(f"Task ignored for zone {self.zone_name}: {task_description}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking ignore rules for zone {self.zone_name}: {e}")
            return False
    
    def load_rules(self) -> bool:
        """
        Load rules from persistence.
        
        Returns:
            bool: True if rules were loaded successfully, False otherwise
        """
        try:
            loaded_rules = self.persistence.load_rules()
            self.rules = loaded_rules
            logger.info(f"Loaded {len(self.rules)} ignore rules for zone {self.zone_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading ignore rules for zone {self.zone_name}: {e}")
            return False
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Get all current rules.
        
        Returns:
            list: List of rule dictionaries
        """
        return self.rules.copy()
    
    def get_rules_count(self) -> int:
        """
        Get the number of active rules.
        
        Returns:
            int: Number of rules
        """
        return len(self.rules)
    
    def clear_all_rules(self) -> bool:
        """
        Remove all ignore rules.
        
        Returns:
            bool: True if all rules were cleared successfully, False otherwise
        """
        try:
            self.rules = []
            
            if self.persistence.save_rules(self.rules):
                logger.info(f"Cleared all ignore rules for zone {self.zone_name}")
                return True
            else:
                logger.error(f"Failed to persist rule clearing for zone {self.zone_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error clearing ignore rules for zone {self.zone_name}: {e}")
            return False
    
    def update_rule(self, rule_id: str, new_text: str) -> bool:
        """
        Update an existing rule's text.
        
        Args:
            rule_id: ID of the rule to update
            new_text: New text for the rule
            
        Returns:
            bool: True if rule was updated successfully, False otherwise
        """
        try:
            # Find the rule
            rule_to_update = None
            for rule in self.rules:
                if rule['id'] == rule_id:
                    rule_to_update = rule
                    break
            
            if rule_to_update is None:
                logger.warning(f"Rule not found for update: {rule_id}")
                return False
            
            # Validate the new text
            validation_result = self.validator.validate_rule(new_text, [r for r in self.rules if r['id'] != rule_id])
            
            if not validation_result['valid']:
                logger.warning(f"Invalid rule update rejected: {validation_result.get('error', 'Unknown error')}")
                return False
            
            # Store old text for rollback
            old_text = rule_to_update['text']
            
            # Update the rule
            rule_to_update['text'] = validation_result['normalized']
            rule_to_update['updated_at'] = datetime.now().isoformat()
            
            # Persist the updated rules
            if self.persistence.save_rules(self.rules):
                logger.info(f"Updated ignore rule for zone {self.zone_name}: {old_text} -> {rule_to_update['text']}")
                return True
            else:
                # Rollback if persistence failed
                rule_to_update['text'] = old_text
                if 'updated_at' in rule_to_update:
                    del rule_to_update['updated_at']
                logger.error(f"Failed to persist rule update for zone {self.zone_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating ignore rule for zone {self.zone_name}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the ignore rules manager.
        
        Returns:
            dict: Status information including rule count and zone
        """
        return {
            'zone_name': self.zone_name,
            'rules_count': len(self.rules),
            'rules': self.get_rules(),
            'persistence_configured': self.persistence.is_configured()
        }
