import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import axios from 'axios';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const alertIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

function MapView({ user, wsMessages, apiUrl }) {
  const [sensors, setSensors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [pipelines, setPipelines] = useState([]);
  const [center] = useState([-26.2041, 28.0473]);
  const lastMsgRef = useRef(null);

  useEffect(() => {
    fetchMapData();
  }, []);

  useEffect(() => {
    if (!wsMessages || wsMessages.length === 0) return;
    const latest = wsMessages[0];
    if (latest === lastMsgRef.current) return;
    lastMsgRef.current = latest;

    if (latest.type === 'alert') {
      setAlerts(prev => [latest.data, ...prev.slice(0, 49)]);
    }
  }, [wsMessages]);

  const fetchMapData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      const [sensorsRes, alertsRes, pipelinesRes] = await Promise.allSettled([
        axios.get(`${apiUrl}/api/v1/sensors`, { headers }),
        axios.get(`${apiUrl}/api/v1/alerts?status=open&limit=50`, { headers }),
        axios.get(`${apiUrl}/api/v1/pipelines`, { headers })
      ]);

      if (sensorsRes.status === 'fulfilled') setSensors(sensorsRes.value.data);
      if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value.data);
      if (pipelinesRes.status === 'fulfilled') setPipelines(pipelinesRes.value.data);
    } catch (error) {
      console.error('Error fetching map data:', error);
    }
  };

  const getPipelineCoords = (geometry) => {
    if (!geometry || geometry.type !== 'LineString') return [];
    return geometry.coordinates.map(([lng, lat]) => [lat, lng]);
  };

  const getSeverityColor = (severity) => {
    const map = { critical: '#f44336', high: '#ff9800', medium: '#ffeb3b', low: '#4caf50', info: '#2196f3' };
    return map[severity] || '#f44336';
  };

  return (
    <div style={{ padding: '20px', height: 'calc(100vh - 80px)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h2 className="panel-header" style={{ margin: 0 }}>GIS PIPELINE MAPPING</h2>
        <div style={{ fontSize: '12px', color: '#7f8c8d' }}>
          {sensors.length} sensors &bull; {alerts.length} active alerts &bull; {pipelines.length} pipelines
        </div>
      </div>

      <div style={{ height: 'calc(100% - 50px)', border: '2px solid #00ff41', borderRadius: '8px', overflow: 'hidden' }}>
        <MapContainer
          center={center}
          zoom={10}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; OpenStreetMap contributors'
          />

          {pipelines.map(pipeline => {
            const coords = getPipelineCoords(pipeline.geometry);
            if (coords.length < 2) return null;
            return (
              <Polyline
                key={pipeline.id}
                positions={coords}
                color={pipeline.status === 'operational' ? '#00ff41' : pipeline.status === 'damaged' ? '#f44336' : '#ffeb3b'}
                weight={3}
              >
                <Popup>
                  <div style={{ color: '#000' }}>
                    <strong>{pipeline.name}</strong><br />
                    Status: {pipeline.status}<br />
                    Material: {pipeline.material || 'N/A'}<br />
                    Length: {pipeline.length_km ? `${pipeline.length_km} km` : 'N/A'}
                  </div>
                </Popup>
              </Polyline>
            );
          })}

          {sensors.map(sensor => {
            if (!sensor.location?.coordinates) return null;
            const [lng, lat] = sensor.location.coordinates;
            return (
              <Marker key={sensor.id} position={[lat, lng]}>
                <Popup>
                  <div style={{ color: '#000' }}>
                    <strong>{sensor.name}</strong><br />
                    Type: {sensor.sensor_type}<br />
                    Status: {sensor.status}<br />
                    Device ID: {sensor.device_id}<br />
                    Battery: {sensor.battery_level != null ? `${sensor.battery_level}%` : 'N/A'}
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {alerts.map(alert => {
            if (!alert.location?.coordinates) return null;
            const [lng, lat] = alert.location.coordinates;
            return (
              <Circle
                key={alert.id}
                center={[lat, lng]}
                radius={200}
                color={getSeverityColor(alert.severity)}
                fillOpacity={0.4}
              >
                <Popup>
                  <div style={{ color: '#000' }}>
                    <strong style={{ color: '#f44336' }}>{alert.title}</strong><br />
                    Severity: {alert.severity}<br />
                    Type: {alert.alert_type}<br />
                    Time: {new Date(alert.created_at).toLocaleString()}
                  </div>
                </Popup>
              </Circle>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}

export default MapView;
