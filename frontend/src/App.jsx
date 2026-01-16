import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Shield, Send, LogOut, User, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import './App.css';

const API_BASE_URL = 'http://localhost:8005';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // Check for existing token
    const token = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (token && storedUser) {
      setIsLoggedIn(true);
      setUser(JSON.parse(storedUser));
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username,
        password,
      });

      const { access_token, user: userData } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      setIsLoggedIn(true);
      setUser(userData);
      setPassword('');
      
      // Add welcome message
      setMessages([{
        type: 'system',
        content: `Welcome, ${userData.username}! I'm your Security Incident Knowledge Assistant. I can help you with security policies, incident response procedures, and log analysis. What would you like to know?`,
        role: userData.role
      }]);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
    setIsLoggedIn(false);
    setUser(null);
    setMessages([]);
    setUsername('');
    setPassword('');
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    
    // Add user message to chat
    setMessages(prev => [...prev, {
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }]);

    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/query`, {
        query: userMessage,
      });

      const { response: aiResponse, tools_used, tool_results, reasoning } = response.data;

      // Add AI response to chat
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: aiResponse,
        tools_used: tools_used || [],
        tool_results: tool_results || [],
        reasoning: reasoning,
        timestamp: new Date().toISOString()
      }]);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'An error occurred. Please try again.';
      setMessages(prev => [...prev, {
        type: 'error',
        content: errorMessage,
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const exampleQueries = [
    "How should I handle a suspected phishing email?",
    "Show me failed login attempts from the last 24 hours",
    "What's the escalation path for a security breach?",
    "Explain the password policy",
    "Detect any brute force attacks"
  ];

  if (!isLoggedIn) {
    return (
      <div className="login-container">
        <div className="login-box">
          <div className="login-header">
            <Shield size={48} className="logo-icon" />
            <h1>Security Assistant</h1>
            <p>Enterprise Security Incident Knowledge System</p>
          </div>

          {error && (
            <div className="error-banner">
              <AlertTriangle size={20} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
              />
            </div>

            <button type="submit" className="login-button">
              Login
            </button>
          </form>

          <div className="demo-credentials">
            <p><strong>Demo Credentials:</strong></p>
            <ul>
              <li>security_admin / security123 (Full access)</li>
              <li>engineer / engineer123 (KB + Logs)</li>
              <li>sales_user / sales123 (KB only)</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-left">
          <Shield size={32} className="header-logo" />
          <div>
            <h1>Security Assistant</h1>
            <p className="header-subtitle">AI-Powered Incident Response</p>
          </div>
        </div>
        <div className="header-right">
          <div className="user-info">
            <User size={20} />
            <div>
              <div className="user-name">{user.username}</div>
              <div className="user-role">{user.role}</div>
            </div>
          </div>
          <button onClick={handleLogout} className="logout-button">
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-screen">
              <Shield size={64} className="welcome-icon" />
              <h2>How can I help you today?</h2>
              <p>Try asking about security policies, incident response, or log analysis</p>
              
              <div className="example-queries">
                <p><strong>Example queries:</strong></p>
                {exampleQueries.map((query, idx) => (
                  <button
                    key={idx}
                    className="example-query"
                    onClick={() => setInputMessage(query)}
                  >
                    {query}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div key={idx} className={`message message-${message.type}`}>
              {message.type === 'system' && (
                <div className="message-icon">
                  <Info size={20} />
                </div>
              )}
              {message.type === 'user' && (
                <div className="message-icon">
                  <User size={20} />
                </div>
              )}
              {message.type === 'assistant' && (
                <div className="message-icon">
                  <Shield size={20} />
                </div>
              )}
              {message.type === 'error' && (
                <div className="message-icon">
                  <AlertTriangle size={20} />
                </div>
              )}

              <div className="message-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>

                {message.tools_used && message.tools_used.length > 0 && (
                  <div className="tools-used">
                    <div className="tools-header">
                      <CheckCircle size={16} />
                      <strong>Tools Used:</strong>
                    </div>
                    <div className="tools-list">
                      {message.tools_used.map((tool, i) => (
                        <span key={i} className="tool-badge">{tool}</span>
                      ))}
                    </div>
                  </div>
                )}

                {message.reasoning && showExplanation && (
                  <div className="reasoning-box">
                    <strong>Decision Reasoning:</strong>
                    <p>{message.reasoning}</p>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message message-assistant">
              <div className="message-icon">
                <Shield size={20} />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSendMessage} className="input-form">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about security policies, incidents, or logs..."
            disabled={isLoading}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={isLoading || !inputMessage.trim()}
            className="send-button"
          >
            <Send size={20} />
          </button>
        </form>

        <div className="chat-footer">
          <label className="explanation-toggle">
            <input
              type="checkbox"
              checked={showExplanation}
              onChange={(e) => setShowExplanation(e.target.checked)}
            />
            <span>Show decision reasoning</span>
          </label>
        </div>
      </main>
    </div>
  );
}

export default App;
