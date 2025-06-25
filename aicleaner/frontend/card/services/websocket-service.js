/**
 * WebSocket Service for Roo AI Cleaning Assistant
 * Handles real-time communication with the backend
 */

export class RooWebSocketService {
  constructor(hassUrl, accessToken) {
    this.wsUrl = `${hassUrl.replace('http', 'ws')}/api/roo/ws`;
    this.accessToken = accessToken;
    this.listeners = new Map();
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.heartbeatInterval = null;
    this.isConnected = false;
    this.isConnecting = false;
  }

  connect() {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    this.isConnecting = true;
    console.log('🔌 Connecting to Roo WebSocket...');

    try {
      this.ws = new WebSocket(`${this.wsUrl}?token=${this.accessToken}`);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  disconnect() {
    console.log('🔌 Disconnecting from Roo WebSocket...');
    
    this.isConnected = false;
    this.isConnecting = false;
    this.reconnectAttempts = 0;

    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  setupEventHandlers() {
    if (!this.ws) return;

    this.ws.onopen = (event) => {
      console.log('✅ Roo WebSocket connected');
      this.isConnected = true;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.reconnectDelay = 1000;
      
      this.startHeartbeat();
      this.emit('connected', { timestamp: new Date() });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error, event.data);
      }
    };

    this.ws.onclose = (event) => {
      console.log('🔌 Roo WebSocket disconnected:', event.code, event.reason);
      this.isConnected = false;
      this.isConnecting = false;

      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }

      this.emit('disconnected', { 
        code: event.code, 
        reason: event.reason,
        timestamp: new Date()
      });

      // Attempt to reconnect unless it was a clean disconnect
      if (event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('❌ Roo WebSocket error:', error);
      this.emit('error', { error, timestamp: new Date() });
    };
  }

  handleMessage(data) {
    const { type, payload, timestamp } = data;

    // Add timestamp if not present
    const messageData = {
      ...payload,
      timestamp: timestamp || new Date().toISOString()
    };

    console.log('📨 Received WebSocket message:', type, messageData);

    switch (type) {
      case 'zone_updated':
        this.emit('zone_updated', messageData);
        break;
      
      case 'task_created':
        this.emit('task_created', messageData);
        break;
      
      case 'task_completed':
        this.emit('task_completed', messageData);
        break;
      
      case 'task_auto_completed':
        this.emit('task_auto_completed', messageData);
        break;
      
      case 'analysis_started':
        this.emit('analysis_started', messageData);
        break;
      
      case 'analysis_complete':
        this.emit('analysis_complete', messageData);
        break;
      
      case 'analysis_error':
        this.emit('analysis_error', messageData);
        break;
      
      case 'metrics_updated':
        this.emit('metrics_updated', messageData);
        break;
      
      case 'notification':
        this.emit('notification', messageData);
        break;
      
      case 'system_status':
        this.emit('system_status', messageData);
        break;
      
      case 'heartbeat':
        this.handleHeartbeat(messageData);
        break;
      
      default:
        console.warn('Unknown WebSocket message type:', type);
        this.emit('unknown_message', { type, data: messageData });
    }
  }

  handleHeartbeat(data) {
    // Respond to server heartbeat
    this.send('heartbeat_response', { 
      client_timestamp: new Date().toISOString(),
      server_timestamp: data.timestamp 
    });
  }

  startHeartbeat() {
    // Send periodic heartbeat to keep connection alive
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send('heartbeat', { timestamp: new Date().toISOString() });
      }
    }, 30000); // Every 30 seconds
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached. Giving up.');
      this.emit('reconnect_failed', { 
        attempts: this.reconnectAttempts,
        timestamp: new Date()
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isConnected && !this.isConnecting) {
        this.connect();
      }
    }, delay);
  }

  send(type, payload = {}) {
    if (!this.isConnected || !this.ws) {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }

    try {
      const message = {
        type,
        payload,
        timestamp: new Date().toISOString()
      };

      this.ws.send(JSON.stringify(message));
      console.log('📤 Sent WebSocket message:', type, payload);
      return true;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return;
    
    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in WebSocket event callback for ${event}:`, error);
      }
    });
  }

  // Convenience methods for common operations
  subscribeToZone(zoneId) {
    return this.send('subscribe_zone', { zone_id: zoneId });
  }

  unsubscribeFromZone(zoneId) {
    return this.send('unsubscribe_zone', { zone_id: zoneId });
  }

  subscribeToNotifications() {
    return this.send('subscribe_notifications');
  }

  unsubscribeFromNotifications() {
    return this.send('unsubscribe_notifications');
  }

  requestZoneUpdate(zoneId) {
    return this.send('request_zone_update', { zone_id: zoneId });
  }

  requestSystemStatus() {
    return this.send('request_system_status');
  }

  // Connection status methods
  getConnectionStatus() {
    return {
      connected: this.isConnected,
      connecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts
    };
  }

  isReady() {
    return this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  // Utility methods
  waitForConnection(timeout = 5000) {
    return new Promise((resolve, reject) => {
      if (this.isConnected) {
        resolve();
        return;
      }

      const timeoutId = setTimeout(() => {
        this.off('connected', onConnected);
        this.off('error', onError);
        reject(new Error('WebSocket connection timeout'));
      }, timeout);

      const onConnected = () => {
        clearTimeout(timeoutId);
        this.off('connected', onConnected);
        this.off('error', onError);
        resolve();
      };

      const onError = (error) => {
        clearTimeout(timeoutId);
        this.off('connected', onConnected);
        this.off('error', onError);
        reject(error);
      };

      this.on('connected', onConnected);
      this.on('error', onError);

      if (!this.isConnecting) {
        this.connect();
      }
    });
  }

  // Debug methods
  getDebugInfo() {
    return {
      wsUrl: this.wsUrl,
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      reconnectDelay: this.reconnectDelay,
      hasHeartbeat: !!this.heartbeatInterval,
      readyState: this.ws ? this.ws.readyState : null,
      listenerCount: Array.from(this.listeners.entries()).map(([event, callbacks]) => ({
        event,
        count: callbacks.length
      }))
    };
  }

  // Cleanup method
  destroy() {
    this.disconnect();
    this.listeners.clear();
  }
}
