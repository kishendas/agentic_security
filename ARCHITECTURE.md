# System Architecture

## Overview

The Security Incident Knowledge Assistant is a full-stack AI application combining Generative AI (GPT-4 for conversations) with Agentic AI (autonomous tool selection and execution) to provide enterprise security guidance.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐     │
│  │  React UI  │  │  Auth State │  │  Message Manager │     │
│  └──────┬─────┘  └──────┬──────┘  └────────┬─────────┘     │
│         └────────────────┴──────────────────┘               │
│                          │ HTTP/REST                         │
└──────────────────────────┼───────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────┐
│                  API Gateway (FastAPI)                       │
│         ┌────────────────┴────────────────┐                 │
│         │    Middleware & Security        │                 │
│         │  - CORS                         │                 │
│         │  - JWT Authentication           │                 │
│         │  - Request Validation           │                 │
│         └────────────┬────────────────────┘                 │
│                      │                                       │
│  ┌───────────────────┼──────────────────────────────────┐   │
│  │         Security Layer (Pre-Processing)              │   │
│  │  ┌─────────────┐  ┌──────────┐  ┌────────────────┐  │   │
│  │  │   Prompt    │  │   RBAC   │  │  Audit Logger  │  │   │
│  │  │  Injection  │  │ Enforcer │  │    (Start)     │  │   │
│  │  │   Defense   │  │          │  │                │  │   │
│  │  └──────┬──────┘  └────┬─────┘  └───────┬────────┘  │   │
│  └─────────┼──────────────┼─────────────────┼───────────┘   │
│            │              │                 │               │
│  ┌─────────▼──────────────▼─────────────────▼───────────┐   │
│  │              Agentic AI Orchestrator                  │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │         GPT-4 Decision Engine                │    │   │
│  │  │  • Analyze query intent                      │    │   │
│  │  │  • Select appropriate tools                  │    │   │
│  │  │  • Generate reasoning                        │    │   │
│  │  └────────────┬─────────────────────────────────┘    │   │
│  └───────────────┼──────────────────────────────────────┘   │
│                  │                                           │
│  ┌───────────────▼──────────────────────────────────────┐   │
│  │              Tool Executor                           │   │
│  │  ┌──────────────┐         ┌──────────────────────┐  │   │
│  │  │  Knowledge   │         │   Log Analyzer       │  │   │
│  │  │  Base (RAG)  │         │  - Failed Logins     │  │   │
│  │  │              │         │  - Brute Force       │  │   │
│  │  │  - FAISS     │         │  - User Activity     │  │   │
│  │  │  - Embeddings│         │  - Log Search        │  │   │
│  │  └──────┬───────┘         └──────────┬───────────┘  │   │
│  └─────────┼────────────────────────────┼──────────────┘   │
│            │                            │                   │
│  ┌─────────▼────────────────────────────▼──────────────┐   │
│  │        Response Generator (GPT-4)                    │   │
│  │  • Synthesize tool results                           │   │
│  │  • Generate natural language response                │   │
│  │  • Format with markdown                              │   │
│  └─────────────────────┬────────────────────────────────┘   │
│                        │                                     │
│  ┌─────────────────────▼────────────────────────────────┐   │
│  │       Audit Logger (Post-Processing)                 │   │
│  │  • Log complete interaction                          │   │
│  │  • Record tool usage                                 │   │
│  │  • Track performance metrics                         │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                     Data Layer                               │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ FAISS Vector  │  │ Security    │  │  Audit Log       │  │
│  │    Index      │  │  Logs CSV   │  │    (JSONL)       │  │
│  │  (In-Memory)  │  │             │  │                  │  │
│  └────────────────┘  └─────────────┘  └──────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend (React)

**Technology**: React 18, Axios, React Markdown, Lucide Icons

**Key Components**:
- `App.jsx`: Main application component
  - Authentication state management
  - Message history management
  - API communication
  - UI rendering

**State Management**:
```javascript
{
  isLoggedIn: boolean,
  user: { username, role, email },
  messages: [{ type, content, tools_used, timestamp }],
  inputMessage: string,
  isLoading: boolean
}
```

**Key Features**:
- JWT token persistence in localStorage
- Automatic token refresh headers
- Markdown rendering for rich responses
- Real-time typing indicators
- Example query suggestions

### 2. API Gateway (FastAPI)

**Technology**: FastAPI, Pydantic, Python 3.11

**Endpoints**:

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Health check | No |
| POST | `/api/auth/login` | User authentication | No |
| POST | `/api/query` | Process AI query | Yes |
| GET | `/api/user/permissions` | Get user permissions | Yes |
| GET | `/api/audit/logs` | View audit logs | Yes (Admin) |

**Middleware Stack**:
1. CORS (allow configured origins)
2. Request validation (Pydantic models)
3. Authentication (JWT bearer tokens)
4. Error handling (global exception handlers)

### 3. Security Layer

#### A. Prompt Injection Defense

**File**: `security/prompt_defense.py`

