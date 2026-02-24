import React from 'react'

export default function AlertPanel({ alerts }) {
  return (
    <div className="panel">
      <h2>Active Alerts</h2>
      <div>
        {alerts.map(alert => (
          <div key={alert.id} className="alert-item">
            <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
              {alert.alert_type}
            </div>
            <div style={{ color: '#e0e0e0', marginBottom: '5px' }}>
              {alert.message}
            </div>
            <div className="alert-time">
              {new Date(alert.created_at).toLocaleString()}
            </div>
          </div>
        ))}
        {alerts.length === 0 && (
          <div style={{ textAlign: 'center', color: '#b0bec5', padding: '20px' }}>
            No active alerts
          </div>
        )}
      </div>
    </div>
  )
}
