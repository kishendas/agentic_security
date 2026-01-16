from typing import Dict, Any, List
import time
from tools.knowledge_base import knowledge_base
from tools.log_analyzer import log_analyzer
from security.audit_logger import audit_logger

class ToolExecutor:
    """Executes tool calls and returns results"""
    
    def __init__(self):
        self.tools = {
            "knowledge_base": self._execute_knowledge_base,
            "log_analyzer": self._execute_log_analyzer,
        }
    
    def execute(self, tool_name: str, params: Dict[str, Any], user: str) -> Dict:
        """
        Execute a tool and return results
        Returns: {"tool": str, "result": any, "execution_time": float, "status": str}
        """
        start_time = time.time()
        
        if tool_name not in self.tools:
            return {
                "tool": tool_name,
                "result": {"error": f"Unknown tool: {tool_name}"},
                "execution_time": 0,
                "status": "error"
            }
        
        try:
            result = self.tools[tool_name](params)
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Log the tool call
            audit_logger.log_tool_call(
                user=user,
                tool_name=tool_name,
                parameters=params,
                result=str(result)[:200],
                execution_time=execution_time
            )
            
            return {
                "tool": tool_name,
                "result": result,
                "execution_time": execution_time,
                "status": "success"
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_result = {
                "tool": tool_name,
                "result": {"error": str(e)},
                "execution_time": execution_time,
                "status": "error"
            }
            
            # Log the failed tool call
            audit_logger.log_tool_call(
                user=user,
                tool_name=tool_name,
                parameters=params,
                result=f"ERROR: {str(e)}",
                execution_time=execution_time
            )
            
            return error_result
    
    def _execute_knowledge_base(self, params: Dict[str, Any]) -> Any:
        """Execute knowledge base search"""
        query = params.get("query", params.get("q", ""))
        top_k = params.get("top_k", 3)
        
        if not query:
            return {"error": "Query parameter required"}
        
        results = knowledge_base.search(query, top_k=top_k)
        
        # Format results for better readability
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "title": doc["title"],
                "content": doc["content"],
                "category": doc.get("category", "unknown"),
                "relevance_score": round(doc["relevance_score"], 3)
            })
        
        return {
            "query": query,
            "results_found": len(formatted_results),
            "results": formatted_results
        }
    
    def _execute_log_analyzer(self, params: Dict[str, Any]) -> Any:
        """Execute log analysis"""
        action = params.get("action", "failed_logins")
        
        if action == "failed_logins":
            hours = params.get("hours", 24)
            user = params.get("user")
            return log_analyzer.get_failed_logins(hours=hours, user=user)
        
        elif action == "brute_force":
            threshold = params.get("threshold", 5)
            time_window = params.get("time_window_minutes", 10)
            return log_analyzer.detect_brute_force(
                threshold=threshold,
                time_window_minutes=time_window
            )
        
        elif action == "user_activity":
            user = params.get("user")
            hours = params.get("hours", 24)
            if not user:
                return {"error": "User parameter required for user_activity"}
            return log_analyzer.get_user_activity(user=user, hours=hours)
        
        elif action == "search":
            keyword = params.get("keyword", params.get("query", ""))
            hours = params.get("hours", 168)
            if not keyword:
                return {"error": "Keyword parameter required for search"}
            return log_analyzer.search_logs(keyword=keyword, hours=hours)
        
        else:
            return {"error": f"Unknown log_analyzer action: {action}"}
    
    def execute_multiple(self, tool_calls: List[Dict], user: str) -> List[Dict]:
        """Execute multiple tool calls and return all results"""
        results = []
        for call in tool_calls:
            tool_name = call.get("tool")
            params = call.get("params", {})
            result = self.execute(tool_name, params, user)
            results.append(result)
        return results

tool_executor = ToolExecutor()
