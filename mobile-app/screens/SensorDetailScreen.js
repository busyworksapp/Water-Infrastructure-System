import React, { useState, useEffect } from 'react';
import { API_URL } from '../config';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';


export default function SensorDetailScreen({ route, navigation }) {
  const { sensorId } = route.params;
  const [sensor, setSensor] = useState(null);
  const [readings, setReadings] = useState([]);

  useEffect(() => {
    fetchSensorDetails();
    fetchReadings();
  }, []);

  const fetchSensorDetails = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/api/v1/sensors/${sensorId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSensor(response.data);
    } catch (error) {
      console.error('Error fetching sensor:', error);
    }
  };

  const fetchReadings = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await axios.get(`${API_URL}/api/v1/sensors/${sensorId}/readings?hours=24&limit=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setReadings(response.data);
    } catch (error) {
      console.error('Error fetching readings:', error);
    }
  };

  if (!sensor) {
    return (
      <View style={styles.container}>
        <Text style={styles.loading}>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>{sensor.name}</Text>
        <Text style={styles.subtitle}>Device ID: {sensor.device_id}</Text>
        
        <View style={styles.infoRow}>
          <Text style={styles.label}>Status:</Text>
          <Text style={[styles.value, { color: sensor.status === 'active' ? '#00ff41' : '#f44336' }]}>
            {sensor.status.toUpperCase()}
          </Text>
        </View>
        
        <View style={styles.infoRow}>
          <Text style={styles.label}>Type:</Text>
          <Text style={styles.value}>{sensor.sensor_type.name}</Text>
        </View>
        
        <View style={styles.infoRow}>
          <Text style={styles.label}>Protocol:</Text>
          <Text style={styles.value}>{sensor.protocol.toUpperCase()}</Text>
        </View>
        
        {sensor.battery_level && (
          <View style={styles.infoRow}>
            <Text style={styles.label}>Battery:</Text>
            <Text style={styles.value}>{sensor.battery_level}%</Text>
          </View>
        )}
        
        {sensor.signal_strength && (
          <View style={styles.infoRow}>
            <Text style={styles.label}>Signal:</Text>
            <Text style={styles.value}>{sensor.signal_strength}%</Text>
          </View>
        )}
      </View>
      
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Recent Readings</Text>
        {readings.map((reading, index) => (
          <View key={index} style={[styles.readingRow, reading.is_anomaly && styles.anomalyRow]}>
            <Text style={styles.readingTime}>
              {new Date(reading.timestamp).toLocaleTimeString()}
            </Text>
            <Text style={[styles.readingValue, reading.is_anomaly && styles.anomalyValue]}>
              {reading.value} {reading.unit}
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0e27',
    padding: 15
  },
  loading: {
    color: '#00ff41',
    textAlign: 'center',
    marginTop: 50
  },
  card: {
    backgroundColor: '#1a2332',
    borderWidth: 1,
    borderColor: '#00ff41',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15
  },
  title: {
    color: '#00ff41',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 5
  },
  subtitle: {
    color: '#7f8c8d',
    fontSize: 12,
    marginBottom: 15
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10
  },
  label: {
    color: '#7f8c8d',
    fontSize: 14
  },
  value: {
    color: '#00ff41',
    fontSize: 14,
    fontWeight: 'bold'
  },
  sectionTitle: {
    color: '#00ff41',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10
  },
  readingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 255, 65, 0.2)'
  },
  anomalyRow: {
    backgroundColor: 'rgba(244, 67, 54, 0.1)'
  },
  readingTime: {
    color: '#7f8c8d',
    fontSize: 12
  },
  readingValue: {
    color: '#00ff41',
    fontSize: 14,
    fontWeight: 'bold'
  },
  anomalyValue: {
    color: '#f44336'
  }
});

