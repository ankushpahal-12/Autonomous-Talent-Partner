import { useEffect, useState, useRef, useCallback } from 'react';

export const useWebSocket = (sessionId) => {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState([]);
  const [currentEvent, setCurrentEvent] = useState(null);
  const [progress, setProgress] = useState({});
  const ws = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = useRef(1000);

  // Connect to WebSocket
  useEffect(() => {
    if (!sessionId) return;

    const connectWebSocket = () => {
      const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000'}/api/v1/ws/${sessionId}`;
      
      try {
        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
          console.log(`[WebSocket] Connected with session: ${sessionId}`);
          setIsConnected(true);
          reconnectAttempts.current = 0; // Reset reconnect attempts on success
          reconnectDelay.current = 1000; // Reset delay
        };

        ws.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            console.log('[WebSocket] Received:', message);

            // Ignore ping messages
            if (message.event === 'PING') {
              console.debug('[WebSocket] Ping received');
              return;
            }

            // Handle different event types
            if (message.event === 'TIMELINE_HISTORY') {
              // Restore previous event history
              setEvents(message.data.history || []);
            } else if (message.event === 'PROGRESS_UPDATE') {
              // Update progress tracking
              const task = message.data.task;
              setProgress(prev => ({
                ...prev,
                [task]: message.data
              }));
            } else {
              // Store event in history
              setEvents(prev => [...prev, message]);
              setCurrentEvent(message);
            }
          } catch (err) {
            console.error('[WebSocket] Error parsing message:', err);
          }
        };

        ws.current.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          setIsConnected(false);
        };

        ws.current.onclose = () => {
          console.log('[WebSocket] Disconnected');
          setIsConnected(false);
          
          // Attempt to reconnect with exponential backoff
          if (reconnectAttempts.current < maxReconnectAttempts) {
            reconnectAttempts.current++;
            console.log(`[WebSocket] Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts}) in ${reconnectDelay.current}ms`);
            setTimeout(() => {
              connectWebSocket();
            }, reconnectDelay.current);
            
            // Exponential backoff: increase delay for next attempt (max 30s)
            reconnectDelay.current = Math.min(reconnectDelay.current * 1.5, 30000);
          } else {
            console.error('[WebSocket] Max reconnection attempts reached');
          }
        };
      } catch (err) {
        console.error('[WebSocket] Connection failed:', err);
        setIsConnected(false);
      }
    };

    // Initial connection attempt
    connectWebSocket();

    // Cleanup on component unmount
    return () => {
      if (ws.current && ws.current.readyState === WebSocket.OPEN) {
        ws.current.close();
      }
    };
  }, [sessionId]);

  // Get latest progress for a specific task
  const getProgress = useCallback((taskName) => {
    return progress[taskName] || { progress: 0, task: taskName };
  }, [progress]);

  // Get all events of a specific type
  const getEventsByType = useCallback((eventType) => {
    return events.filter(e => e.event === eventType);
  }, [events]);

  // Get last event of a specific type
  const getLastEventByType = useCallback((eventType) => {
    const filtered = events.filter(e => e.event === eventType);
    return filtered.length > 0 ? filtered[filtered.length - 1] : null;
  }, [events]);

  // Clear event history
  const clearEvents = useCallback(() => {
    setEvents([]);
    setCurrentEvent(null);
    setProgress({});
  }, []);

  return {
    isConnected,
    events,
    currentEvent,
    progress,
    getProgress,
    getEventsByType,
    getLastEventByType,
    clearEvents
  };
};
