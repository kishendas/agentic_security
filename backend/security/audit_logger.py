import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from config import config

class AuditLogger:
    """Comprehensive audit logging for all AI assistant actions"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or config.AUDIT_LOG_FILE
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Create log file if it doesn't exist"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                pass
    
    def log_interaction(
        self,
        user: str,
        role: str,
        prompt: str,
        action: str,
        tool_used: Optional[str] = None,
        result_summary: Optional[str] = None,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a user interaction with the AI assistant"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user,
            "role": role,
            "prompt": prompt[:200],  # Truncate for privacy
            "action": action,
            "tool_used": tool_used,
            "result_summary": result_summary[:100] if result_summary else None,
            "status": status,
            "metadata": metadata or {}
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_security_event(
        self,
        user: str,
        event_type: str,
        details: str,
        severity: str = "medium"
    ):
        """Log security-related events"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "security",
            "user": user,
            "security_event": event_type,
            "details": details,
            "severity": severity
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def log_tool_call(
        self,
        user: str,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Optional[str] = None,
        execution_time: Optional[float] = None
    ):
        """Log tool/API calls made by the agent"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "tool_call",
            "user": user,
            "tool_name": tool_name,
            "parameters": parameters,
            "result_preview": result[:100] if result else None,
            "execution_time_ms": execution_time
        }
        
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_recent_logs(self, limit: int = 50) -> list:
        """Retrieve recent audit logs"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                recent = lines[-limit:] if len(lines) > limit else lines
                return [json.loads(line) for line in recent]
        except Exception as e:
            return []

audit_logger = AuditLogger()
