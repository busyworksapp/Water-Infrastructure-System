import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

class OfflineCacheService {
  constructor() {
    this.isOnline = true;
    this.pendingRequests = [];
    this.cacheKeys = {
      SENSORS: 'cache_sensors',
      ALERTS: 'cache_alerts',
      READINGS: 'cache_readings',
      MUNICIPALITIES: 'cache_municipalities',
      PENDING_REQUESTS: 'cache_pending_requests',
    };
  }

  async initialize() {
    NetInfo.addEventListener(state => {
      this.isOnline = state.isConnected;
      if (this.isOnline) {
        this.syncPendingRequests();
      }
    });

    const netState = await NetInfo.fetch();
    this.isOnline = netState.isConnected;
  }

  async cacheData(key, data) {
    try {
      const cacheEntry = {
        data,
        timestamp: Date.now(),
      };
      await AsyncStorage.setItem(key, JSON.stringify(cacheEntry));
    } catch (error) {
      console.error('Cache write error:', error);
    }
  }

  async getCachedData(key, maxAge = 3600000) {
    try {
      const cached = await AsyncStorage.getItem(key);
      if (!cached) return null;

      const { data, timestamp } = JSON.parse(cached);
      const age = Date.now() - timestamp;

      if (age > maxAge) {
        await AsyncStorage.removeItem(key);
        return null;
      }

      return data;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  }

  async cacheSensors(sensors) {
    await this.cacheData(this.cacheKeys.SENSORS, sensors);
  }

  async getCachedSensors() {
    return await this.getCachedData(this.cacheKeys.SENSORS, 1800000);
  }

  async cacheAlerts(alerts) {
    await this.cacheData(this.cacheKeys.ALERTS, alerts);
  }

  async getCachedAlerts() {
    return await this.getCachedData(this.cacheKeys.ALERTS, 300000);
  }

  async cacheReadings(sensorId, readings) {
    const key = `${this.cacheKeys.READINGS}_${sensorId}`;
    await this.cacheData(key, readings);
  }

  async getCachedReadings(sensorId) {
    const key = `${this.cacheKeys.READINGS}_${sensorId}`;
    return await this.getCachedData(key, 600000);
  }

  async addPendingRequest(request) {
    try {
      const pending = await this.getPendingRequests();
      pending.push({
        ...request,
        timestamp: Date.now(),
        id: Date.now().toString(),
      });
      await AsyncStorage.setItem(
        this.cacheKeys.PENDING_REQUESTS,
        JSON.stringify(pending)
      );
    } catch (error) {
      console.error('Failed to add pending request:', error);
    }
  }

  async getPendingRequests() {
    try {
      const pending = await AsyncStorage.getItem(this.cacheKeys.PENDING_REQUESTS);
      return pending ? JSON.parse(pending) : [];
    } catch (error) {
      console.error('Failed to get pending requests:', error);
      return [];
    }
  }

  async removePendingRequest(id) {
    try {
      const pending = await this.getPendingRequests();
      const filtered = pending.filter(req => req.id !== id);
      await AsyncStorage.setItem(
        this.cacheKeys.PENDING_REQUESTS,
        JSON.stringify(filtered)
      );
    } catch (error) {
      console.error('Failed to remove pending request:', error);
    }
  }

  async syncPendingRequests() {
    if (!this.isOnline) return;

    const pending = await this.getPendingRequests();
    for (const request of pending) {
      try {
        await this.executePendingRequest(request);
        await this.removePendingRequest(request.id);
      } catch (error) {
        console.error('Failed to sync request:', error);
      }
    }
  }

  async executePendingRequest(request) {
    const axios = require('axios').default;
    const { method, url, data, headers } = request;

    return await axios({
      method,
      url,
      data,
      headers,
    });
  }

  async clearCache() {
    try {
      const keys = Object.values(this.cacheKeys);
      await AsyncStorage.multiRemove(keys);
    } catch (error) {
      console.error('Failed to clear cache:', error);
    }
  }

  async getCacheSize() {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => key.startsWith('cache_'));
      let totalSize = 0;

      for (const key of cacheKeys) {
        const value = await AsyncStorage.getItem(key);
        if (value) {
          totalSize += value.length;
        }
      }

      return totalSize;
    } catch (error) {
      console.error('Failed to get cache size:', error);
      return 0;
    }
  }

  isOffline() {
    return !this.isOnline;
  }
}

export default new OfflineCacheService();
