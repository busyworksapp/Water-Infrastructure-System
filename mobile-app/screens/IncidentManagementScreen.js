import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, TextInput, Modal } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../config';

const IncidentManagementScreen = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      const response = await fetch(`${API_URL}/api/v1/incidents`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setIncidents(data);
    } catch (error) {
      console.error('Error fetching incidents:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateIncident = async (incidentId, status) => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      await fetch(`${API_URL}/api/v1/incidents/${incidentId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, notes })
      });
      fetchIncidents();
      setModalVisible(false);
    } catch (error) {
      console.error('Error updating incident:', error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      open: '#ff6600',
      in_progress: '#ffcc00',
      resolved: '#00ff00',
      closed: '#888888'
    };
    return colors[status] || '#888888';
  };

  const renderIncident = ({ item }) => (
    <TouchableOpacity
      style={styles.incidentCard}
      onPress={() => {
        setSelectedIncident(item);
        setNotes(item.notes || '');
        setModalVisible(true);
      }}
    >
      <View style={styles.incidentHeader}>
        <Text style={styles.incidentTitle}>{item.title}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) }]}>
          <Text style={styles.statusText}>{item.status.toUpperCase()}</Text>
        </View>
      </View>
      <Text style={styles.incidentDescription}>{item.description}</Text>
      <View style={styles.incidentMeta}>
        <Text style={styles.metaText}>Sensor: {item.sensor_name}</Text>
        <Text style={styles.metaText}>{new Date(item.created_at).toLocaleDateString()}</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Incident Management</Text>
      
      <FlatList
        data={incidents}
        renderItem={renderIncident}
        keyExtractor={item => item.id.toString()}
        refreshing={loading}
        onRefresh={fetchIncidents}
        contentContainerStyle={styles.list}
      />

      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>{selectedIncident?.title}</Text>
            
            <TextInput
              style={styles.notesInput}
              placeholder="Add notes..."
              placeholderTextColor="#888"
              multiline
              value={notes}
              onChangeText={setNotes}
            />
            
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.button, styles.progressButton]}
                onPress={() => updateIncident(selectedIncident.id, 'in_progress')}
              >
                <Text style={styles.buttonText}>In Progress</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.button, styles.resolveButton]}
                onPress={() => updateIncident(selectedIncident.id, 'resolved')}
              >
                <Text style={styles.buttonText}>Resolve</Text>
              </TouchableOpacity>
            </View>
            
            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
    padding: 15
  },
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00ff00',
    marginBottom: 20
  },
  list: {
    paddingBottom: 20
  },
  incidentCard: {
    backgroundColor: '#1e1e1e',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#ff6600'
  },
  incidentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10
  },
  incidentTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    flex: 1
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4
  },
  statusText: {
    color: '#000',
    fontSize: 10,
    fontWeight: 'bold'
  },
  incidentDescription: {
    color: '#ccc',
    fontSize: 14,
    marginBottom: 10
  },
  incidentMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between'
  },
  metaText: {
    color: '#888',
    fontSize: 12
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.8)'
  },
  modalContent: {
    backgroundColor: '#1e1e1e',
    borderRadius: 12,
    padding: 20,
    width: '90%',
    maxHeight: '80%'
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15
  },
  notesInput: {
    backgroundColor: '#2a2a2a',
    color: '#fff',
    borderRadius: 8,
    padding: 12,
    minHeight: 100,
    marginBottom: 20,
    textAlignVertical: 'top'
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center'
  },
  progressButton: {
    backgroundColor: '#ffcc00'
  },
  resolveButton: {
    backgroundColor: '#00ff00'
  },
  buttonText: {
    color: '#000',
    fontWeight: 'bold',
    fontSize: 14
  },
  closeButton: {
    padding: 12,
    alignItems: 'center'
  },
  closeButtonText: {
    color: '#888',
    fontSize: 14
  }
});

export default IncidentManagementScreen;
