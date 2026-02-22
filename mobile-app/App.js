import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import AsyncStorage from '@react-native-async-storage/async-storage';
import LoginScreen from './screens/LoginScreen';
import DashboardScreen from './screens/DashboardScreen';
import SensorDetailScreen from './screens/SensorDetailScreen';
import AlertsScreen from './screens/AlertsScreen';
import MapScreen from './screens/MapScreen';
import IncidentReportScreen from './screens/IncidentReportScreen';

const Stack = createStackNavigator();

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = await AsyncStorage.getItem('access_token');
      setIsAuthenticated(!!token);
    } catch (error) {
      console.error('Error checking auth:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return null;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: '#0a0e27' },
          headerTintColor: '#00ff41',
          headerTitleStyle: { fontWeight: 'bold' }
        }}
      >
        {!isAuthenticated ? (
          <Stack.Screen 
            name="Login" 
            component={LoginScreen}
            options={{ headerShown: false }}
          />
        ) : (
          <>
            <Stack.Screen 
              name="Dashboard" 
              component={DashboardScreen}
              options={{ title: 'Water Monitoring' }}
            />
            <Stack.Screen 
              name="SensorDetail" 
              component={SensorDetailScreen}
              options={{ title: 'Sensor Details' }}
            />
            <Stack.Screen 
              name="Alerts" 
              component={AlertsScreen}
              options={{ title: 'Alerts' }}
            />
            <Stack.Screen 
              name="Map" 
              component={MapScreen}
              options={{ title: 'Map View' }}
            />
            <Stack.Screen 
              name="IncidentReport" 
              component={IncidentReportScreen}
              options={{ title: 'Report Incident' }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
