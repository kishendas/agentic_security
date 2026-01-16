import pandas as pd
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random

class LogAnalyzer:
    """Analyzes security logs for failed logins, suspicious activity, etc."""
    
    def __init__(self):
        self.logs_df = None
        self._load_logs()
    
    def _generate_mock_logs(self) -> pd.DataFrame:
        """Generate realistic mock security logs"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        # Generate timestamps
        timestamps = []
        current = start_time
        while current < end_time:
            timestamps.append(current)
            current += timedelta(minutes=random.randint(1, 30))
        
        users = ['john.doe', 'jane.smith', 'bob.wilson', 'alice.chen', 'admin', 'service_account']
        ips = ['192.168.1.100', '192.168.1.101', '10.0.0.50', '172.16.0.10', '203.0.113.45', '198.51.100.89']
        actions = ['login_success', 'login_failed', 'password_change', 'file_access', 'api_call']
        sources = ['web_app', 'vpn', 'ssh', 'api', 'internal_app']
        
        logs = []
        for ts in timestamps[:500]:  # Limit to 500 log entries
            # Create some patterns
            is_suspicious = random.random() < 0.1
            
            if is_suspicious:
                # Suspicious patterns
                user = random.choice(['unknown_user', 'admin', 'root'])
                action = 'login_failed'
                ip = random.choice(['203.0.113.45', '198.51.100.89'])  # External IPs
                source = random.choice(['ssh', 'vpn'])
            else:
                user = random.choice(users)
                action = random.choice(actions)
                ip = random.choice(ips)
                source = random.choice(sources)
            
            logs.append({
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'user': user,
                'action': action,
                'source': source,
                'ip_address': ip,
                'status': 'success' if 'success' in action else 'failed',
                'details': f"{action} from {source}"
            })
        
        return pd.DataFrame(logs)
    
    def _load_logs(self):
        """Load security logs from CSV or generate mock data"""
        log_file = os.path.join(os.path.dirname(__file__), '../data/security_logs.csv')
        
        if os.path.exists(log_file):
            self.logs_df = pd.read_csv(log_file)
        else:
            self.logs_df = self._generate_mock_logs()
            # Save for future use
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            self.logs_df.to_csv(log_file, index=False)
    
    def get_failed_logins(self, hours: int = 24, user: Optional[str] = None) -> Dict:
        """Get failed login attempts within specified time window"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        df = self.logs_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by time
        recent_logs = df[df['timestamp'] >= cutoff_time]
        
        # Filter failed logins
        failed = recent_logs[recent_logs['action'] == 'login_failed']
        
        if user:
            failed = failed[failed['user'] == user]
        
        # Analyze patterns
        by_user = failed.groupby('user').size().to_dict()
        by_ip = failed.groupby('ip_address').size().to_dict()
        by_source = failed.groupby('source').size().to_dict()
        
        return {
            'total_failed': len(failed),
            'time_window_hours': hours,
            'by_user': dict(sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:10]),
            'by_ip': dict(sorted(by_ip.items(), key=lambda x: x[1], reverse=True)[:10]),
            'by_source': by_source,
            'recent_entries': failed.tail(10).to_dict('records')
        }
    
    def detect_brute_force(self, threshold: int = 5, time_window_minutes: int = 10) -> Dict:
        """Detect potential brute force attacks"""
        df = self.logs_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        failed = df[df['action'] == 'login_failed'].sort_values('timestamp')
        
        alerts = []
        for user in failed['user'].unique():
            user_failed = failed[failed['user'] == user]
            
            for i in range(len(user_failed)):
                current_time = user_failed.iloc[i]['timestamp']
                window_start = current_time - timedelta(minutes=time_window_minutes)
                
                window_attempts = user_failed[
                    (user_failed['timestamp'] >= window_start) & 
                    (user_failed['timestamp'] <= current_time)
                ]
                
                if len(window_attempts) >= threshold:
                    alerts.append({
                        'user': user,
                        'attempts': len(window_attempts),
                        'time_window_minutes': time_window_minutes,
                        'latest_attempt': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'ip_addresses': window_attempts['ip_address'].unique().tolist(),
                        'severity': 'HIGH' if len(window_attempts) > 10 else 'MEDIUM'
                    })
                    break  # One alert per user
        
        return {
            'alerts_found': len(alerts),
            'threshold': threshold,
            'alerts': alerts
        }
    
    def get_user_activity(self, user: str, hours: int = 24) -> Dict:
        """Get all activity for a specific user"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        df = self.logs_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        user_logs = df[
            (df['user'] == user) & 
            (df['timestamp'] >= cutoff_time)
        ]
        
        return {
            'user': user,
            'time_window_hours': hours,
            'total_activities': len(user_logs),
            'by_action': user_logs.groupby('action').size().to_dict(),
            'recent_activities': user_logs.tail(20).to_dict('records')
        }
    
    def search_logs(self, keyword: str, hours: int = 168) -> Dict:
        """Search logs for specific keywords"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        df = self.logs_df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        recent = df[df['timestamp'] >= cutoff_time]
        
        # Search in multiple fields
        matches = recent[
            recent['user'].str.contains(keyword, case=False, na=False) |
            recent['action'].str.contains(keyword, case=False, na=False) |
            recent['details'].str.contains(keyword, case=False, na=False) |
            recent['ip_address'].str.contains(keyword, case=False, na=False)
        ]
        
        return {
            'keyword': keyword,
            'matches_found': len(matches),
            'time_window_hours': hours,
            'results': matches.tail(20).to_dict('records')
        }

log_analyzer = LogAnalyzer()
