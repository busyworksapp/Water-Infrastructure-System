import React, { useState, useEffect } from 'react';
import { API_URL } from '../config';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';


export default function AlertsScreen() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAlerts();
  }, [filter]);

  const fetchAlerts = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      let url = `${API_URL}/api/v1/alerts?limit=50`;
      
      if (filter === 'open') url += '&status=open';
      if (filter === 'critical') url += '&severity=critical';
      
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(response.data);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchAlerts();
    setRefreshing(false);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#f44336';
      case 'high': return '#ff9800';
      case 'medium': return '#ffeb3b';
      default: return '#00ff41';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.filterBar}>
        <TouchableOpacity 
          style={[styles.filterBtn, filter === 'all' && styles.filterBtnActive]}
          onPress={() => setFilter('all')}
        >
          <Text style={styles.filterText}>ALL</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.filterBtn, filter === 'open' && styles.filterBtnActive]}
          onPress={() => setFilter('open')}
        >
          <Text style={styles.filterText}>OPEN</Text>
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={[styles.filterBtn, filter === 'critical' && styles.filterBtnActive]}
          onPress={() => setFilter('critical')}
        >
          <Text style={styles.filterText}>CRITICAL</Text>
        </TouchableOpacity>
      </View>
      
      <ScrollView 
        style={styles.alertList}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {alerts.map(alert => (
          <View key={alert.id} style={[
            styles.alertCard,
            { borderLeftColor: getSeverityColor(alert.severity) }
          ]}>
            <View style={styles.alertHeader}>
              <Text style={styles.alertTitle}>{alert.title}</Text>
              <Text style={[styles.alertSeverity, { color: getSeverityColor(alert.severity) }]}>
                {alert.severity.toUpperCase()}
              </Text>
            </View>
            
            <Text style={styles.alertDescription}>{alert.description}</Text>
            
            <View style={styles.alertFooter}>
              <Text style={styles.alertMeta}>
                {alert.alert_type.replace('_', ' ')}
              </Text>
              <Text style={styles.alertMeta}>
                {new Date(alert.created_at).toLocaleString()}
              </Text>
            </View>
            
            <View style={styles.alertStatus}>
              <Text style={styles.statusText}>Status: {alert.status}</Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0e27'
  },
  filterBar: {
    flexDirection: 'row',
    padding: 15,
    gap: 10
  },
  filterBtn: {
    flex: 1,
    padding: 10,
    borderWidth: 1,
    borderColor: '#00ff41',
    borderRadius: 4,
    alignItems: 'center'
  },
  filterBtnActive: {
    backgroundColor: 'rgba(0, 255, 65, 0.2)'
  },
  filterText: {
    color: '#00ff41',
    fontSize: 12,
    fontWeight: 'bold'
  },
  alertList: {
    flex: 1,
    padding: 15
  },
  alertCard: {
    backgroundColor: '#1a2332',
    borderLeftWidth: 4,
    borderRadius: 4,
    padding: 15,
    marginBottom: 10
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8
  },
  alertTitle: {
    color: '#00ff41',
    fontSize: 14,
    fontWeight: 'bold',
    flex: 1
  },
  alertSeverity: {
    fontSize: 12,
    fontWeight: 'bold'
  },
  alertDescription: {
    color: '#7f8c8d',
    fontSize: 12,
    marginBottom: 10
  },
  alertFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8
  },
  alertMeta: {
    color: '#7f8c8d',
    fontSize: 11
  },
  alertStatus: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 255, 65, 0.2)'
  },
  statusText: {
    color: '#00ff41',
    fontSize: 11
  }
});

