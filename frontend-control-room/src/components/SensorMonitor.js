import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

function SensorMonitor({ user, wsMessages, apiUrl }) {
  const [sensors, setSensors] = useState([]);
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [readings, setReadings] = useState([]);
  const [loading, setLoading] = useState(false);
  const lastMsgRef = useRef(null);

  useEffect(() => {
    fetchSensors();
  }, []);

  useEffect(() => {
    if (!wsMessages || wsMessages.length === 0) return;
    const latest = wsMessages[0];
    if (latest === lastMsgRef.current) return;
    lastMsgRef.current = latest;

    if (latest.type === 'sensor_reading') {
      const data = latest.data;
      setSensors(prev => prev.map(s =>
        s.id === data.sensor_id
          ? { ...s, last_reading: data.value, last_reading_at: data.timestamp }
          : s
      ));
    }
  }, [wsMessages]);

  const fetchSensors = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${apiUrl}/api/v1/sensors`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSensors(response.data);
    } catch (error) {
      console.error('Error fetching sensors:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSensorReadings = async (sensorId) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.get(`${apiUrl}/api/v1/sensors/${sensorId}/readings?hours=24`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setReadings(response.data);
    } catch (error) {
      console.error('Error fetching readings:', error);
    }
  };

  const handleSensorClick = (sensor) => {
    setSelectedSensor(sensor);
    fetchSensorReadings(sensor.id);
  };

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 className="panel-header" style={{ margin: 0 }}>SENSOR MONITORING</h2>
        <button className="btn" onClick={fetchSensors} disabled={loading}>
          {loading ? 'LOADING...' : 'REFRESH'}
        </button>
      </div>

      {loading && sensors.length === 0 ? (
        <div style={{ color: '#7f8c8d', textAlign: 'center', padding: '40px' }}>Loading sensors...</div>
      ) : (
        <div className="sensor-grid">
          {sensors.map(sensor => (
            <div
              key={sensor.id}
              className="sensor-card"
              onClick={() => handleSensorClick(sensor)}
              style={{
                cursor: 'pointer',
                borderColor: selectedSensor?.id === sensor.id ? '#00ff41' : 'rgba(0,255,65,0.3)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <strong style={{ fontSize: '13px' }}>{sensor.name}</strong>
                <span className={`status-indicator status-${
                  sensor.status === 'active' ? 'green' :
                  sensor.status === 'maintenance' ? 'yellow' : 'red'
                }`}></span>
              </div>

              <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>
                ID: {sensor.device_id}
              </div>
              <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>
                Type: {sensor.sensor_type}
              </div>
              <div style={{ color: '#7f8c8d', fontSize: '12px', marginBottom: '4px' }}>
                Protocol: {(sensor.protocol || '').toUpperCase()}
              </div>

              {sensor.battery_level != null && (
                <div style={{ fontSize: '12px', marginBottom: '3px' }}>
                  Battery: {sensor.battery_level}%
                </div>
              )}
              {sensor.signal_strength != null && (
                <div style={{ fontSize: '12px', marginBottom: '3px' }}>
                  Signal: {sensor.signal_strength}%
                </div>
              )}
              {sensor.last_reading_at && (
                <div style={{ color: '#7f8c8d', fontSize: '11px', marginTop: '8px' }}>
                  Last: {new Date(sensor.last_reading_at).toLocaleString()}
                </div>
              )}
              {sensor.last_reading != null && (
                <div style={{ color: '#00ff41', fontWeight: 'bold', fontSize: '14px', marginTop: '4px' }}>
                  {sensor.last_reading}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedSensor && (
        <div className="panel" style={{ marginTop: '20px' }}>
          <div className="panel-header">
            READINGS: {selectedSensor.name}
          </div>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {readings.length === 0 ? (
              <div style={{ color: '#7f8c8d', textAlign: 'center', padding: '20px' }}>No readings available</div>
            ) : (
              readings.map(reading => (
                <div
                  key={reading.id}
                  style={{
                    padding: '10px',
                    borderBottom: '1px solid rgba(0, 255, 65, 0.2)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    background: reading.is_anomaly ? 'rgba(244, 67, 54, 0.1)' : 'transparent'
                  }}
                >
                  <span style={{ fontSize: '12px' }}>{new Date(reading.timestamp).toLocaleString()}</span>
                  <span style={{ color: reading.is_anomaly ? '#f44336' : '#00ff41', fontWeight: 'bold' }}>
                    {reading.value} {reading.unit} {reading.is_anomaly && '!'}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default SensorMonitor;
