import { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot } from 'lucide-react';
import { endpoints } from '../api';

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hi! I am the Autonomous Talent AI. Ask me to find candidates by skill or name, or query technology relationships.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const toggleChat = () => setIsOpen(!isOpen);

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMsg = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(endpoints.chat, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg.text }),
      });
      const data = await res.json();
      
      setMessages((prev) => [...prev, { sender: 'bot', text: data.response || 'No response.' }]);
    } catch (error) {
      setMessages((prev) => [...prev, { sender: 'bot', text: 'Sorry, I encountered an error connecting to the backend.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      <button 
        className={`chat-widget-btn ${isOpen ? 'hidden' : ''}`} 
        onClick={toggleChat}
        style={{
          position: 'fixed', bottom: '30px', right: '30px', zIndex: 1000,
          background: 'var(--accent)', color: 'white', border: 'none',
          borderRadius: '50%', width: '60px', height: '60px',
          display: isOpen ? 'none' : 'flex', justifyContent: 'center', alignItems: 'center',
          boxShadow: '0 8px 24px rgba(59, 130, 246, 0.4)', cursor: 'pointer',
          transition: 'all 0.3s ease'
        }}
      >
        <MessageSquare size={28} />
      </button>

      <div 
        className={`chat-widget-panel ${isOpen ? 'open' : ''}`}
        style={{
          position: 'fixed', bottom: '24px', right: '24px', zIndex: 1001,
          width: '380px', height: '600px', maxHeight: '80vh',
          background: 'rgba(15, 23, 42, 0.95)', backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)', border: '1px solid var(--glass-border)',
          borderRadius: '20px', display: isOpen ? 'flex' : 'none', flexDirection: 'column',
          boxShadow: '0 12px 32px rgba(0, 0, 0, 0.6)', overflow: 'hidden'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '20px', borderBottom: '1px solid var(--glass-border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          background: 'rgba(255,255,255,0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={20} color="white" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 600, color: '#fff', background: 'none', WebkitTextFillColor: 'inherit' }}>Database AI</h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--success)' }}>● Online</span>
            </div>
          </div>
          <button onClick={toggleChat} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{
              display: 'flex', gap: '12px',
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%'
            }}>
              {msg.sender === 'bot' && (
                <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Bot size={16} />
                </div>
              )}
              <div style={{
                background: msg.sender === 'user' ? 'var(--accent)' : 'rgba(255,255,255,0.05)',
                color: 'white', padding: '12px 16px', borderRadius: '16px', borderBottomRightRadius: msg.sender === 'user' ? '4px' : '16px',
                borderBottomLeftRadius: msg.sender === 'bot' ? '4px' : '16px',
                fontSize: '0.95rem', lineHeight: '1.5', wordBreak: 'break-word', whiteSpace: 'pre-wrap'
              }}>
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '12px' }}>
               <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Bot size={16} />
                </div>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px 16px', borderRadius: '16px', borderBottomLeftRadius: '4px' }}>
                  <div className="loader" style={{ width: '16px', height: '16px', margin: 0, borderWidth: '2px' }}></div>
                </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{ padding: '16px', borderTop: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.2)' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', background: 'rgba(255,255,255,0.05)', borderRadius: '24px', padding: '8px 16px', border: '1px solid var(--glass-border)' }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Ask about candidates..."
              style={{
                flex: 1, background: 'transparent', border: 'none', color: 'white',
                outline: 'none', resize: 'none', maxHeight: '100px', minHeight: '24px',
                padding: '4px 0', fontFamily: 'inherit', fontSize: '0.95rem'
              }}
              rows={1}
            />
            <button onClick={sendMessage} disabled={loading || !input.trim()} style={{
              background: 'var(--accent)', border: 'none', color: 'white', width: '36px', height: '36px',
              borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: (loading || !input.trim()) ? 'not-allowed' : 'pointer', opacity: (loading || !input.trim()) ? 0.5 : 1,
              transition: 'all 0.2s', padding: 0
            }}>
              <Send size={18} style={{ marginLeft: '2px' }} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
