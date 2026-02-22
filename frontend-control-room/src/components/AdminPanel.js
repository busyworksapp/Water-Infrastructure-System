import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AdminPanel({ user, apiUrl }) {
  const [stats, setStats] = useState(null);
  const [newSensorType, setNewSensorType] = useState({ name: '', code: '', unit: '' });
  const [sensorTypeMsg, setSensorTypeMsg] = useState('');

  useEffect(() => {
    if (user?.is_super_admin) {
      fetchStats();
    }
  }, [user]);

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${apiUrl}/api/v1/admin/system/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const createSensorType = async (e) => {
    e.preventDefault();
    setSensorTypeMsg('');
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(`${apiUrl}/api/v1/admin/sensor-types`, {
        ...newSensorType,
        threshold_config: { min: 0, max: 100 }
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSensorTypeMsg('Sensor type created successfully');
      setNewSensorType({ name: '', code: '', unit: '' });
    } catch (error) {
      setSensorTypeMsg(error.response?.data?.detail || 'Error creating sensor type');
    }
  };

  if (!user?.is_super_admin) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#f44336' }}>
        Super Admin access required
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2 className="panel-header">⚙️ ADMIN PANEL</h2>
      
      {stats && (
        <div className="dashboard-grid" style={{ marginBottom: '20px' }}>
          <div className="status-card">
            <h3>MUNICIPALITIES</h3>
            <div className="status-value">{stats.municipalities}</div>
          </div>
          <div className="status-card">
            <h3>USERS</h3>
            <div className="status-value">{stats.users}</div>
          </div>
          <div className="status-card">
            <h3>TOTAL SENSORS</h3>
            <div className="status-value">{stats.sensors.total}</div>
          </div>
          <div className="status-card">
            <h3>OPEN ALERTS</h3>
            <div className="status-value">{stats.open_alerts}</div>
          </div>
        </div>
      )}
      
      <div className="panel" style={{ marginBottom: '20px' }}>
        <div className="panel-header">Create Sensor Type</div>
        <form onSubmit={createSensorType}>
          <input
            className="input-field"
            placeholder="Name"
            value={newSensorType.name}
            onChange={(e) => setNewSensorType({...newSensorType, name: e.target.value})}
            required
          />
          <input
            className="input-field"
            placeholder="Code"
            value={newSensorType.code}
            onChange={(e) => setNewSensorType({...newSensorType, code: e.target.value})}
            required
          />
          <input
            className="input-field"
            placeholder="Unit"
            value={newSensorType.unit}
            onChange={(e) => setNewSensorType({...newSensorType, unit: e.target.value})}
            required
          />
          <button type="submit" className="btn" style={{ width: '100%', marginTop: '10px' }}>
            CREATE SENSOR TYPE
          </button>
          {sensorTypeMsg && (
            <div style={{
              marginTop: '10px',
              color: sensorTypeMsg.includes('success') ? '#00ff41' : '#f44336',
              fontSize: '12px'
            }}>
              {sensorTypeMsg}
            </div>
          )}
        </form>
      </div>

      <div className="panel" style={{ marginBottom: '20px' }}>
        <div className="panel-header">Quick Links</div>
        <div style={{ padding: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <a href="/api/v1/admin/users" target="_blank" rel="noreferrer">
            <button className="btn">VIEW USERS API</button>
          </a>
          <a href="/api/v1/admin/rules" target="_blank" rel="noreferrer">
            <button className="btn">VIEW RULES API</button>
          </a>
          <a href="/api/v1/admin/logs/audit" target="_blank" rel="noreferrer">
            <button className="btn">AUDIT LOGS API</button>
          </a>
          <button className="btn" onClick={fetchStats}>REFRESH STATS</button>
        </div>
      </div>
    </div>
  );
}

export default AdminPanel;
