import React from 'react'

export default function SensorGrid({ sensors }) {
  return (
    <div className="panel">
      <h2>Sensor Status</h2>
      <div className="sensor-grid">
        {sensors.map(sensor => (
          <div key={sensor.id} className={`sensor-item ${sensor.status === 'critical' ? 'critical' : sensor.status === 'warning' ? 'warning' : ''}`}>
            <div className="sensor-header">
              <span className="sensor-name">{sensor.name}</span>
              <span className={`sensor-status ${sensor.is_active ? 'status-online' : 'status-offline'}`}>
                {sensor.is_active ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
            <div className="sensor-value">
              {sensor.last_reading?.value?.toFixed(2) || '--'} {sensor.unit || ''}
            </div>
            <div style={{ color: '#b0bec5', fontSize: '12px' }}>
              {sensor.location || 'Unknown Location'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
