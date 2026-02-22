import React, { useState, useEffect, useCallback, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import SensorMonitor from './components/SensorMonitor';
import AlertPanel from './components/AlertPanel';
import MapView from './components/MapView';
import AdminPanel from './components/AdminPanel';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [wsMessages, setWsMessages] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connectWebSocket = useCallback((municipalityId) => {
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      wsRef.current.close();
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }
    const wsId = municipalityId || 'global';
    const ws = new WebSocket(`${WS_URL}/ws/${wsId}?token=${encodeURIComponent(token)}&replay_limit=50`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setWsMessages(prev => [message, ...prev.slice(0, 99)]);
      } catch (e) {
        console.warn('WS parse error:', e);
      }
    };

    ws.onerror = (error) => {
      console.warn('WebSocket error:', error);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed. Reconnecting in 5s...');
      reconnectTimeoutRef.current = setTimeout(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
          connectWebSocket(municipalityId);
        }
      }, 5000);
    };

    wsRef.current = ws;
    return ws;
  }, []);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');

    if (token && userData) {
      const parsedUser = JSON.parse(userData);
      setIsAuthenticated(true);
      setUser(parsedUser);
      connectWebSocket(parsedUser.municipality_id);
    }

    return () => disconnectWebSocket();
  }, [connectWebSocket, disconnectWebSocket]);

  const handleLogin = (token, userData) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setIsAuthenticated(true);
    setUser(userData);
    connectWebSocket(userData.municipality_id);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setUser(null);
    setWsMessages([]);
    disconnectWebSocket();
  };

  const wsProps = {
    ws: wsRef.current,
    wsMessages,
    apiUrl: API_URL
  };

  return (
    <Router>
      <div className="app-container">
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? <Navigate to="/dashboard" /> : <Login onLogin={handleLogin} apiUrl={API_URL} />
            }
          />
          <Route
            path="/dashboard"
            element={
              isAuthenticated ? <Dashboard user={user} onLogout={handleLogout} {...wsProps} /> : <Navigate to="/login" />
            }
          />
          <Route
            path="/sensors"
            element={
              isAuthenticated ? <SensorMonitor user={user} {...wsProps} /> : <Navigate to="/login" />
            }
          />
          <Route
            path="/alerts"
            element={
              isAuthenticated ? <AlertPanel user={user} {...wsProps} /> : <Navigate to="/login" />
            }
          />
          <Route
            path="/map"
            element={
              isAuthenticated ? <MapView user={user} {...wsProps} /> : <Navigate to="/login" />
            }
          />
          <Route
            path="/analytics"
            element={
              isAuthenticated ? <AnalyticsDashboard user={user} {...wsProps} /> : <Navigate to="/login" />
            }
          />
          <Route
            path="/admin"
            element={
              isAuthenticated && user?.is_super_admin ? <AdminPanel user={user} {...wsProps} /> : <Navigate to="/dashboard" />
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
