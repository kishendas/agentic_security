import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # LLM Settings
    LLM_MODEL = "gpt-4"
    LLM_TEMPERATURE = 0.3
    MAX_TOKENS = 1000
    
    # RAG Settings
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    TOP_K_RESULTS = 3
    
    # CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
    
    # Audit Log
    AUDIT_LOG_FILE = "audit_log.jsonl"
    
    # Role Permissions
    ROLE_PERMISSIONS = {
        "security": ["knowledge_base", "log_analyzer", "all_policies"],
        "engineering": ["knowledge_base", "log_analyzer"],
        "sales": ["knowledge_base"],
        "admin": ["knowledge_base", "log_analyzer", "all_policies", "audit_logs"]
    }

config = Config()