**Detection Methods**:
- Regex pattern matching for known injection phrases
- Special character ratio analysis
- Input length validation
- Command injection prevention

**Blocked Patterns**:
```python
[
  "ignore (previous|all) instructions",
  "you are now|from now on",
  "system: you are",
  "reveal your prompt",
  "admin mode|developer mode"
]
```

#### B. Role-Based Access Control (RBAC)

**File**: `security/rbac.py`

**Role Hierarchy**:
```
Admin > Security > Engineering > Sales
```

**Permission Matrix**:
```python
{
  "security": ["knowledge_base", "log_analyzer", "all_policies"],
  "engineering": ["knowledge_base", "log_analyzer"],
  "sales": ["knowledge_base"],
  "admin": ["*"]  # All permissions
}
```

**Authentication Flow**:
```
1. User submits credentials
2. bcrypt password verification
3. JWT token generation (30-min expiry)
4. Token stored client-side
5. Token validated on each request
```

#### C. Audit Logger

**File**: `security/audit_logger.py`

**Log Entry Schema**:
```json
{
  "timestamp": "ISO-8601",
  "user": "username",
  "role": "role_name",
  "prompt": "truncated_query",
  "action": "action_type",
  "tool_used": "tool_name",
  "result_summary": "truncated_result",
  "status": "success|error",
  "metadata": {}
}
```

**Log Types**:
- User interactions
- Security events
- Tool calls
- Authentication events

### 4. Agentic AI Orchestrator

**File**: `agents/security_agent.py`

**Core Responsibilities**:
1. **Query Analysis**: Understand user intent
2. **Tool Selection**: Decide which tools to invoke
3. **Response Generation**: Synthesize results into natural language

**Decision Engine**:
```python
def decide_action(query, user_role, available_tools):
    # GPT-4 prompt engineering to analyze query
    # Returns: {
    #   "tools_to_call": [...],
    #   "needs_tools": bool,
    #   "reasoning": str
    # }
```

**Agentic Behaviors**:
- Autonomous tool selection (no hardcoded rules)
- Multi-tool orchestration
- Context-aware responses
- Explanation generation

### 5. Tool Executor

**File**: `agents/tool_executor.py`

**Tool Interface**:
```python
def execute(tool_name, params, user):
    # 1. Validate tool exists
    # 2. Execute tool
    # 3. Log execution
    # 4. Return structured result
```

**Available Tools**:

#### A. Knowledge Base (RAG)

**File**: `tools/knowledge_base.py`

**Technology**: FAISS, Sentence-Transformers

**Process**:
```
1. Load security documents
2. Generate embeddings (all-MiniLM-L6-v2)
3. Build FAISS index
4. Query: embed query → search index → return top-K
```

**Document Schema**:
```python
{
  "id": "unique_id",
  "title": "Document Title",
  "content": "Full text content",
  "category": "policy|incident_response|escalation",
  "tags": ["tag1", "tag2"]
}
```

**Search Algorithm**:
- Cosine similarity via L2 distance in FAISS
- Top-K retrieval (default K=3)
- Relevance scoring

#### B. Log Analyzer

**File**: `tools/log_analyzer.py`

**Technology**: Pandas, CSV

**Capabilities**:
- Failed login analysis
- Brute force detection
- User activity tracking
- Keyword search

**Log Schema**:
```python
{
  "timestamp": datetime,
  "user": string,
  "action": string,
  "source": string,
  "ip_address": string,
  "status": "success|failed",
  "details": string
}
```

**Brute Force Detection Algorithm**:
```python
def detect_brute_force(threshold=5, window_minutes=10):
    # Sliding window analysis
    # Flag: >= threshold failed logins in window
    # Return: alerts with severity
```

### 6. Response Generator

**Technology**: OpenAI GPT-4

**Input Context**:
- User query
- User role
- Tool results (if any)
- Conversation history (if implemented)

**System Prompt Template**:
```
You are a Security Incident Knowledge Assistant.
User role: {role}
Provide helpful, accurate security guidance.
Use tool results: {tool_results}
```

**Output**:
- Natural language response
- Markdown formatted
- Actionable guidance
- References to sources

### 7. Data Layer

#### A. Vector Database (FAISS)

**Storage**: In-memory (rebuilt on startup)

**Index Type**: IndexFlatL2 (exact search)

**Dimensions**: 384 (all-MiniLM-L6-v2 embedding size)

**Performance**: O(n) search, suitable for <10K documents

#### B. Security Logs

**Format**: CSV

**Storage**: `backend/data/security_logs.csv`

**Generation**: Mock data generator creates realistic logs

**Size**: ~500 entries covering 7 days

#### C. Audit Log

**Format**: JSONL (JSON Lines)

**Storage**: `backend/audit_log.jsonl`

**Persistence**: Append-only file

**Rotation**: Manual (production would use log rotation)

## Data Flow: Complete Request Lifecycle

### Example: "Show me failed login attempts from today"

