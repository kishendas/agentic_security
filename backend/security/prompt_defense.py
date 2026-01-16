import re
from typing import Tuple

class PromptInjectionDefense:
    """Detects and blocks prompt injection attacks"""
    
    def __init__(self):
        # Patterns that indicate prompt injection attempts
        self.injection_patterns = [
            r"ignore (previous|all|above|prior) (instructions|prompts|rules)",
            r"disregard (previous|all|above|prior) (instructions|prompts|rules)",
            r"forget (previous|all|above|prior) (instructions|prompts|rules)",
            r"you are now|from now on you are",
            r"new (instructions|rules|system prompt)",
            r"system:\s*you are",
            r"admin mode|developer mode|god mode",
            r"</system>|<\|im_end\|>|<\|endoftext\|>",
            r"reveal your (prompt|instructions|system message)",
            r"what are your (instructions|rules|guidelines)",
            r"print (your|the) (prompt|instructions|system)",
            r"sudo |root access|bypass",
        ]
        
        self.combined_pattern = re.compile(
            "|".join(self.injection_patterns),
            re.IGNORECASE
        )
        
    def is_malicious(self, user_input: str) -> Tuple[bool, str]:
        """
        Check if input contains prompt injection attempts
        
        Returns:
            Tuple of (is_malicious: bool, reason: str)
        """
        if not user_input or len(user_input.strip()) == 0:
            return False, ""
        
        # Check for patterns
        match = self.combined_pattern.search(user_input)
        if match:
            return True, f"Potential prompt injection detected: '{match.group()}'"
        
        # Check for excessive special characters (potential encoding attacks)
        special_char_ratio = sum(1 for c in user_input if not c.isalnum() and not c.isspace()) / len(user_input)
        if special_char_ratio > 0.3:
            return True, "Excessive special characters detected"
        
        # Check for suspiciously long input
        if len(user_input) > 5000:
            return True, "Input exceeds maximum length"
        
        return False, ""
    
    def sanitize_input(self, user_input: str) -> str:
        """Basic input sanitization"""
        # Remove potential command injections
        sanitized = user_input.strip()
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        return sanitized

# Global instance
prompt_defense = PromptInjectionDefense()
