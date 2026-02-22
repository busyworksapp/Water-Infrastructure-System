import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Dashboard({ user, onLogout, wsMessages, apiUrl }) {
  const [stats, setStats] = useState({
    totalSensors: 0,
    activeSensors: 0,
    openAlerts: 0,
    criticalAlerts: 0,
    systemHealth: 100
  });
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [liveReadings, setLiveReadings] = useState([]);
  const [systemStatus, setSystemStatus] = useState('operational');
  const navigate = useNavigate();
  const lastMsgRef = useRef(null);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!wsMessages || wsMessages.length === 0) return;
    const latest = wsMessages[0];
    if (latest === lastMsgRef.current) return;
    lastMsgRef.current = latest;

    if (latest.type === 'sensor_reading') {
      setLiveReadings(prev => [latest.data, ...prev.slice(0, 19)]);
    } else if (latest.type === 'alert') {
      setRecentAlerts(prev => [latest.data, ...prev.slice(0, 19)]);
      setStats(prev => ({
        ...prev,
        openAlerts: prev.openAlerts + 1,
        criticalAlerts: latest.data.severity === 'critical' ? prev.criticalAlerts + 1 : prev.criticalAlerts
      }));
    }
  }, [wsMessages]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const [sensorsRes, alertsRes, statsRes, healthRes] = await Promise.allSettled([
        axios.get(`${apiUrl}/api/v1/sensors`, { headers }),
        axios.get(`${apiUrl}/api/v1/alerts?limit=15`, { headers }),
        axios.get(`${apiUrl}/api/v1/alerts/statistics/summary`, { headers }),
        axios.get(`${apiUrl}/api/v1/monitoring/health`, { headers })
      ]);

      if (sensorsRes.status === 'fulfilled') {
        const sensors = sensorsRes.value.data;
        setStats(prev => ({
          ...prev,
          totalSensors: sensors.length,
          activeSensors: sensors.filter(s => s.status === 'active').length
        }));
      }

      if (statsRes.status === 'fulfilled') {
        const s = statsRes.value.data;
        setStats(prev => ({
          ...prev,
          openAlerts: s.open || 0,
          criticalAlerts: s.critical || 0
        }));
      }

      if (alertsRes.status === 'fulfilled') {
        setRecentAlerts(alertsRes.value.data);
      }

      if (healthRes.status === 'fulfilled') {
        setSystemStatus(healthRes.value.data.status);
      }
    } catch (error) {
      console.error('Dashboard fetch error:', error);
    }
  };

  const getStatusColor = (status) => {
    if (status === 'healthy' || status === 'operational') return '#00ff41';
    if (status === 'warning') return '#ffeb3b';
    return '#f44336';
  };

  const getSeverityColor = (severity) => {
    const map = { critical: '#f44336', high: '#ff9800', medium: '#ffeb3b', low: '#4caf50', info: '#2196f3' };
    return map[severity] || '#7f8c8d';
  };

  return (
    <div className="dashboard-container">
      <div className="header">
        <h1>NATIONAL WATER INFRASTRUCTURE MONITORING SYSTEM</h1>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <span style={{ color: getStatusColor(systemStatus), fontSize: '12px' }}>
            ● SYSTEM {systemStatus.toUpperCase()}
          </span>
          <span style={{ color: '#7f8c8d' }}>{user?.username}</span>
          {user?.is_super_admin && (
            <button className="btn" onClick={() => navigate('/admin')} style={{ fontSize: '12px' }}>ADMIN</button>
          )}
          <button className="btn" onClick={onLogout}>LOGOUT</button>
        </div>
      </div>

      <div className="sidebar">
        <div className="nav-item active" onClick={() => navigate('/dashboard')}>DASHBOARD</div>
        <div className="nav-item" onClick={() => navigate('/sensors')}>SENSORS</div>
        <div className="nav-item" onClick={() => navigate('/alerts')}>ALERTS</div>
        <div className="nav-item" onClick={() => navigate('/map')}>GIS MAP</div>
        <div className="nav-item" onClick={() => navigate('/analytics')}>ANALYTICS</div>
        {user?.is_super_admin && (
          <div className="nav-item" onClick={() => navigate('/admin')}>ADMIN PANEL</div>
        )}
      </div>

      <div className="main-content">
        <div className="dashboard-grid">
          <div className="status-card">
            <h3>TOTAL SENSORS</h3>
            <div className="status-value">{stats.totalSensors}</div>
          </div>
          <div className="status-card">
            <h3>ACTIVE SENSORS</h3>
            <div className="status-value">
              <span className="status-indicator status-green"></span>
              {stats.activeSensors}
            </div>
          </div>
          <div className="status-card">
            <h3>OPEN ALERTS</h3>
            <div className="status-value">
              <span className="status-indicator" style={{ background: stats.openAlerts > 0 ? '#ffeb3b' : '#00ff41' }}></span>
              {stats.openAlerts}
            </div>
          </div>
          <div className="status-card">
            <h3>CRITICAL ALERTS</h3>
            <div className="status-value">
              <span className="status-indicator" style={{ background: stats.criticalAlerts > 0 ? '#f44336' : '#00ff41' }}></span>
              {stats.criticalAlerts}
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="panel">
            <div className="panel-header">RECENT ALERTS</div>
            {recentAlerts.length === 0 ? (
              <div style={{ color: '#7f8c8d', textAlign: 'center', padding: '20px' }}>No recent alerts</div>
            ) : (
              <div style={{ maxHeight: '320px', overflowY: 'auto' }}>
                {recentAlerts.map(alert => (
                  <div key={alert.id} style={{
                    padding: '10px',
                    borderBottom: '1px solid rgba(0,255,65,0.15)',
                    borderLeft: `3px solid ${getSeverityColor(alert.severity)}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong style={{ fontSize: '13px' }}>{alert.title}</strong>
                      <span style={{ color: getSeverityColor(alert.severity), fontSize: '11px', fontWeight: 'bold' }}>
                        {(alert.severity || '').toUpperCase()}
                      </span>
                    </div>
                    <div style={{ color: '#7f8c8d', fontSize: '11px', marginTop: '3px' }}>
                      {alert.alert_type} | {alert.status} | {new Date(alert.created_at || alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="panel">
            <div className="panel-header">LIVE SENSOR READINGS</div>
            {liveReadings.length === 0 ? (
              <div style={{ color: '#7f8c8d', textAlign: 'center', padding: '20px' }}>
                Waiting for sensor data...
              </div>
            ) : (
              <div style={{ maxHeight: '320px', overflowY: 'auto' }}>
                {liveReadings.map((reading, idx) => (
                  <div key={idx} style={{
                    padding: '8px 10px',
                    borderBottom: '1px solid rgba(0,255,65,0.1)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span style={{ fontSize: '12px' }}>{reading.device_id || reading.sensor_id}</span>
                    <span style={{ color: reading.is_anomaly ? '#f44336' : '#00ff41', fontWeight: 'bold' }}>
                      {reading.value} {reading.is_anomaly && '⚠'}
                    </span>
                    <span style={{ color: '#7f8c8d', fontSize: '11px' }}>
                      {new Date(reading.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