1. **Frontend**:
   ```
   User types query → Click send → POST /api/query
   Authorization: Bearer <token>
   Body: { "query": "Show me failed login attempts from today" }
   ```

2. **API Gateway**:
   ```
   Receive request → Validate JWT → Extract user info
   User: security_admin, Role: security
   ```

3. **Prompt Injection Defense**:
   ```
   Check query for malicious patterns → Clean ✓
   Sanitize input → Pass through
   ```

4. **RBAC Check**:
   ```
   Role: security → Permissions: [knowledge_base, log_analyzer, all_policies]
   log_analyzer required → Authorized ✓
   ```

5. **Agentic Decision**:
   ```
   GPT-4 analyzes: "This query needs log analysis"
   Decision: {
     "tools_to_call": [{"tool": "log_analyzer", "params": {"action": "failed_logins", "hours": 24}}],
     "needs_tools": true,
     "reasoning": "User requesting security log data"
   }
   ```

6. **Tool Execution**:
   ```
   Tool Executor → log_analyzer.get_failed_logins(hours=24)
   Result: {
     "total_failed": 23,
     "by_user": {"john.doe": 5, "admin": 3, ...},
     "by_ip": {"203.0.113.45": 8, ...}
   }
   Execution time: 45ms
   ```

7. **Audit Logging**:
   ```
   Log: {
     "timestamp": "2026-01-15T10:30:00Z",
     "user": "security_admin",
     "tool_used": "log_analyzer",
     "status": "success"
   }
   ```

8. **Response Generation**:
   ```
   GPT-4 synthesizes:
   Input: Query + Tool Results
   Output: "I found 23 failed login attempts in the last 24 hours. 
            The top users are john.doe (5) and admin (3). 
            The IP 203.0.113.45 has 8 failed attempts, which may indicate 
            a brute force attack. I recommend..."
   ```

9. **Frontend Display**:
   ```
   Receive response → Display message
   Show "Tools Used: log_analyzer" badge
   Render markdown content
   ```

## Security Architecture

### Defense in Depth

**Layer 1: Network**
- CORS restrictions
- HTTPS (production)

**Layer 2: Authentication**
- JWT tokens
- bcrypt password hashing
- Token expiration

**Layer 3: Authorization**
- Role-based permissions
- Tool access control
- Endpoint restrictions

**Layer 4: Input Validation**
- Prompt injection detection
- Request sanitization
- Type validation (Pydantic)

**Layer 5: Output Protection**
- Sensitive data masking (ready for implementation)
- Audit logging
- Rate limiting (can be added)

### Threat Model

| Threat | Mitigation |
|--------|-----------|
| Prompt Injection | Pattern detection, input sanitization |
| Unauthorized Access | JWT auth, RBAC, permission checks |
| Data Exfiltration | Role-based data access, audit logging |
| Brute Force Login | Account lockout (can be added) |
| XSS | React escaping, CSP headers (can be added) |
| CSRF | SameSite cookies (can be added) |

## Scalability Considerations

### Current Limitations
- In-memory FAISS index
- Single-server deployment
- CSV log storage
- No caching layer

### Production Enhancements
```
1. Database:
   - PostgreSQL for users, logs
   - Pinecone/Weaviate for vector storage

2. Caching:
   - Redis for frequent queries
   - CDN for static assets

3. Load Balancing:
   - Multiple backend instances
   - Nginx reverse proxy

4. Monitoring:
   - Prometheus metrics
   - Grafana dashboards
   - Sentry error tracking

5. Deployment:
   - Kubernetes orchestration
   - Docker containers
   - CI/CD pipeline
```

## Technology Choices: Rationale

| Technology | Reason |
|-----------|---------|
| FastAPI | Async support, automatic docs, type safety |
| React | Component reusability, ecosystem, performance |
| GPT-4 | Best-in-class reasoning for tool selection |
| FAISS | Fast similarity search, no external dependencies |
| JWT | Stateless auth, scalable, standard |
| bcrypt | Industry standard password hashing |
| Sentence-Transformers | High-quality embeddings, open source |

## Future Architecture Vision

```
┌─────────────────────────────────────────────────┐
│           Multi-Channel Interface               │
│  Web App │ Mobile App │ Slack Bot │ API         │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│        API Gateway + Load Balancer              │
│              (Nginx/Kong)                       │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│     Microservices Architecture                  │
│  ┌─────────┐  ┌────────┐  ┌──────────────────┐ │
│  │  Auth   │  │  Chat  │  │  Tool Orchestr.  │ │
│  │ Service │  │Service │  │    Service       │ │
│  └─────────┘  └────────┘  └──────────────────┘ │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│            Data & AI Services                   │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ PostgreSQL │  │  Pinecone  │  │  Redis   │  │
│  │ (Metadata) │  │  (Vectors) │  │  (Cache) │  │
│  └────────────┘  └────────────┘  └──────────┘  │
└─────────────────────────────────────────────────┘
```

## Conclusion

This architecture balances simplicity for demonstration with production-ready concepts. The modular design allows easy extension while maintaining security and traceability at every layer.
