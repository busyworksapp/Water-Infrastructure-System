import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function AnalyticsDashboard({ user, apiUrl }) {
  const [trends, setTrends] = useState({ readings: [], alerts: [] });
  const [topAlerts, setTopAlerts] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const [trendsRes, topAlertsRes, healthRes] = await Promise.allSettled([
        axios.get(`${apiUrl}/api/v1/analytics/trends?days=7`, { headers }),
        axios.get(`${apiUrl}/api/v1/analytics/top-alerts?limit=5`, { headers }),
        axios.get(`${apiUrl}/api/v1/monitoring/health`, { headers })
      ]);
      
      if (trendsRes.status === 'fulfilled') setTrends(trendsRes.value.data);
      if (topAlertsRes.status === 'fulfilled') setTopAlerts(topAlertsRes.value.data);
      if (healthRes.status === 'fulfilled') setSystemHealth(healthRes.value.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2 className="panel-header">📊 ANALYTICS DASHBOARD</h2>
      
      {systemHealth && (
        <div className="panel" style={{ marginBottom: '20px' }}>
          <div className="panel-header">System Health</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px' }}>
            <div>
              <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Database</div>
              <div style={{ color: systemHealth.components.database.status === 'healthy' ? '#00ff41' : '#f44336' }}>
                {systemHealth.components.database.status.toUpperCase()}
              </div>
            </div>
            <div>
              <div style={{ color: '#7f8c8d', fontSize: '12px' }}>CPU Usage</div>
              <div style={{ color: '#00ff41' }}>
                {systemHealth.components.system.cpu_percent?.toFixed(1)}%
              </div>
            </div>
            <div>
              <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Memory</div>
              <div style={{ color: '#00ff41' }}>
                {systemHealth.components.system.memory_percent?.toFixed(1)}%
              </div>
            </div>
            <div>
              <div style={{ color: '#7f8c8d', fontSize: '12px' }}>Sensor Health</div>
              <div style={{ color: '#00ff41' }}>
                {systemHealth.components.sensors.health_score?.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
      
      <div className="panel" style={{ marginBottom: '20px' }}>
        <div className="panel-header">Readings Trend (7 Days)</div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trends.readings}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2332" />
            <XAxis dataKey="date" stroke="#00ff41" />
            <YAxis stroke="#00ff41" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a2332', border: '1px solid #00ff41' }}
              labelStyle={{ color: '#00ff41' }}
            />
            <Legend />
            <Line type="monotone" dataKey="count" stroke="#00ff41" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      <div className="panel" style={{ marginBottom: '20px' }}>
        <div className="panel-header">Alerts Trend (7 Days)</div>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={trends.alerts}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2332" />
            <XAxis dataKey="date" stroke="#00ff41" />
            <YAxis stroke="#00ff41" />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a2332', border: '1px solid #00ff41' }}
              labelStyle={{ color: '#00ff41' }}
            />
            <Legend />
            <Bar dataKey="count" fill="#f44336" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      <div className="panel">
        <div className="panel-header">Top Alert Sensors</div>
        {topAlerts.map((sensor, idx) => (
          <div key={idx} style={{
            padding: '10px',
            borderBottom: '1px solid rgba(0, 255, 65, 0.2)',
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <span>{sensor.name}</span>
            <span style={{ color: '#f44336' }}>{sensor.alert_count} alerts</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AnalyticsDashboard;
