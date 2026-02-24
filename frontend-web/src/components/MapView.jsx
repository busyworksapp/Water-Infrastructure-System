import React, { useEffect, useRef } from 'react'
import L from 'leaflet'

export default function MapView({ sensors, token }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)

  useEffect(() => {
    if (!mapInstance.current) {
      mapInstance.current = L.map(mapRef.current).setView([-26.2041, 28.0473], 10)
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapInstance.current)
    }

    mapInstance.current.eachLayer(layer => {
      if (layer instanceof L.Marker) {
        mapInstance.current.removeLayer(layer)
      }
    })

    sensors.forEach(sensor => {
      if (sensor.latitude && sensor.longitude) {
        const color = sensor.is_active ? 'green' : 'red'
        const marker = L.circleMarker([sensor.latitude, sensor.longitude], {
          radius: 8,
          fillColor: color,
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(mapInstance.current)

        marker.bindPopup(`
          <strong>${sensor.name}</strong><br/>
          Status: ${sensor.is_active ? 'Online' : 'Offline'}<br/>
          Value: ${sensor.last_reading?.value?.toFixed(2) || '--'} ${sensor.unit || ''}
        `)
      }
    })

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove()
        mapInstance.current = null
      }
    }
  }, [sensors])

  return (
    <div className="panel">
      <h2>Sensor Map</h2>
      <div ref={mapRef} className="map-container"></div>
    </div>
  )
}
