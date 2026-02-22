import React, { useState } from 'react';
import { API_URL } from '../config';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';


export default function LoginScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('Error', 'Please enter username and password');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/api/v1/auth/login`, {
        username,
        password
      });

      const { access_token, user } = response.data;
      
      await AsyncStorage.setItem('access_token', access_token);
      await AsyncStorage.setItem('user', JSON.stringify(user));
      
      navigation.replace('Dashboard');
    } catch (error) {
      Alert.alert('Login Failed', error.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>ðŸŒŠ WATER MONITORING</Text>
      <Text style={styles.subtitle}>Mobile Access</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Username"
        placeholderTextColor="#7f8c8d"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />
      
      <TextInput
        style={styles.input}
        placeholder="Password"
        placeholderTextColor="#7f8c8d"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      
      <TouchableOpacity 
        style={styles.button} 
        onPress={handleLogin}
        disabled={loading}
      >
        <Text style={styles.buttonText}>
          {loading ? 'LOGGING IN...' : 'LOGIN'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0e27',
    justifyContent: 'center',
    padding: 20
  },
  title: {
    fontSize: 28,
    color: '#00ff41',
    textAlign: 'center',
    marginBottom: 10,
    fontWeight: 'bold'
  },
  subtitle: {
    fontSize: 16,
    color: '#7f8c8d',
    textAlign: 'center',
    marginBottom: 40
  },
  input: {
    backgroundColor: '#1a2332',
    borderWidth: 1,
    borderColor: '#00ff41',
    borderRadius: 8,
    padding: 15,
    color: '#00ff41',
    marginBottom: 15,
    fontSize: 16
  },
  button: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#00ff41',
    borderRadius: 8,
    padding: 15,
    marginTop: 10
  },
  buttonText: {
    color: '#00ff41',
    textAlign: 'center',
    fontSize: 16,
    fontWeight: 'bold'
  }
});

