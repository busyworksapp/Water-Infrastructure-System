import React, { useState, useEffect } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import SensorGrid from './SensorGrid'
import AlertPanel from './AlertPanel'
import MapView from './MapView'

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export default function Dashboard({ user, onLogout, token }) {
  const [activeView, setActiveView] = useState('overview')
  const [stats, setStats] = useState({
    totalSensors: 0,
    activeSensors: 0,
    activeAlerts: 0,
    criticalAlerts: 0
  })
  const [sensors, setSensors] = useState([])
  const [alerts, setAlerts] = useState([])
  const [ws, setWs] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchStats()
    fetchSensors()
    fetchAlerts()
    connectWebSocket()

    const interval = setInterval(() => {
      fetchStats()
      fetchSensors()
      fetchAlerts()
    }, 30000)

    return () => {
      clearInterval(interval)
      if (ws) ws.close()
    }
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/sensors/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  const fetchSensors = async () => {
    try {
      const response = await fetch(`${API_URL}/sensors?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setSensors(data)
      }
    } catch (err) {
      console.error('Failed to fetch sensors:', err)
    }
  }

  const fetchAlerts = async () => {
    try {
      const response = await fetch(`${API_URL}/alerts?status=active&limit=20`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setAlerts(data)
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err)
    }
  }

  const connectWebSocket = () => {
    const websocket = new WebSocket(`${WS_URL}/ws?token=${token}`)
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'sensor_reading') {
        fetchSensors()
      } else if (data.type === 'alert') {
        fetchAlerts()
        fetchStats()
      }
    }

    websocket.onerror = () => console.error('WebSocket error')
    websocket.onclose = () => setTimeout(connectWebSocket, 5000)
    
    setWs(websocket)
  }

  return (
    <div className="dashboard">
      <div className="sidebar">
        <h2>🌊 RandWater</h2>
        <div className="nav-item" onClick={() => setActiveView('overview')}>
          📊 Overview
        </div>
        <div className="nav-item" onClick={() => setActiveView('sensors')}>
          📡 Sensors
        </div>
        <div className="nav-item" onClick={() => setActiveView('alerts')}>
          🚨 Alerts
        </div>
        <div className="nav-item" onClick={() => setActiveView('map')}>
          🗺️ Map
        </div>
      </div>

      <div className="main-content">
        <div className="header">
          <h1>Control Room Dashboard</h1>
          <div className="user-info">
            <span>{user?.username || 'User'}</span>
            <button className="btn-logout" onClick={onLogout}>Logout</button>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-card good">
            <h3>Total Sensors</h3>
            <div className="stat-value">{stats.totalSensors}</div>
          </div>
          <div className="stat-card good">
            <h3>Active Sensors</h3>
            <div className="stat-value">{stats.activeSensors}</div>
          </div>
          <div className="stat-card warning">
            <h3>Active Alerts</h3>
            <div className="stat-value">{stats.activeAlerts}</div>
          </div>
          <div className="stat-card critical">
            <h3>Critical Alerts</h3>
            <div className="stat-value">{stats.criticalAlerts}</div>
          </div>
        </div>

        {activeView === 'overview' && (
          <div className="content-grid">
            <SensorGrid sensors={sensors.slice(0, 10)} />
            <AlertPanel alerts={alerts.slice(0, 10)} />
          </div>
        )}

        {activeView === 'sensors' && <SensorGrid sensors={sensors} />}
        {activeView === 'alerts' && <AlertPanel alerts={alerts} />}
        {activeView === 'map' && <MapView sensors={sensors} token={token} />}
      </div>
    </div>
  )
}
