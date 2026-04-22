import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, AlertCircle, Info, Zap, FileText, Brain, 
  TrendingUp, Clock, X 
} from 'lucide-react';

const RealtimeNotifications = ({ events, isConnected }) => {
  const [notifications, setNotifications] = useState([]);
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    if (events && events.length > 0) {
      const latestEvent = events[events.length - 1];
      
      // Filter out internal progress updates from toast notifications
      if (latestEvent.event && !latestEvent.event.includes('PROGRESS')) {
        addToast(latestEvent);
      }
    }
  }, [events]);

  const addToast = (event) => {
    const toastId = Math.random();
    const toast = createToastFromEvent(event, toastId);
    
    setToasts(prev => [...prev, toast]);
    
    // Auto-remove after 5 seconds (unless it's an error)
    const duration = event.event && event.event.includes('ERROR') ? 8000 : 5000;
    setTimeout(() => {
      removeToast(toastId);
    }, duration);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const createToastFromEvent = (event, id) => {
    const eventType = event.event || 'NOTIFICATION';
    const data = event.data || {};
    
    const toastConfig = {
      id,
      type: 'info',
      icon: <Info size={20} />,
      title: 'Update',
      message: ''
    };

    // CV Upload Events
    if (eventType === 'CV_UPLOAD_STARTED') {
      toastConfig.type = 'info';
      toastConfig.icon = <FileText size={20} />;
      toastConfig.title = 'Uploading CV';
      toastConfig.message = `Uploading ${data.filename || 'resume'}...`;
    }
    else if (eventType === 'CV_UPLOADED') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'CV Uploaded';
      toastConfig.message = `${data.filename || 'Resume'} uploaded successfully (${data.size_mb} MB)`;
    }
    else if (eventType === 'CV_PARSING_STARTED') {
      toastConfig.type = 'info';
      toastConfig.icon = <Zap size={20} />;
      toastConfig.title = 'Parsing CV';
      toastConfig.message = 'Extracting information from your CV...';
    }
    else if (eventType === 'CV_PARSING_DONE') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'CV Parsed';
      toastConfig.message = 'CV content extracted successfully';
    }
    else if (eventType === 'CV_EMBEDDING_STARTED') {
      toastConfig.type = 'info';
      toastConfig.icon = <Zap size={20} />;
      toastConfig.title = 'Generating Embeddings';
      toastConfig.message = 'Creating semantic vectors for matching...';
    }
    else if (eventType === 'CV_EMBEDDING_DONE') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'Embeddings Generated';
      toastConfig.message = 'CV embeddings ready for job matching';
    }
    else if (eventType === 'CV_PROCESSING_COMPLETE') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'Processing Complete';
      toastConfig.message = 'CV processed and ready for analysis';
    }
    // Job/File Events
    else if (eventType === 'FILE_UPLOADED') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'File Uploaded';
      toastConfig.message = `${data.filename || 'File'} uploaded successfully`;
    }
    else if (eventType === 'JOB_CREATED') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'Job Created';
      toastConfig.message = `Job "${data.title || 'Untitled'}" created successfully`;
    }
    else if (eventType === 'JOB_EMBEDDING_DONE') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'Job Embeddings Generated';
      toastConfig.message = 'Job description embeddings ready';
    }
    // CV Analysis Events
    else if (eventType === 'CV_ANALYSIS_STARTED') {
      toastConfig.type = 'info';
      toastConfig.icon = <Brain size={20} />;
      toastConfig.title = 'Starting Analysis';
      toastConfig.message = 'Running AI analysis on CV...';
    }
    else if (eventType === 'CV_REVIEW_COMPLETED') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'Review Complete';
      toastConfig.message = 'AI review phase completed';
    }
    else if (eventType === 'CV_ANALYSIS_COMPLETED') {
      toastConfig.type = 'success';
      toastConfig.icon = <TrendingUp size={20} />;
      toastConfig.title = 'Analysis Complete';
      toastConfig.message = `Score: ${data.final_score}/100 - ${formatDecision(data.decision)}`;
    }
    else if (eventType === 'SUGGESTION_APPLIED') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'Suggestion Applied';
      toastConfig.message = 'AI suggestion has been applied';
    }
    else if (eventType === 'FINALIZED') {
      toastConfig.type = 'success';
      toastConfig.icon = <CheckCircle size={20} />;
      toastConfig.title = 'Finalized';
      toastConfig.message = 'Job finalized and ready for use';
    }
    // Error Events
    else if (eventType.includes('ERROR')) {
      toastConfig.type = 'error';
      toastConfig.icon = <AlertCircle size={20} />;
      toastConfig.title = 'Error';
      toastConfig.message = data.error || 'An error occurred';
    }
    // Notification Event (from backend)
    else if (eventType === 'NOTIFICATION') {
      const level = data.level || 'info';
      toastConfig.type = level;
      toastConfig.title = level.charAt(0).toUpperCase() + level.slice(1);
      toastConfig.message = data.message || '';
      
      if (level === 'error') {
        toastConfig.icon = <AlertCircle size={20} />;
      } else if (level === 'success') {
        toastConfig.icon = <CheckCircle size={20} />;
      } else if (level === 'warning') {
        toastConfig.icon = <Clock size={20} />;
      }
    }

    return toastConfig;
  };

  const formatDecision = (decision) => {
    if (!decision) return 'Pending';
    return decision
      .replace(/_/g, ' ')
      .split(' ')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  const getToastStyles = (type) => {
    const baseStyles = {
      position: 'relative',
      padding: '14px 16px',
      borderRadius: '12px',
      display: 'flex',
      gap: '12px',
      alignItems: 'flex-start',
      boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
      animation: 'slideIn 0.3s ease, slideOut 0.3s ease 4.7s forwards',
      fontSize: '0.95rem',
      lineHeight: '1.4'
    };

    const typeStyles = {
      success: {
        background: 'rgba(16, 185, 129, 0.95)',
        border: '1px solid rgba(16, 185, 129, 0.5)',
        color: '#fff'
      },
      error: {
        background: 'rgba(239, 68, 68, 0.95)',
        border: '1px solid rgba(239, 68, 68, 0.5)',
        color: '#fff'
      },
      warning: {
        background: 'rgba(245, 158, 11, 0.95)',
        border: '1px solid rgba(245, 158, 11, 0.5)',
        color: '#fff'
      },
      info: {
        background: 'rgba(59, 130, 246, 0.95)',
        border: '1px solid rgba(59, 130, 246, 0.5)',
        color: '#fff'
      }
    };

    return { ...baseStyles, ...typeStyles[type] };
  };

  return (
    <>
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        @keyframes slideOut {
          from {
            transform: translateX(0);
            opacity: 1;
          }
          to {
            transform: translateX(400px);
            opacity: 0;
          }
        }
      `}</style>

      {/* Toast Notifications Stack */}
      <div style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        maxWidth: '400px',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        {toasts.map(toast => (
          <div
            key={toast.id}
            style={getToastStyles(toast.type)}
          >
            <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
              {toast.icon}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                {toast.title}
              </div>
              <div style={{ fontSize: '0.9rem', opacity: 0.95 }}>
                {toast.message}
              </div>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              style={{
                background: 'none',
                border: 'none',
                color: 'inherit',
                cursor: 'pointer',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                opacity: 0.7,
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.opacity = '1'}
              onMouseLeave={(e) => e.target.style.opacity = '0.7'}
            >
              <X size={18} />
            </button>
          </div>
        ))}
      </div>

      {/* Connection Status */}
      {!isConnected && (
        <div style={{
          position: 'fixed',
          top: '16px',
          left: '50%',
          transform: 'translateX(-50%)',
          padding: '12px 20px',
          borderRadius: '8px',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#ef4444',
          fontSize: '0.9rem',
          zIndex: 9998,
          display: 'flex',
          gap: '8px',
          alignItems: 'center'
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#ef4444',
            animation: 'pulse 2s infinite'
          }} />
          <span>Connection lost - reconnecting...</span>
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </>
  );
};

export default RealtimeNotifications;
