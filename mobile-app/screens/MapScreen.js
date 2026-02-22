import React, { useState, useEffect } from 'react';
import { API_URL } from '../config';
import { View, StyleSheet } from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';


export default function MapScreen() {
  const [sensors, setSensors] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [region] = useState({
    latitude: -26.2041,
    longitude: 28.0473,
    latitudeDelta: 0.5,
    longitudeDelta: 0.5
  });

  useEffect(() => {
    fetchMapData();
  }, []);

  const fetchMapData = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [sensorsRes, alertsRes] = await Promise.all([
        axios.get(`${API_URL}/api/v1/sensors`, { headers }),
        axios.get(`${API_URL}/api/v1/alerts?status=open&limit=50`, { headers })
      ]);
      
      setSensors(sensorsRes.data);
      setAlerts(alertsRes.data);
    } catch (error) {
      console.error('Error fetching map data:', error);
    }
  };

  return (
    <View style={styles.container}>
      <MapView style={styles.map} initialRegion={region}>
        {sensors.map(sensor => {
          if (!sensor.location?.coordinates) return null;
          const [lng, lat] = sensor.location.coordinates;
          
          return (
            <Marker
              key={sensor.id}
              coordinate={{ latitude: lat, longitude: lng }}
              title={sensor.name}
              description={`Status: ${sensor.status}`}
              pinColor={sensor.status === 'active' ? 'green' : 'red'}
            />
          );
        })}
        
        {alerts.map(alert => {
          if (!alert.location?.coordinates) return null;
          const [lng, lat] = alert.location.coordinates;
          
          return (
            <Marker
              key={alert.id}
              coordinate={{ latitude: lat, longitude: lng }}
              title={alert.title}
              description={`Severity: ${alert.severity}`}
              pinColor="orange"
            />
          );
        })}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1
  },
  map: {
    flex: 1
  }
});

