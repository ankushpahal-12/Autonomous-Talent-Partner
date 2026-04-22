import { CheckCircle, AlertCircle, Info, Zap, Clock } from 'lucide-react';

export default function EventTimeline({ events, isConnected }) {
  if (!events || events.length === 0) return null;

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'JOB_CREATED':
      case 'JOB_CREATION_STARTED':
      case 'EMBEDDINGS_GENERATED':
      case 'SUGGESTIONS_GENERATED':
        return <CheckCircle size={18} style={{ color: 'var(--success)' }} />;
      case 'PROGRESS_UPDATE':
        return <Zap size={18} style={{ color: 'var(--accent)' }} />;
      case 'EMBEDDING_ERROR':
      case 'ERROR':
        return <AlertCircle size={18} style={{ color: 'var(--error)' }} />;
      case 'NOTIFICATION':
        return <Info size={18} style={{ color: 'var(--neon-cyan)' }} />;
      default:
        return <Clock size={18} style={{ color: 'var(--text-muted)' }} />;
    }
  };

  const getEventColor = (eventType) => {
    if (eventType.includes('ERROR')) return 'var(--error)';
    if (eventType.includes('GENERATED') || eventType.includes('CREATED')) return 'var(--success)';
    if (eventType.includes('PROGRESS')) return 'var(--accent)';
    return 'var(--neon-cyan)';
  };

  const getEventBgColor = (eventType) => {
    if (eventType.includes('ERROR')) return 'rgba(239, 68, 68, 0.05)';
    if (eventType.includes('GENERATED') || eventType.includes('CREATED')) return 'rgba(16, 185, 129, 0.05)';
    if (eventType.includes('PROGRESS')) return 'rgba(59, 130, 246, 0.05)';
    return 'rgba(34, 211, 238, 0.05)';
  };

  const getEventBorderColor = (eventType) => {
    if (eventType.includes('ERROR')) return 'rgba(239, 68, 68, 0.2)';
    if (eventType.includes('GENERATED') || eventType.includes('CREATED')) return 'rgba(16, 185, 129, 0.2)';
    if (eventType.includes('PROGRESS')) return 'rgba(59, 130, 246, 0.2)';
    return 'rgba(34, 211, 238, 0.2)';
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <div style={{
      padding: '16px',
      borderRadius: '12px',
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid var(--glass-border)',
      marginBottom: '20px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <Clock size={18} style={{ color: isConnected ? 'var(--success)' : 'var(--error)' }} />
        <span style={{ fontWeight: 600 }}>Event Timeline</span>
        <span style={{
          fontSize: '0.8rem',
          color: isConnected ? 'var(--success)' : 'var(--error)',
          marginLeft: 'auto'
        }}>
          {isConnected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>

      <div style={{
        maxHeight: '300px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}>
        {events.slice().reverse().map((event, idx) => (
          <div 
            key={idx}
            style={{
              padding: '10px 12px',
              borderRadius: '8px',
              background: getEventBgColor(event.event),
              border: `1px solid ${getEventBorderColor(event.event)}`,
              display: 'flex',
              gap: '8px',
              alignItems: 'flex-start',
              fontSize: '0.9rem'
            }}
          >
            <div style={{ minWidth: '18px', marginTop: '2px' }}>
              {getEventIcon(event.event)}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, color: getEventColor(event.event) }}>
                {event.event}
              </div>
              {event.data && Object.keys(event.data).length > 0 && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {event.event === 'PROGRESS_UPDATE' && `${event.data.task}: ${event.data.progress}%`}
                  {event.event === 'NOTIFICATION' && event.data.message}
                  {!['PROGRESS_UPDATE', 'NOTIFICATION'].includes(event.event) && 
                    JSON.stringify(event.data).substring(0, 80)}
                </div>
              )}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
              {formatTime(event.timestamp)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
