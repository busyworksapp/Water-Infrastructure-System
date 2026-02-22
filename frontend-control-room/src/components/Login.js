import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/v1/auth/login`, {
        username,
        password
      });

      const { access_token, user } = response.data;
      onLogin(access_token, user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 style={{ 
          textAlign: 'center', 
          marginBottom: '30px',
          color: '#00ff41',
          textTransform: 'uppercase',
          letterSpacing: '2px'
        }}>
          🌊 WATER MONITORING
        </h1>
        <h2 style={{ 
          textAlign: 'center', 
          marginBottom: '30px',
          color: '#7f8c8d',
          fontSize: '14px'
        }}>
          CONTROL ROOM ACCESS
        </h2>
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            className="input-field"
            placeholder="USERNAME"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          
          <input
            type="password"
            className="input-field"
            placeholder="PASSWORD"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          
          {error && (
            <div style={{ 
              color: '#f44336', 
              marginTop: '10px',
              textAlign: 'center',
              fontSize: '12px'
            }}>
              {error}
            </div>
          )}
          
          <button 
            type="submit" 
            className="btn" 
            style={{ width: '100%', marginTop: '20px' }}
            disabled={loading}
          >
            {loading ? 'AUTHENTICATING...' : 'LOGIN'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;
