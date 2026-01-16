from typing import Dict, List, Optional
from openai import OpenAI
from config import config
import json
import re

class SecurityAgent:
    """Agentic AI that decides which tools to use and orchestrates responses"""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.conversation_history = []
        
    def _build_system_prompt(self, user_role: str, available_tools: List[str]) -> str:
        """Build system prompt based on user role and permissions"""
        base_prompt = """You are a Security Incident Knowledge Assistant for an enterprise.
Your role is to help employees understand and respond to security incidents.

You have access to the following tools:
{tools}

When responding to queries:
1. Analyze the user's question carefully
2. Decide which tool(s) would be most helpful
3. Use tools to gather information when needed
4. Provide clear, actionable guidance
5. Always prioritize security and follow the principle of least privilege

User Role: {role}

Guidelines:
- Be concise but thorough
- Reference specific policies and playbooks
- Provide step-by-step instructions for incident response
- Escalate critical issues appropriately
- Never share information outside the user's permission level
"""
        
        tools_description = "\n".join([f"- {tool}" for tool in available_tools])
        return base_prompt.format(tools=tools_description, role=user_role)
    
    def _extract_tool_calls(self, text: str) -> List[Dict]:
        """Extract tool calls from LLM response"""
        # Look for patterns like [TOOL: tool_name, params: {...}]
        pattern = r'\[TOOL:\s*(\w+)(?:,\s*params:\s*(\{[^}]+\}))?\]'
        matches = re.findall(pattern, text)
        
        tool_calls = []
        for match in matches:
            tool_name = match[0]
            params = {}
            if match[1]:
                try:
                    params = json.loads(match[1])
                except:
                    pass
            tool_calls.append({"tool": tool_name, "params": params})
        
        return tool_calls
    
    def decide_action(self, query: str, user_role: str, available_tools: List[str]) -> Dict:
        """
        Use LLM to decide which tools to call based on the query
        Returns: {"tools_to_call": [...], "reasoning": "..."}
        """
        decision_prompt = f"""Given the user query and available tools, decide which tools should be called.

Available tools:
- knowledge_base: Search security policies, playbooks, and incident response procedures
- log_analyzer: Query security logs for failed logins, suspicious activity, user behavior
- audit_logs: View audit trail (admin only)

User query: "{query}"
User role: {user_role}

Respond in JSON format:
{{
  "tools_to_call": [
    {{"tool": "tool_name", "params": {{"param1": "value"}}, "reason": "why this tool"}}
  ],
  "needs_tools": true/false,
  "reasoning": "explanation of decision"
}}

If no tools are needed, respond with needs_tools: false.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a tool selection agent. Respond only with valid JSON."},
                    {"role": "user", "content": decision_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"tools_to_call": [], "needs_tools": False, "reasoning": "Could not parse decision"}
                
        except Exception as e:
            print(f"Error in decide_action: {e}")
            # Fallback: simple keyword matching
            tools_to_call = []
            if any(word in query.lower() for word in ['policy', 'procedure', 'how to', 'what is', 'playbook']):
                tools_to_call.append({"tool": "knowledge_base", "params": {}, "reason": "Query about policies"})
            if any(word in query.lower() for word in ['logs', 'failed login', 'activity', 'attempts']):
                tools_to_call.append({"tool": "log_analyzer", "params": {}, "reason": "Query about logs"})
            
            return {
                "tools_to_call": tools_to_call,
                "needs_tools": len(tools_to_call) > 0,
                "reasoning": "Fallback keyword matching"
            }
    
    def generate_response(
        self, 
        query: str, 
        user_role: str,
        tool_results: Optional[List[Dict]] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """Generate final response using LLM with tool results"""
        
        # Build context from tool results
        context = ""
        if tool_results:
            context = "\n\n=== Information gathered from tools ===\n"
            for result in tool_results:
                context += f"\n[{result['tool']}]:\n{json.dumps(result['result'], indent=2)}\n"
        
        messages = [
            {
                "role": "system", 
                "content": f"""You are a Security Incident Knowledge Assistant.
User role: {user_role}

Provide helpful, accurate security guidance. Use the tool results provided to give specific answers.
Be clear, actionable, and security-focused. Format responses with proper structure."""
            },
            {
                "role": "user",
                "content": f"{query}\n{context}"
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.MAX_TOKENS
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def explain_reasoning(self, query: str, tools_used: List[str], result: str) -> str:
        """Generate explanation of why the assistant answered the way it did"""
        explanation = f"""
**Decision Process:**

1. **Query Analysis:** I analyzed your question: "{query[:100]}..."

2. **Tools Selected:** 
{chr(10).join([f"   - {tool}: Used to gather relevant information" for tool in tools_used])}

3. **Information Synthesis:** Combined data from tools with security best practices to provide guidance.

4. **Response Generation:** Formatted the answer to be clear and actionable for your role.
"""
        return explanation

security_agent = SecurityAgent()
