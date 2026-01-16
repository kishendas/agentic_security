import json
import os
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class KnowledgeBase:
    """RAG-based knowledge base for security policies and playbooks"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.documents = []
        self.embeddings = None
        self.index = None
        self._load_documents()
        self._build_index()
    
    def _load_documents(self):
        """Load security policies and playbooks"""
        # Default security knowledge
        self.documents = [
            {
                "id": "phishing_policy",
                "title": "Phishing Email Response Policy",
                "content": "When you receive a suspected phishing email: 1) Do NOT click any links or download attachments. 2) Do NOT reply to the sender. 3) Forward the email to security@company.com with subject 'PHISHING REPORT'. 4) Delete the email from your inbox. 5) Report to your manager if you clicked any links. 6) Change your password immediately if you entered credentials. The Security team will investigate within 1 hour and notify affected users.",
                "category": "incident_response",
                "tags": ["phishing", "email", "social_engineering"]
            },
            {
                "id": "data_breach_playbook",
                "title": "Data Breach Response Playbook",
                "content": "Data breach response steps: 1) IMMEDIATELY isolate affected systems - disconnect from network. 2) Contact Security Lead (security@company.com, phone: ext 5555) within 15 minutes. 3) DO NOT shut down systems - preserve evidence. 4) Document timeline and affected data. 5) Security team will: assess scope, contain breach, analyze logs, notify stakeholders. 6) Legal and PR teams engaged for external communications. 7) Post-incident review within 48 hours.",
                "category": "incident_response",
                "tags": ["breach", "data_loss", "incident"]
            },
            {
                "id": "failed_login_policy",
                "title": "Failed Login Investigation",
                "content": "Investigating failed login attempts: 1) Check if attempts are distributed or from single IP. 2) Verify if legitimate user forgot password. 3) More than 5 failed attempts in 10 minutes triggers account lock. 4) Check for credential stuffing patterns (same username, many IPs). 5) Brute force attacks: block IP immediately, alert Security team. 6) Review authentication logs for anomalies. 7) Enable MFA for affected accounts.",
                "category": "security_monitoring",
                "tags": ["authentication", "failed_login", "monitoring"]
            },
            {
                "id": "production_outage_security",
                "title": "Security-Related Production Outage",
                "content": "Escalation for security-caused production outage: 1) Page on-call Security Engineer immediately (PagerDuty). 2) Simultaneously alert DevOps lead and CTO. 3) Initiate incident bridge call within 5 minutes. 4) Assess if attack is ongoing - if yes, enable DDoS protection and block malicious IPs. 5) If breach detected, follow data breach playbook. 6) Coordinate with Engineering for system restoration. 7) All hands on deck - Senior leadership notified within 30 minutes. 8) Customer communication via Status page.",
                "category": "escalation",
                "tags": ["outage", "escalation", "production"]
            },
            {
                "id": "password_policy",
                "title": "Password and Credential Policy",
                "content": "Password requirements: Minimum 12 characters, including uppercase, lowercase, number, and special character. Passwords expire every 90 days. Cannot reuse last 5 passwords. MFA required for all production systems. Shared credentials are prohibited. Use password manager (1Password). Service account credentials must be stored in vault (HashiCorp Vault). Credential rotation for service accounts every 180 days. Never commit credentials to git repos.",
                "category": "policy",
                "tags": ["password", "credentials", "authentication"]
            },
            {
                "id": "access_control",
                "title": "Access Control and Least Privilege",
                "content": "Access control principles: Follow principle of least privilege - users get minimum access needed. Access reviews quarterly by managers. New employees: access provisioned based on role template. Departing employees: access revoked immediately upon termination. Privileged access (admin/root) requires approval from Security team and CTO. All privileged actions logged and audited. Time-bound access for contractors (max 90 days, renewable). VPN required for all remote access.",
                "category": "policy",
                "tags": ["access_control", "permissions", "rbac"]
            },
            {
                "id": "vulnerability_disclosure",
                "title": "Vulnerability Disclosure Policy",
                "content": "Security vulnerability handling: External reports sent to security@company.com acknowledged within 24 hours. Internal discoveries reported immediately to Security team. Critical vulnerabilities patched within 48 hours. High severity within 7 days. Medium within 30 days. Patch management coordinated with DevOps. Security advisories published for customer-facing vulnerabilities. Bug bounty program for external researchers - rewards up to $10,000 for critical findings.",
                "category": "policy",
                "tags": ["vulnerability", "patching", "disclosure"]
            },
            {
                "id": "incident_severity",
                "title": "Incident Severity Classification",
                "content": "Incident severity levels: CRITICAL (Sev-1) - Active breach, production down, data loss, immediate response. HIGH (Sev-2) - Significant security risk, degraded service, potential data exposure, response within 1 hour. MEDIUM (Sev-3) - Security concern, no immediate risk, response within 4 hours. LOW (Sev-4) - Minor issue, policy violation, response within 24 hours. Severity determines escalation path and response time.",
                "category": "incident_response",
                "tags": ["severity", "classification", "incident"]
            }
        ]
        
        # Try to load additional documents from file if available
        data_file = os.path.join(os.path.dirname(__file__), '../data/security_policies.json')
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                additional_docs = json.load(f)
                self.documents.extend(additional_docs)
    
    def _build_index(self):
        """Build FAISS index for similarity search"""
        texts = [doc['content'] for doc in self.documents]
        self.embeddings = self.embedding_model.encode(texts)
        
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(self.embeddings).astype('float32'))
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search knowledge base for relevant documents"""
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding).astype('float32'), 
            top_k
        )
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            doc = self.documents[idx].copy()
            doc['relevance_score'] = float(1 / (1 + distance))  # Convert distance to similarity
            results.append(doc)
        
        return results
    
    def get_document_by_id(self, doc_id: str) -> Dict:
        """Retrieve specific document by ID"""
        for doc in self.documents:
            if doc['id'] == doc_id:
                return doc
        return None
    
    def get_documents_by_category(self, category: str) -> List[Dict]:
        """Get all documents in a category"""
        return [doc for doc in self.documents if doc.get('category') == category]

knowledge_base = KnowledgeBase()
