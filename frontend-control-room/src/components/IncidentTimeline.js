import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './IncidentTimeline.css';

function IncidentTimeline({ incidentId, apiUrl, user }) {
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTimeIndex, setCurrentTimeIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hoursBefore, setHoursBefore] = useState(24);
  const [resolution, setResolution] = useState(300);

  // Auto-play animation
  useEffect(() => {
    if (!isPlaying || !timeline || !timeline.timeline_events) return;

    const interval = setInterval(() => {
      setCurrentTimeIndex(prev => {
        const next = prev + 1;
        return next >= timeline.timeline_events.length ? 0 : next;
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isPlaying, timeline]);

  useEffect(() => {
    fetchIncidentTimeline();
  }, [incidentId, hoursBefore, resolution]);

  const fetchIncidentTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const response = await axios.get(
        `${apiUrl}/api/v1/geo/incidents/${incidentId}/timeline`,
        {
          params: { hours_before: hoursBefore, resolution },
          headers
        }
      );
      
      setTimeline(response.data);
      setCurrentTimeIndex(0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load incident timeline');
      console.error('Error fetching timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="incident-timeline loading">Loading timeline...</div>;
  }

  if (error) {
    return <div className="incident-timeline error">Error: {error}</div>;
  }

  if (!timeline) {
    return <div className="incident-timeline">No timeline data available</div>;
  }

  const currentEvent = timeline.timeline_events[currentTimeIndex];
  const incidents = timeline.features;
  const currentReadings = incidents.filter(f => {
    if (!currentEvent) return false;
    return f.properties.timestamp.startsWith(currentEvent.timestamp);
  });

  return (
    <div className="incident-timeline">
      <div className="timeline-header">
        <h2>{timeline.incident.title}</h2>
        <p className="incident-description">{timeline.incident.description}</p>
        <div className="incident-meta">
          <span className="severity" data-severity={timeline.incident.severity.toLowerCase()}>
            {timeline.incident.severity}
          </span>
          <span className="timestamp">{new Date(timeline.incident.created_at).toLocaleString()}</span>
        </div>
      </div>

      <div className="controls-panel">
        <div className="control-group">
          <label>Hours Before Incident:</label>
          <select value={hoursBefore} onChange={(e) => setHoursBefore(parseInt(e.target.value))}>
            <option value={1}>1 hour</option>
            <option value={6}>6 hours</option>
            <option value={12}>12 hours</option>
            <option value={24}>24 hours</option>
            <option value={48}>48 hours</option>
            <option value={72}>72 hours</option>
          </select>
        </div>

        <div className="control-group">
          <label>Resolution:</label>
          <select value={resolution} onChange={(e) => setResolution(parseInt(e.target.value))}>
            <option value={60}>1 minute</option>
            <option value={300}>5 minutes</option>
            <option value={600}>10 minutes</option>
            <option value={1800}>30 minutes</option>
            <option value={3600}>1 hour</option>
          </select>
        </div>

        <div className="playback-controls">
          <button 
            className={`play-btn ${isPlaying ? 'playing' : ''}`}
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          <button 
            className="reset-btn"
            onClick={() => setCurrentTimeIndex(0)}
          >
            ⟲ Reset
          </button>
          <span className="event-counter">
            {currentTimeIndex + 1} / {timeline.timeline_events.length}
          </span>
        </div>
      </div>

      <div className="timeline-main">
        <div className="event-details">
          {currentEvent && (
            <>
              <div className="event-header">
                <h3>Event Time: {currentEvent.timestamp}</h3>
              </div>
              <div className="event-stats">
                <div className="stat">
                  <span className="label">Readings:</span>
                  <span className="value">{currentEvent.reading_count}</span>
                </div>
                <div className="stat">
                  <span className="label">Average Value:</span>
                  <span className="value">{currentEvent.average_value.toFixed(2)}</span>
                </div>
                <div className="stat">
                  <span className="label">Anomalies:</span>
                  <span className="value error">{currentEvent.anomaly_count}</span>
                </div>
                <div className="stat">
                  <span className="label">Active Sensors:</span>
                  <span className="value">{currentEvent.sensors.length}</span>
                </div>
              </div>

              {currentReadings.length > 0 && (
                <div className="readings-list">
                  <h4>Readings at this time:</h4>
                  <div className="readings-grid">
                    {currentReadings.map((reading, idx) => (
                      <div 
                        key={idx} 
                        className={`reading-card ${reading.properties.is_anomaly ? 'anomaly' : ''}`}
                      >
                        <div className="reading-sensor">{reading.properties.sensor_name}</div>
                        <div className="reading-value">
                          {reading.properties.value.toFixed(2)} {reading.properties.unit}
                        </div>
                        {reading.properties.is_anomaly && (
                          <div className="anomaly-score">
                            Score: {reading.properties.anomaly_score.toFixed(3)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="timeline-slider">
          <input
            type="range"
            min="0"
            max={timeline.timeline_events.length - 1}
            value={currentTimeIndex}
            onChange={(e) => {
              setCurrentTimeIndex(parseInt(e.target.value));
              setIsPlaying(false);
            }}
            className="slider"
          />
          <div className="slider-labels">
            <span>{timeline.metadata.start_time.split('T')[0]}</span>
            <span>{timeline.metadata.incident_time.split('T')[1]}</span>
          </div>
        </div>
      </div>

      {timeline.related_alerts && timeline.related_alerts.length > 0 && (
        <div className="related-alerts">
          <h3>Related Alerts During Period</h3>
          <div className="alerts-grid">
            {timeline.related_alerts.map((alert, idx) => (
              <div key={idx} className={`alert-item severity-${alert.severity.toLowerCase()}`}>
                <div className="alert-type">{alert.type}</div>
                <div className="alert-message">{alert.message}</div>
                <div className="alert-time">{new Date(alert.timestamp).toLocaleString()}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default IncidentTimeline;
