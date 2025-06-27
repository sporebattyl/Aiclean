"""
RuleValidator - Handles validation and normalization of ignore rules
Component-based design following TDD principles
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class RuleValidator:
    """
    Validates and normalizes ignore rule text.
    
    This component is responsible for ensuring rule text is valid,
    normalized, and doesn't conflict with existing rules.
    """
    
    # Configuration constants
    MIN_RULE_LENGTH = 1
    MAX_RULE_LENGTH = 200
    FORBIDDEN_PATTERNS = [
        r'^\s*$',  # Empty or whitespace only
        r'^ignore\s*$',  # Just the word "ignore"
        r'[<>{}[\]\\|`~]',  # Special characters that could cause issues
    ]
    
    def __init__(self):
        """Initialize the rule validator."""
        logger.info("RuleValidator initialized")
    
    def validate_rule(self, rule_text: str, existing_rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Validate and normalize a rule text.
        
        Args:
            rule_text: The rule text to validate
            existing_rules: List of existing rules to check for duplicates
            
        Returns:
            dict: Validation result with 'valid', 'normalized', and optional 'error' keys
        """
        try:
            # Basic validation
            if not isinstance(rule_text, str):
                return {
                    'valid': False,
                    'error': 'Rule text must be a string'
                }
            
            # Normalize the text
            normalized = self._normalize_text(rule_text)
            
            # Check if empty after normalization
            if not normalized:
                return {
                    'valid': False,
                    'error': 'Rule text cannot be empty or whitespace only'
                }
            
            # Check length constraints
            if len(normalized) < self.MIN_RULE_LENGTH:
                return {
                    'valid': False,
                    'error': f'Rule text must be at least {self.MIN_RULE_LENGTH} character(s) long'
                }
            
            if len(normalized) > self.MAX_RULE_LENGTH:
                return {
                    'valid': False,
                    'error': f'Rule text cannot exceed {self.MAX_RULE_LENGTH} characters'
                }
            
            # Check forbidden patterns
            for pattern in self.FORBIDDEN_PATTERNS:
                if re.search(pattern, normalized, re.IGNORECASE):
                    return {
                        'valid': False,
                        'error': 'Rule text contains forbidden characters or patterns'
                    }
            
            # Check for duplicates
            if existing_rules:
                duplicate_check = self._check_for_duplicates(normalized, existing_rules)
                if not duplicate_check['valid']:
                    return duplicate_check
            
            # Additional semantic validation
            semantic_check = self._validate_semantics(normalized)
            if not semantic_check['valid']:
                return semantic_check
            
            logger.debug(f"Rule validated successfully: {normalized}")
            return {
                'valid': True,
                'normalized': normalized
            }
            
        except Exception as e:
            logger.error(f"Error validating rule: {e}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize rule text for consistent processing.
        
        Args:
            text: Raw rule text
            
        Returns:
            str: Normalized text
        """
        # Strip whitespace and convert to lowercase
        normalized = text.strip().lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Ensure it starts with "ignore" if it doesn't already
        if normalized and not normalized.startswith('ignore '):
            if normalized.startswith('ignore'):
                # Handle cases like "ignoredirty" -> "ignore dirty"
                normalized = re.sub(r'^ignore([a-z])', r'ignore \1', normalized)
            else:
                # Add "ignore" prefix
                normalized = f'ignore {normalized}'
        
        return normalized
    
    def _check_for_duplicates(self, normalized_text: str, existing_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check if the normalized text duplicates an existing rule.
        
        Args:
            normalized_text: Normalized rule text to check
            existing_rules: List of existing rules
            
        Returns:
            dict: Validation result
        """
        for rule in existing_rules:
            existing_text = rule.get('text', '').lower().strip()
            if existing_text == normalized_text:
                return {
                    'valid': False,
                    'error': f'Duplicate rule: "{normalized_text}" already exists'
                }
        
        return {'valid': True}
    
    def _validate_semantics(self, normalized_text: str) -> Dict[str, Any]:
        """
        Validate the semantic meaning of the rule.
        
        Args:
            normalized_text: Normalized rule text
            
        Returns:
            dict: Validation result
        """
        # Check for meaningful content after "ignore"
        content = normalized_text.replace('ignore ', '', 1).strip()
        
        if not content:
            return {
                'valid': False,
                'error': 'Rule must specify what to ignore (e.g., "ignore dirty dishes")'
            }
        
        # Check for overly generic rules that might ignore everything
        generic_patterns = [
            r'^(everything|all|anything|stuff|things|items)$',
            r'^(clean|cleaning|tasks|task)$',
            r'^(mess|messy|dirty)$'
        ]
        
        for pattern in generic_patterns:
            if re.match(pattern, content, re.IGNORECASE):
                return {
                    'valid': False,
                    'error': f'Rule "{content}" is too generic and might ignore too many tasks'
                }
        
        # Check minimum word count for specificity
        words = content.split()
        if len(words) < 1:
            return {
                'valid': False,
                'error': 'Rule must be more specific about what to ignore'
            }
        
        return {'valid': True}
    
    def suggest_improvements(self, rule_text: str) -> List[str]:
        """
        Suggest improvements for a rule text.
        
        Args:
            rule_text: Rule text to analyze
            
        Returns:
            list: List of improvement suggestions
        """
        suggestions = []
        normalized = self._normalize_text(rule_text)
        
        if not normalized:
            return ["Rule text cannot be empty"]
        
        content = normalized.replace('ignore ', '', 1).strip()
        words = content.split()
        
        # Suggest more specificity
        if len(words) == 1:
            suggestions.append(f"Consider being more specific than just '{content}' (e.g., 'ignore {content} on counter')")
        
        # Suggest common patterns
        common_objects = ['dishes', 'clothes', 'papers', 'books', 'toys']
        if any(obj in content for obj in common_objects):
            suggestions.append("Consider specifying location (e.g., 'on table', 'in sink', 'on floor')")
        
        # Suggest avoiding overly broad terms
        broad_terms = ['mess', 'clutter', 'stuff', 'things']
        if any(term in content for term in broad_terms):
            suggestions.append(f"Consider replacing broad terms like '{content}' with specific items")
        
        return suggestions
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        Get the current validation rules and constraints.
        
        Returns:
            dict: Validation rules and constraints
        """
        return {
            'min_length': self.MIN_RULE_LENGTH,
            'max_length': self.MAX_RULE_LENGTH,
            'forbidden_patterns': self.FORBIDDEN_PATTERNS,
            'auto_prefix': 'ignore',
            'normalization': {
                'lowercase': True,
                'trim_whitespace': True,
                'collapse_spaces': True
            }
        }
