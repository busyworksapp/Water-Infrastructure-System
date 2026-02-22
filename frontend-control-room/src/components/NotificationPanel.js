import React, { useState, useEffect } from 'react';
import './NotificationPanel.css';

const NotificationPanel = ({ wsUrl, token }) => {
  const [notifications, setNotifications] = useState([]);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    const websocket = new WebSocket(`${wsUrl}?token=${token}`);
    
    websocket.onopen = () => {
      console.log('Notification WebSocket connected');
    };
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'alert') {
        addNotification({
          id: Date.now(),
          severity: data.severity,
          message: data.message,
          sensor: data.sensor_name,
          timestamp: new Date().toISOString()
        });
        
        if (data.severity === 'critical') {
          playAlertSound();
        }
      }
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    setWs(websocket);
    
    return () => {
      if (websocket) websocket.close();
    };
  }, [wsUrl, token]);

  const addNotification = (notification) => {
    setNotifications(prev => [notification, ...prev].slice(0, 50));
  };

  const playAlertSound = () => {
    const audio = new Audio('/alert-sound.mp3');
    audio.play().catch(e => console.log('Audio play failed:', e));
  };

  const clearNotification = (id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const getSeverityIcon = (severity) => {
    const icons = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🟢'
    };
    return icons[severity] || '🔵';
  };

  return (
    <div className="notification-panel">
      <div className="notification-header">
        <h3>🔔 Live Notifications</h3>
        <button onClick={clearAll} className="clear-btn">Clear All</button>
      </div>
      
      <div className="notification-list">
        {notifications.length === 0 ? (
          <div className="no-notifications">No new notifications</div>
        ) : (
          notifications.map(notif => (
            <div key={notif.id} className={`notification-item ${notif.severity}`}>
              <div className="notif-icon">{getSeverityIcon(notif.severity)}</div>
              <div className="notif-content">
                <div className="notif-message">{notif.message}</div>
                <div className="notif-meta">
                  <span>{notif.sensor}</span>
                  <span>{new Date(notif.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
              <button onClick={() => clearNotification(notif.id)} className="close-btn">×</button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default NotificationPanel;
