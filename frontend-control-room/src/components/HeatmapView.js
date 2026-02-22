import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const HeatmapView = ({ sensors, alerts }) => {
  const [center] = useState([-26.2041, 28.0473]);
  const [zoom] = useState(6);

  const getSeverityColor = (severity) => {
    const colors = {
      critical: '#ff0000',
      high: '#ff6600',
      medium: '#ffcc00',
      low: '#00ff00',
      normal: '#0088ff'
    };
    return colors[severity] || colors.normal;
  };

  const getSensorStatus = (sensor) => {
    const sensorAlerts = alerts.filter(a => a.sensor_id === sensor.id && !a.resolved);
    if (sensorAlerts.length === 0) return 'normal';
    
    const severities = sensorAlerts.map(a => a.severity);
    if (severities.includes('critical')) return 'critical';
    if (severities.includes('high')) return 'high';
    if (severities.includes('medium')) return 'medium';
    return 'low';
  };

  return (
    <div style={{ height: '100%', width: '100%' }}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        
        {sensors.map(sensor => {
          if (!sensor.latitude || !sensor.longitude) return null;
          
          const status = getSensorStatus(sensor);
          const color = getSeverityColor(status);
          
          return (
            <CircleMarker
              key={sensor.id}
              center={[sensor.latitude, sensor.longitude]}
              radius={8}
              fillColor={color}
              color="#fff"
              weight={2}
              opacity={1}
              fillOpacity={0.8}
            >
              <Popup>
                <div style={{ color: '#000' }}>
                  <h3>{sensor.name}</h3>
                  <p>Type: {sensor.type}</p>
                  <p>Status: {status.toUpperCase()}</p>
                  <p>Last Reading: {sensor.last_value || 'N/A'}</p>
                  <p>Municipality: {sensor.municipality_name}</p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default HeatmapView;
