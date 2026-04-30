import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import './Chat.css';

const welcomeMessage = {
  role: 'model',
  content: 'Welcome! Select a language below, then ask a question.'
};

const Chat = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [messages, setMessages] = useState([welcomeMessage]);
  const [conversationId, setConversationId] = useState(null);
  const [currentLanguage, setCurrentLanguage] = useState('none');
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatboxRef = useRef(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();
  const location = useLocation();

  const languages = [
    { id: 'none', name: 'Original' },
    { id: 'spanish', name: 'Spanish' },
    { id: 'french', name: 'French' },
    { id: 'german', name: 'German' },
    { id: 'japanese', name: 'Japanese' },
    { id: 'chinese', name: 'Chinese' }
  ];

  const createConversation = async () => {
    const response = await fetch('/api/my/conversations', {
      method: 'POST',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('Failed to create conversation');
    }

    const data = await response.json();
    setConversationId(data.conversation_id);
    return data.conversation_id;
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  useEffect(() => {
    const requestedConversationId = location.state?.conversationId;
    if (requestedConversationId) {
      setConversationId(requestedConversationId);
      setMessages([welcomeMessage]);
      setInputValue('');
    }
  }, [location.state]);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/auth/status', {
        credentials: 'include',
        headers: {
          Accept: 'application/json',
        }
      });
      const data = await response.json();
      if (!data.authenticated) {
        navigate('/login');
        return;
      }

      if (location.state?.conversationId) {
        setConversationId(location.state.conversationId);
      } else {
        await createConversation();
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      navigate('/login');
    }
  };

  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  const buildPayload = (question) => {
    return messages.map((m) => `${m.role}: ${m.content}`).join('\n\n') +
      '\n\n==============================\ncurrent question: ' + question;
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const question = inputValue.trim();
    setInputValue('');

    setMessages((prev) => [...prev, { role: 'user', content: question }]);

    setIsLoading(true);
    setMessages((prev) => [...prev, { role: 'model', content: 'Thinking...' }]);

    try {
      const activeConversationId = conversationId ?? await createConversation();
      const payload = buildPayload(question);

      const response = await fetch('/api/prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: payload,
          lang: currentLanguage,
          conversation_id: activeConversationId
        }),
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = { role: 'model', content: data.answer };
        return newMessages;
      });
    } catch (error) {
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = {
          role: 'model',
          content: 'Error: Could not get response. Please try again.'
        };
        return newMessages;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } finally {
      navigate('/login');
    }
  };

  const handleNewConversation = async () => {
    if (isLoading) return;

    setMessages([welcomeMessage]);
    setInputValue('');

    try {
      await createConversation();
    } catch (error) {
      console.error('Failed to create conversation:', error);
      alert('Could not start a new conversation. Please try again.');
    }
  };

  const handleFileUpload = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.txt') && !file.name.endsWith('.pdf')) {
      alert('Only .txt and .pdf files are allowed.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      const result = await response.json();
      alert(result.message);
    } catch (error) {
      alert('Error uploading file. Please try again.');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  return (
    <div className="chat-container">
      <header className="app-shell-nav">
        <div className="brand-mark" aria-label="AI Student Advisor">
          <span>AI</span>
          <strong>Student Advisor</strong>
        </div>
        <nav>
          <button type="button" className="active">CHAT</button>
          <button type="button" onClick={() => navigate('/planner')}>COURSE GRAPH</button>
          <button type="button" onClick={() => navigate('/vote')}>VOTING</button>
        </nav>
        <div className="utility-actions">
          <button onClick={handleNewConversation} className="new-chat-btn">New Chat</button>
          <button onClick={handleFileUpload} className="upload-btn">Upload File</button>
          <button onClick={handleLogout} className="logout-btn">Logout</button>
        </div>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".txt,.pdf"
          hidden
        />
      </header>

      <div className="chatbox" ref={chatboxRef}>
        {messages.map((msg, index) => (
          <div key={index} className={`msg-${msg.role === 'user' ? 'user' : 'bot'}`}>
            {msg.content}
          </div>
        ))}
      </div>

      <div className="translator-section">
        {languages.map((lang) => (
          <button
            key={lang.id}
            className={`lang-btn ${currentLanguage === lang.id ? 'active' : ''}`}
            onClick={() => setCurrentLanguage(lang.id)}
          >
            {lang.name}
          </button>
        ))}
      </div>

      <div className="input-section">
        <input
          className="promptbar"
          placeholder="Ask the advisor anything about Purdue courses, schedules, requirements, or planning."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading || conversationId === null}
        />
        <button type="button" onClick={handleSend} disabled={isLoading || conversationId === null}>
          Send
        </button>
      </div>
    </div>
  );
};

export default Chat;
