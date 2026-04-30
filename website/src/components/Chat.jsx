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

  const parseChatHistory = (historyString) => {
    if (!historyString || historyString.trim() === "") return [welcomeMessage];
    
    const historyMessages = [];
    // Split by the equals sign separator (matching 10 or more to be safe)
    const blocks = historyString.split(/={10,}/);

    blocks.forEach(block => {
      if (block.trim() === '') return;

      const qIndex = block.indexOf('Q:');
      const aIndex = block.indexOf('A:');

      if (qIndex !== -1 && aIndex !== -1) {
        // Grab everything between "Q:" and "A:"
        const qText = block.substring(qIndex + 2, aIndex).trim();
        // Grab everything after "A:" to the end of the block
        const aText = block.substring(aIndex + 2).trim();

        if (qText) historyMessages.push({ role: 'user', content: qText });
        if (aText) historyMessages.push({ role: 'model', content: aText });
      } else if (qIndex !== -1) {
        // Handle edge case where a question exists but the answer got cut off
        const qText = block.substring(qIndex + 2).trim();
        if (qText) historyMessages.push({ role: 'user', content: qText });
      }
    });

    return historyMessages.length > 0 ? historyMessages : [welcomeMessage];
  };

  const fetchChatHistory = async () => {
    try {
      const response = await fetch('/api/get_history', { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        const parsed = parseChatHistory(data.history);
        setMessages(parsed);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  };

  const handleNavigate = async (direction) => {
    if (isLoading) return;
    setIsLoading(true);

    try {
      const response = await fetch('/api/my/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: direction }),
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to navigate conversation');
      
      const data = await response.json();
      setConversationId(data.conversation_id);
      
      await fetchChatHistory();
      setInputValue('');
    } catch (error) {
      console.error('Navigation failed:', error);
      alert('Could not change conversation.');
    } finally {
      setIsLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/auth/status', {
        credentials: 'include',
        headers: { Accept: 'application/json' }
      });
      const data = await response.json();
      if (!data.authenticated) { navigate('/login'); return; }

      await fetchChatHistory();
      if (location.state?.conversationId) {
        setConversationId(location.state.conversationId);
      } else {
        handleNavigate('stay'); 
      }
    } catch (error) {
      navigate('/login');
    }
  };

  useEffect(() => { checkAuthStatus(); }, []);

  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  const buildPayload = (question) => {
    return messages.map((m) => `${m.role === 'user' ? 'Q' : 'A'}: ${m.content}`).join('\n\n') +
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
      const payload = buildPayload(question);
      const response = await fetch('/api/prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: payload,
          lang: currentLanguage,
          conversation_id: conversationId
        }),
        credentials: 'include'
      });
      const data = await response.json();
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = {
          role: 'model', content: data.answer, turn_id: data.turn_id
        };
        return newMessages;
      });
    } catch (error) {
      setMessages((prev) => [...prev.slice(0, -1), { role: 'model', content: 'Error getting response.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = () => fileInputRef.current.click();
  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    setIsUploading(true);
    try {
      await fetch('/api/upload', { method: 'POST', body: formData, credentials: 'include' });
      alert("File uploaded!");
    } catch (error) { alert('Upload failed.'); } 
    finally { setIsUploading(false); e.target.value = ''; }
  };

  return (
    <div className="chat-container">
      <div className="topbar">
        <button 
          onClick={() => handleNavigate('back')} 
          className="nav-btn" 
          disabled={isLoading}
        >
          Back
        </button>
        <button 
          onClick={() => handleNavigate('forward')} 
          className="nav-btn" 
          disabled={isLoading}
        >
          Forward
        </button>
        
        <button onClick={() => navigate('/vote')} className="vote-btn">Voting</button>
        <button onClick={handleFileUpload} className="upload-btn">Upload File</button>
        <button onClick={() => fetch('/api/logout', {method: 'POST'}).then(() => navigate('/login'))} className="logout-btn">Logout</button>
        <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".txt,.pdf" hidden />
      </div>

      <div className="chatbox" ref={chatboxRef}>
        {messages.map((msg, index) => (
          <div key={index}>
            <div className={`msg-${msg.role === 'user' ? 'user' : 'bot'}`}>{msg.content}</div>
          </div>
        ))}
      </div>

      <div className="translator-section">
        {languages.map((lang) => (
          <button key={lang.id} className={`lang-btn ${currentLanguage === lang.id ? 'active' : ''}`} onClick={() => setCurrentLanguage(lang.id)}>
            {lang.name}
          </button>
        ))}
      </div>

      <div className="input-section">
        <input
          className="promptbar"
          placeholder="Ask a question..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          disabled={isLoading}
        />
      </div>
    </div>
  );
};

export default Chat;