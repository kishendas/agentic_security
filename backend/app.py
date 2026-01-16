from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import timedelta
import uvicorn

from config import config
from security.prompt_defense import prompt_defense
from security.rbac import rbac_manager, User
from security.audit_logger import audit_logger
from agents.security_agent import security_agent
from agents.tool_executor import tool_executor

app = FastAPI(title="Security Incident Knowledge Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer()

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class QueryResponse(BaseModel):
    response: str
    tools_used: List[str]
    tool_results: List[dict]
    reasoning: Optional[str] = None
    security_warning: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str

# Dependency for authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """Validate JWT token and return user info"""
    token = credentials.credentials
    payload = rbac_manager.decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "username": payload.get("sub"),
        "role": payload.get("role")
    }

# Routes
@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="1.0.0")

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user = rbac_manager.authenticate_user(request.username, request.password)
    
    if not user:
        audit_logger.log_security_event(
            user=request.username,
            event_type="failed_login",
            details="Invalid credentials",
            severity="medium"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Create access token
    access_token = rbac_manager.create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    audit_logger.log_security_event(
        user=user.username,
        event_type="successful_login",
        details=f"User logged in with role: {user.role}",
        severity="low"
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=User(username=user.username, role=user.role, email=user.email)
    )

@app.post("/api/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process user query with AI agent"""
    username = current_user["username"]
    role = current_user["role"]
    query = request.query
    
    # 1. Prompt Injection Defense
    is_malicious, reason = prompt_defense.is_malicious(query)
    if is_malicious:
        audit_logger.log_security_event(
            user=username,
            event_type="prompt_injection_blocked",
            details=reason,
            severity="high"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security alert: {reason}"
        )
    
    # Sanitize input
    query = prompt_defense.sanitize_input(query)
    
    # 2. Get user permissions
    available_tools = []
    if rbac_manager.has_permission(role, "knowledge_base"):
        available_tools.append("knowledge_base")
    if rbac_manager.has_permission(role, "log_analyzer"):
        available_tools.append("log_analyzer")
    
    # 3. Agent decides which tools to use
    decision = security_agent.decide_action(query, role, available_tools)
    
    # 4. Execute tools
    tool_results = []
    tools_used = []
    
    if decision.get("needs_tools", False):
        tools_to_call = decision.get("tools_to_call", [])
        
        # Filter tools based on permissions
        authorized_calls = []
        for tool_call in tools_to_call:
            tool_name = tool_call["tool"]
            if tool_name in available_tools:
                authorized_calls.append(tool_call)
            else:
                audit_logger.log_security_event(
                    user=username,
                    event_type="unauthorized_tool_access",
                    details=f"Attempted to use {tool_name} without permission",
                    severity="medium"
                )
        
        # Execute authorized tools
        if authorized_calls:
            tool_results = tool_executor.execute_multiple(authorized_calls, username)
            tools_used = [r["tool"] for r in tool_results]
    
    # 5. Generate response
    response_text = security_agent.generate_response(
        query=query,
        user_role=role,
        tool_results=tool_results,
        conversation_id=request.conversation_id
    )
    
    # 6. Log the interaction
    audit_logger.log_interaction(
        user=username,
        role=role,
        prompt=query,
        action="query_processed",
        tool_used=", ".join(tools_used) if tools_used else "none",
        result_summary=response_text[:100],
        status="success"
    )
    
    return QueryResponse(
        response=response_text,
        tools_used=tools_used,
        tool_results=tool_results,
        reasoning=decision.get("reasoning")
    )

@app.get("/api/user/permissions")
async def get_permissions(current_user: dict = Depends(get_current_user)):
    """Get current user's permissions"""
    role = current_user["role"]
    permissions = rbac_manager.get_user_permissions(role)
    
    return {
        "username": current_user["username"],
        "role": role,
        "permissions": permissions
    }

@app.get("/api/audit/logs")
async def get_audit_logs(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get audit logs (admin only)"""
    role = current_user["role"]
    
    if not rbac_manager.has_permission(role, "audit_logs"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view audit logs"
        )
    
    logs = audit_logger.get_recent_logs(limit=limit)
    return {"logs": logs, "count": len(logs)}

if __name__ == "__main__":
    print("🚀 Starting Security Incident Knowledge Assistant")
    print(f"📝 API Documentation: http://localhost:8005/docs")
    print(f"🔐 Default users:")
    print("   - security_admin / security123 (Security role)")
    print("   - engineer / engineer123 (Engineering role)")
    print("   - sales_user / sales123 (Sales role)")
    uvicorn.run(app, host="0.0.0.0", port=8005)
