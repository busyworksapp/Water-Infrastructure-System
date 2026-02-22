import React, { useState } from 'react';
import { API_URL } from '../config';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert, ScrollView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';


export default function IncidentReportScreen({ navigation }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [incidentType, setIncidentType] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!title || !description) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('access_token');
      const user = JSON.parse(await AsyncStorage.getItem('user'));
      
      await axios.post(
        `${API_URL}/api/v1/incidents`,
        {
          title,
          description,
          incident_type: incidentType || 'general',
          municipality_id: user.municipality_id,
          severity: 'medium'
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      Alert.alert('Success', 'Incident reported successfully');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Error', 'Failed to report incident');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.form}>
        <Text style={styles.label}>Title *</Text>
        <TextInput
          style={styles.input}
          placeholder="Incident title"
          placeholderTextColor="#7f8c8d"
          value={title}
          onChangeText={setTitle}
        />
        
        <Text style={styles.label}>Type</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g., leak, burst, damage"
          placeholderTextColor="#7f8c8d"
          value={incidentType}
          onChangeText={setIncidentType}
        />
        
        <Text style={styles.label}>Description *</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Describe the incident..."
          placeholderTextColor="#7f8c8d"
          value={description}
          onChangeText={setDescription}
          multiline
          numberOfLines={6}
        />
        
        <TouchableOpacity 
          style={styles.submitBtn}
          onPress={handleSubmit}
          disabled={loading}
        >
          <Text style={styles.submitText}>
            {loading ? 'SUBMITTING...' : 'SUBMIT REPORT'}
          </Text>
        </TouchableOpacity>
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
  form: {
    backgroundColor: '#1a2332',
    borderWidth: 1,
    borderColor: '#00ff41',
    borderRadius: 8,
    padding: 20
  },
  label: {
    color: '#00ff41',
    fontSize: 14,
    marginBottom: 8,
    fontWeight: 'bold'
  },
  input: {
    backgroundColor: '#0a0e27',
    borderWidth: 1,
    borderColor: '#00ff41',
    borderRadius: 4,
    padding: 12,
    color: '#00ff41',
    marginBottom: 15,
    fontSize: 14
  },
  textArea: {
    height: 120,
    textAlignVertical: 'top'
  },
  submitBtn: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#00ff41',
    borderRadius: 4,
    padding: 15,
    marginTop: 10
  },
  submitText: {
    color: '#00ff41',
    textAlign: 'center',
    fontSize: 14,
    fontWeight: 'bold'
  }
});

