"""
RuleMatcher - Handles matching task descriptions against ignore rules
Component-based design following TDD principles
"""

import logging
import re
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class RuleMatcher:
    """
    Matches task descriptions against ignore rules.
    
    This component is responsible for determining if a task description
    matches any of the configured ignore rules using various matching strategies.
    """
    
    def __init__(self):
        """Initialize the rule matcher."""
        self.similarity_threshold = 0.8  # For fuzzy matching
        logger.info("RuleMatcher initialized")
    
    def matches_any_rule(self, task_description: str, rules: List[Dict[str, Any]]) -> bool:
        """
        Check if a task description matches any of the ignore rules.
        
        Args:
            task_description: Description of the task to check
            rules: List of ignore rules to match against
            
        Returns:
            bool: True if task matches any rule, False otherwise
        """
        try:
            if not task_description or not rules:
                return False
            
            # Normalize the task description
            normalized_task = self._normalize_text(task_description)
            
            for rule in rules:
                rule_text = rule.get('text', '')
                if self._matches_rule(normalized_task, rule_text):
                    logger.debug(f"Task '{task_description}' matches rule '{rule_text}'")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error matching rules: {e}")
            return False
    
    def find_matching_rules(self, task_description: str, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find all rules that match a task description.
        
        Args:
            task_description: Description of the task to check
            rules: List of ignore rules to match against
            
        Returns:
            list: List of matching rules with match details
        """
        try:
            matching_rules = []
            
            if not task_description or not rules:
                return matching_rules
            
            normalized_task = self._normalize_text(task_description)
            
            for rule in rules:
                rule_text = rule.get('text', '')
                match_details = self._get_match_details(normalized_task, rule_text)
                
                if match_details['matches']:
                    matching_rule = rule.copy()
                    matching_rule['match_details'] = match_details
                    matching_rules.append(matching_rule)
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"Error finding matching rules: {e}")
            return []
    
    def _matches_rule(self, normalized_task: str, rule_text: str) -> bool:
        """
        Check if a normalized task matches a specific rule.
        
        Args:
            normalized_task: Normalized task description
            rule_text: Rule text to match against
            
        Returns:
            bool: True if task matches rule, False otherwise
        """
        if not rule_text:
            return False
        
        # Normalize the rule text
        normalized_rule = self._normalize_text(rule_text)
        
        # Remove "ignore" prefix from rule for matching
        rule_content = normalized_rule.replace('ignore ', '', 1).strip()
        
        if not rule_content:
            return False
        
        # Try different matching strategies
        return (
            self._exact_match(normalized_task, rule_content) or
            self._substring_match(normalized_task, rule_content) or
            self._word_match(normalized_task, rule_content) or
            self._fuzzy_match(normalized_task, rule_content)
        )
    
    def _get_match_details(self, normalized_task: str, rule_text: str) -> Dict[str, Any]:
        """
        Get detailed information about how a task matches a rule.
        
        Args:
            normalized_task: Normalized task description
            rule_text: Rule text to match against
            
        Returns:
            dict: Match details including type and confidence
        """
        if not rule_text:
            return {'matches': False}
        
        normalized_rule = self._normalize_text(rule_text)
        rule_content = normalized_rule.replace('ignore ', '', 1).strip()
        
        if not rule_content:
            return {'matches': False}
        
        # Check each matching strategy
        if self._exact_match(normalized_task, rule_content):
            return {
                'matches': True,
                'type': 'exact',
                'confidence': 1.0,
                'rule_content': rule_content
            }
        
        if self._substring_match(normalized_task, rule_content):
            return {
                'matches': True,
                'type': 'substring',
                'confidence': 0.9,
                'rule_content': rule_content
            }
        
        if self._word_match(normalized_task, rule_content):
            return {
                'matches': True,
                'type': 'word',
                'confidence': 0.8,
                'rule_content': rule_content
            }
        
        similarity = self._calculate_similarity(normalized_task, rule_content)
        if similarity >= self.similarity_threshold:
            return {
                'matches': True,
                'type': 'fuzzy',
                'confidence': similarity,
                'rule_content': rule_content
            }
        
        return {'matches': False}
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent matching.
        
        Args:
            text: Text to normalize
            
        Returns:
            str: Normalized text
        """
        # Convert to lowercase and strip whitespace
        normalized = text.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common task prefixes
        task_prefixes = ['clean', 'organize', 'tidy', 'put away', 'pick up', 'wipe', 'wash']
        for prefix in task_prefixes:
            pattern = rf'^{re.escape(prefix)}\s+'
            normalized = re.sub(pattern, '', normalized)
        
        return normalized
    
    def _exact_match(self, task: str, rule_content: str) -> bool:
        """Check for exact string match."""
        return task == rule_content
    
    def _substring_match(self, task: str, rule_content: str) -> bool:
        """Check if rule content is a substring of the task."""
        return rule_content in task
    
    def _word_match(self, task: str, rule_content: str) -> bool:
        """Check if all words in rule content appear in the task."""
        rule_words = set(rule_content.split())
        task_words = set(task.split())
        
        # All rule words must be present in task
        return rule_words.issubset(task_words)
    
    def _fuzzy_match(self, task: str, rule_content: str) -> bool:
        """Check for fuzzy string similarity match."""
        similarity = self._calculate_similarity(task, rule_content)
        return similarity >= self.similarity_threshold
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two strings.
        
        Args:
            text1: First string
            text2: Second string
            
        Returns:
            float: Similarity score between 0 and 1
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def set_similarity_threshold(self, threshold: float) -> None:
        """
        Set the similarity threshold for fuzzy matching.
        
        Args:
            threshold: Similarity threshold between 0 and 1
        """
        if 0 <= threshold <= 1:
            self.similarity_threshold = threshold
            logger.info(f"Similarity threshold set to {threshold}")
        else:
            logger.warning(f"Invalid similarity threshold: {threshold}. Must be between 0 and 1")
    
    def get_similarity_threshold(self) -> float:
        """
        Get the current similarity threshold.
        
        Returns:
            float: Current similarity threshold
        """
        return self.similarity_threshold
    
    def test_match(self, task_description: str, rule_text: str) -> Dict[str, Any]:
        """
        Test how a specific task matches against a specific rule.
        
        Args:
            task_description: Task description to test
            rule_text: Rule text to test against
            
        Returns:
            dict: Detailed match results for testing/debugging
        """
        normalized_task = self._normalize_text(task_description)
        normalized_rule = self._normalize_text(rule_text)
        rule_content = normalized_rule.replace('ignore ', '', 1).strip()
        
        return {
            'original_task': task_description,
            'normalized_task': normalized_task,
            'original_rule': rule_text,
            'normalized_rule': normalized_rule,
            'rule_content': rule_content,
            'exact_match': self._exact_match(normalized_task, rule_content),
            'substring_match': self._substring_match(normalized_task, rule_content),
            'word_match': self._word_match(normalized_task, rule_content),
            'fuzzy_similarity': self._calculate_similarity(normalized_task, rule_content),
            'fuzzy_match': self._fuzzy_match(normalized_task, rule_content),
            'overall_match': self._matches_rule(normalized_task, rule_text)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the rule matcher.
        
        Returns:
            dict: Status information including configuration
        """
        return {
            'similarity_threshold': self.similarity_threshold,
            'matching_strategies': ['exact', 'substring', 'word', 'fuzzy'],
            'normalization_enabled': True
        }
