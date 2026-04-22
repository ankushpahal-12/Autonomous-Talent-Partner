import { useState, useEffect } from 'react';
import { Clock, Cpu, User, Zap, AlertCircle, RefreshCw } from 'lucide-react';
import { endpoints } from '../api';

export default function ActivityLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch(endpoints.systemActivity);
      if (!res.ok) {
        throw new Error(`API error: ${res.status} ${res.statusText}`);
      }
      const data = await res.json();
      // Ensure data is an array
      const logArray = Array.isArray(data) ? data : (data?.logs || []);
      setLogs(logArray);
    } catch (err) {
      console.error('Failed to fetch activity logs:', err);
      setLogs([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    // Poll every 10 seconds for "real-time" feel
    const interval = setInterval(fetchLogs, 10000);
    return () => clearInterval(interval);
  }, []);

  const getEventIcon = (type) => {
    switch (type) {
      case 'AI': return <Cpu size={18} className="text-accent" />;
      case 'HR': return <User size={18} style={{ color: '#ec4899' }} />; // Pink
      case 'Automation': return <Zap size={18} style={{ color: '#eab308' }} />; // Yellow
      case 'Error': return <AlertCircle size={18} style={{ color: '#ef4444' }} />; // Red
      default: return <Clock size={18} className="text-muted" />;
    }
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <header style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ textAlign: 'left', background: 'none', WebkitTextFillColor: 'inherit' }}>System Activity Feed</h1>
          <p className="subtitle" style={{ textAlign: 'left', marginBottom: 0 }}>
            Real-time audit trail of AI processing, HR decisions, and automated workflows.
          </p>
        </div>
        <button 
          className="btn-pill" 
          onClick={fetchLogs} 
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </header>

      {loading && logs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '100px' }}>
          <span className="loader"></span>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {logs.map((log, index) => (
              <div 
                key={log._id} 
                style={{ 
                  padding: '24px', 
                  borderBottom: index === logs.length - 1 ? 'none' : '1px solid var(--glass-border)',
                  display: 'flex',
                  gap: '20px',
                  transition: 'background 0.2s ease',
                  cursor: 'default'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
              >
                <div style={{ 
                  width: '40px', 
                  height: '40px', 
                  borderRadius: '12px', 
                  background: 'rgba(255,255,255,0.05)', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {getEventIcon(log.event_type)}
                </div>
                
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-main)' }}>{log.event_type} Event</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: '1.5' }}>
                    {log.description}
                  </p>
                  {log.metadata && (
                    <div style={{ 
                      marginTop: '12px', 
                      padding: '8px 12px', 
                      background: 'rgba(0,0,0,0.1)', 
                      borderRadius: '8px', 
                      fontSize: '0.75rem', 
                      fontFamily: 'monospace',
                      color: 'var(--accent)',
                      opacity: 0.8
                    }}>
                      {typeof log.metadata === 'object' ? JSON.stringify(log.metadata) : log.metadata}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {logs.length === 0 && !loading && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px' }}>
          <Clock size={48} style={{ opacity: 0.1, marginBottom: '16px' }} />
          <p className="subtitle">No system activity recorded yet.</p>
        </div>
      )}
    </div>
  );
}
