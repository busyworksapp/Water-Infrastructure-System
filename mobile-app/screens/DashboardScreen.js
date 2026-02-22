import React, { useState, useEffect } from 'react';
import { API_URL } from '../config';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';


export default function DashboardScreen({ navigation }) {
  const [stats, setStats] = useState({ totalSensors: 0, activeSensors: 0, openAlerts: 0, criticalAlerts: 0 });
  const [alerts, setAlerts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [sensorsRes, alertsRes, statsRes] = await Promise.all([
        axios.get(`${API_URL}/api/v1/sensors`, { headers }),
        axios.get(`${API_URL}/api/v1/alerts?limit=5`, { headers }),
        axios.get(`${API_URL}/api/v1/alerts/statistics/summary`, { headers })
      ]);
      
      setStats({
        totalSensors: sensorsRes.data.length,
        activeSensors: sensorsRes.data.filter(s => s.status === 'active').length,
        openAlerts: statsRes.data.open,
        criticalAlerts: statsRes.data.critical
      });
      
      setAlerts(alertsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const handleLogout = async () => {
    await AsyncStorage.clear();
    navigation.replace('Login');
  };

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>TOTAL SENSORS</Text>
          <Text style={styles.statValue}>{stats.totalSensors}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>ACTIVE</Text>
          <Text style={[styles.statValue, { color: '#00ff41' }]}>{stats.activeSensors}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>OPEN ALERTS</Text>
          <Text style={[styles.statValue, { color: '#ffeb3b' }]}>{stats.openAlerts}</Text>
        </View>
        
        <View style={styles.statCard}>
          <Text style={styles.statLabel}>CRITICAL</Text>
          <Text style={[styles.statValue, { color: '#f44336' }]}>{stats.criticalAlerts}</Text>
        </View>
      </View>
      
      <View style={styles.menuGrid}>
        <TouchableOpacity style={styles.menuCard} onPress={() => navigation.navigate('Alerts')}>
          <Text style={styles.menuIcon}>ðŸš¨</Text>
          <Text style={styles.menuText}>Alerts</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.menuCard} onPress={() => navigation.navigate('Map')}>
          <Text style={styles.menuIcon}>ðŸ—ºï¸</Text>
          <Text style={styles.menuText}>Map View</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.menuCard} onPress={() => navigation.navigate('IncidentReport')}>
          <Text style={styles.menuIcon}>ðŸ“</Text>
          <Text style={styles.menuText}>Report</Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.menuCard} onPress={handleLogout}>
          <Text style={styles.menuIcon}>ðŸšª</Text>
          <Text style={styles.menuText}>Logout</Text>
        </TouchableOpacity>
      </View>
      
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>RECENT ALERTS</Text>
        {alerts.map(alert => (
          <View key={alert.id} style={styles.alertCard}>
            <Text style={styles.alertTitle}>{alert.title}</Text>
            <Text style={styles.alertMeta}>
              {alert.severity.toUpperCase()} - {new Date(alert.created_at).toLocaleString()}
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
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20
  },
  statCard: {
    width: '48%',
    backgroundColor: '#1a2332',
    borderWidth: 2,
    borderColor: '#00ff41',
    borderRadius: 8,
    padding: 15,
    marginBottom: 10
  },
  statLabel: {
    color: '#7f8c8d',
    fontSize: 12,
    marginBottom: 5
  },
  statValue: {
    color: '#00ff41',
    fontSize: 28,
    fontWeight: 'bold'
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20
  },
  menuCard: {
    width: '48%',
    backgroundColor: '#1a2332',
    borderWidth: 1,
    borderColor: '#00ff41',
    borderRadius: 8,
    padding: 20,
    alignItems: 'center',
    marginBottom: 10
  },
  menuIcon: {
    fontSize: 40,
    marginBottom: 10
  },
  menuText: {
    color: '#00ff41',
    fontSize: 14,
    fontWeight: 'bold'
  },
  section: {
    marginBottom: 20
  },
  sectionTitle: {
    color: '#00ff41',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10
  },
  alertCard: {
    backgroundColor: '#1a2332',
    borderLeftWidth: 4,
    borderLeftColor: '#f44336',
    padding: 15,
    marginBottom: 10,
    borderRadius: 4
  },
  alertTitle: {
    color: '#00ff41',
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 5
  },
  alertMeta: {
    color: '#7f8c8d',
    fontSize: 12
  }
});

