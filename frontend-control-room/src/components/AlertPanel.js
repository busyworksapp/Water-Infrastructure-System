import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

function AlertPanel({ user, wsMessages, apiUrl }) {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');
  const lastMsgRef = useRef(null);

  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    if (!wsMessages || wsMessages.length === 0) return;
    const latest = wsMessages[0];
    if (latest === lastMsgRef.current) return;
    lastMsgRef.current = latest;

    if (latest.type === 'alert') {
      setAlerts(prev => [latest.data, ...prev]);
    }
  }, [wsMessages]);

  const fetchAlerts = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${apiUrl || 'http://localhost:8000'}/api/v1/alerts?limit=100`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(response.data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${apiUrl || 'http://localhost:8000'}/api/v1/alerts/${alertId}/acknowledge`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchAlerts();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const resolveAlert = async (alertId) => {
    const notes = prompt('Enter resolution notes:');
    if (!notes) return;
    
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `${apiUrl || 'http://localhost:8000'}/api/v1/alerts/${alertId}/resolve`,
        { resolution_notes: notes },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchAlerts();
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filter === 'all') return true;
    if (filter === 'open') return alert.status === 'open';
    if (filter === 'critical') return alert.severity === 'critical';
    return true;
  });

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 className="panel-header">🚨 ALERT MANAGEMENT</h2>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            className="btn" 
            onClick={() => setFilter('all')}
            style={{ opacity: filter === 'all' ? 1 : 0.5 }}
          >
            ALL
          </button>
          <button 
            className="btn" 
            onClick={() => setFilter('open')}
            style={{ opacity: filter === 'open' ? 1 : 0.5 }}
          >
            OPEN
          </button>
          <button 
            className="btn" 
            onClick={() => setFilter('critical')}
            style={{ opacity: filter === 'critical' ? 1 : 0.5 }}
          >
            CRITICAL
          </button>
        </div>
      </div>
      
      <div>
        {filteredAlerts.map(alert => (
          <div key={alert.id} className={`alert-item alert-${alert.severity}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div>
                <strong style={{ fontSize: '16px' }}>{alert.title}</strong>
                <div style={{ color: '#7f8c8d', fontSize: '12px', marginTop: '5px' }}>
                  {alert.description}
                </div>
              </div>
              
              <div style={{ textAlign: 'right' }}>
                <div style={{ 
                  color: alert.severity === 'critical' ? '#f44336' : 
                         alert.severity === 'high' ? '#ff9800' : '#ffeb3b',
                  fontWeight: 'bold',
                  marginBottom: '5px'
                }}>
                  {alert.severity.toUpperCase()}
                </div>
                <div style={{ color: '#7f8c8d', fontSize: '11px' }}>
                  {new Date(alert.created_at).toLocaleString()}
                </div>
              </div>
            </div>
            
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '10px',
              paddingTop: '10px',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <div style={{ color: '#7f8c8d', fontSize: '12px' }}>
                Type: {alert.alert_type} | Status: {alert.status}
              </div>
              
              <div style={{ display: 'flex', gap: '10px' }}>
                {alert.status === 'open' && (
                  <button 
                    className="btn" 
                    style={{ padding: '5px 15px', fontSize: '12px' }}
                    onClick={() => acknowledgeAlert(alert.id)}
                  >
                    ACKNOWLEDGE
                  </button>
                )}
                
                {(alert.status === 'open' || alert.status === 'acknowledged') && (
                  <button 
                    className="btn" 
                    style={{ padding: '5px 15px', fontSize: '12px' }}
                    onClick={() => resolveAlert(alert.id)}
                  >
                    RESOLVE
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AlertPanel;
