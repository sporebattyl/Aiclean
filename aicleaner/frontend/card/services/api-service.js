/**
 * API Service for Roo AI Cleaning Assistant
 * Handles all communication with the backend API
 */

export class RooApiService {
  constructor(hassUrl, accessToken) {
    this.baseUrl = `${hassUrl}/api/roo`;
    this.headers = {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: this.headers,
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Zone Management
  async getZones() {
    return this.request('/zones');
  }

  async getZone(zoneId) {
    return this.request(`/zones/${zoneId}`);
  }

  async createZone(zoneData) {
    return this.request('/zones', {
      method: 'POST',
      body: JSON.stringify(zoneData)
    });
  }

  async updateZone(zoneId, updates) {
    return this.request(`/zones/${zoneId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteZone(zoneId) {
    return this.request(`/zones/${zoneId}`, {
      method: 'DELETE'
    });
  }

  // Task Management
  async getZoneTasks(zoneId, status = null) {
    const params = status ? `?status=${status}` : '';
    return this.request(`/zones/${zoneId}/tasks${params}`);
  }

  async getTask(taskId) {
    return this.request(`/tasks/${taskId}`);
  }

  async completeTask(taskId, userId = null) {
    const body = userId ? JSON.stringify({ user_id: userId }) : '{}';
    return this.request(`/tasks/${taskId}/complete`, {
      method: 'POST',
      body
    });
  }

  async ignoreTask(taskId, userId = null) {
    const body = userId ? JSON.stringify({ user_id: userId }) : '{}';
    return this.request(`/tasks/${taskId}/ignore`, {
      method: 'POST',
      body
    });
  }

  async deleteTask(taskId) {
    return this.request(`/tasks/${taskId}`, {
      method: 'DELETE'
    });
  }

  // Performance Metrics
  async getPerformanceMetrics(zoneId, days = 30) {
    return this.request(`/zones/${zoneId}/metrics?days=${days}`);
  }

  async getMetricsSummary(zoneId, days = 30) {
    return this.request(`/zones/${zoneId}/metrics/summary?days=${days}`);
  }

  async getZoneHistory(zoneId, limit = 10) {
    return this.request(`/zones/${zoneId}/history?limit=${limit}`);
  }

  // Analysis
  async triggerAnalysis(zoneId) {
    return this.request(`/zones/${zoneId}/analyze`, {
      method: 'POST'
    });
  }

  async triggerAnalysisAll() {
    return this.request('/analyze-all', {
      method: 'POST'
    });
  }

  async getAnalysisStatus(analysisId) {
    return this.request(`/analysis/${analysisId}/status`);
  }

  // Ignore Rules
  async getIgnoreRules(zoneId) {
    return this.request(`/zones/${zoneId}/ignore-rules`);
  }

  async createIgnoreRule(zoneId, ruleData) {
    return this.request(`/zones/${zoneId}/ignore-rules`, {
      method: 'POST',
      body: JSON.stringify(ruleData)
    });
  }

  async updateIgnoreRule(ruleId, updates) {
    return this.request(`/ignore-rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteIgnoreRule(ruleId) {
    return this.request(`/ignore-rules/${ruleId}`, {
      method: 'DELETE'
    });
  }

  // Notifications
  async getNotifications(limit = 10) {
    return this.request(`/notifications?limit=${limit}`);
  }

  async getZoneNotifications(zoneId, limit = 10) {
    return this.request(`/zones/${zoneId}/notifications?limit=${limit}`);
  }

  async dismissNotification(notificationId) {
    return this.request(`/notifications/${notificationId}/dismiss`, {
      method: 'POST'
    });
  }

  async getNotificationSettings(zoneId = null) {
    const endpoint = zoneId ? `/zones/${zoneId}/notification-settings` : '/notification-settings';
    return this.request(endpoint);
  }

  async updateNotificationSettings(settings, zoneId = null) {
    const endpoint = zoneId ? `/zones/${zoneId}/notification-settings` : '/notification-settings';
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
  }

  // Dashboard Data
  async getDashboardData() {
    return this.request('/dashboard');
  }

  async getSystemStatus() {
    return this.request('/status');
  }

  async getSystemStats() {
    return this.request('/stats');
  }

  // Configuration
  async getConfig() {
    return this.request('/config');
  }

  async updateConfig(config) {
    return this.request('/config', {
      method: 'PUT',
      body: JSON.stringify(config)
    });
  }

  async exportConfig() {
    return this.request('/config/export');
  }

  async importConfig(configData) {
    return this.request('/config/import', {
      method: 'POST',
      body: JSON.stringify(configData)
    });
  }

  // Image Management
  async getZoneImage(zoneId, timestamp = null) {
    const params = timestamp ? `?timestamp=${timestamp}` : '';
    return this.request(`/zones/${zoneId}/image${params}`);
  }

  async getAnalysisImage(analysisId) {
    return this.request(`/analysis/${analysisId}/image`);
  }

  // Testing and Debugging
  async testZoneCamera(zoneId) {
    return this.request(`/zones/${zoneId}/test-camera`, {
      method: 'POST'
    });
  }

  async testZoneAnalysis(zoneId, imageData = null) {
    const body = imageData ? JSON.stringify({ image_data: imageData }) : '{}';
    return this.request(`/zones/${zoneId}/test-analysis`, {
      method: 'POST',
      body
    });
  }

  async getDebugInfo(zoneId = null) {
    const endpoint = zoneId ? `/zones/${zoneId}/debug` : '/debug';
    return this.request(endpoint);
  }

  // Batch Operations
  async batchUpdateTasks(updates) {
    return this.request('/tasks/batch', {
      method: 'PUT',
      body: JSON.stringify({ updates })
    });
  }

  async batchDeleteTasks(taskIds) {
    return this.request('/tasks/batch', {
      method: 'DELETE',
      body: JSON.stringify({ task_ids: taskIds })
    });
  }

  // Search and Filtering
  async searchTasks(query, zoneId = null, status = null) {
    const params = new URLSearchParams();
    params.append('q', query);
    if (zoneId) params.append('zone_id', zoneId);
    if (status) params.append('status', status);
    
    return this.request(`/tasks/search?${params.toString()}`);
  }

  async getTasksByDateRange(startDate, endDate, zoneId = null) {
    const params = new URLSearchParams();
    params.append('start_date', startDate);
    params.append('end_date', endDate);
    if (zoneId) params.append('zone_id', zoneId);
    
    return this.request(`/tasks/date-range?${params.toString()}`);
  }

  // Utility Methods
  isHealthy() {
    return this.request('/health').then(() => true).catch(() => false);
  }

  async ping() {
    const start = Date.now();
    await this.request('/ping');
    return Date.now() - start;
  }

  // Error Handling Helpers
  handleApiError(error, context = '') {
    console.error(`API Error${context ? ` (${context})` : ''}:`, error);
    
    if (error.message.includes('401')) {
      throw new Error('Authentication failed. Please check your Home Assistant token.');
    } else if (error.message.includes('403')) {
      throw new Error('Access denied. Please check your permissions.');
    } else if (error.message.includes('404')) {
      throw new Error('Resource not found. The requested item may have been deleted.');
    } else if (error.message.includes('429')) {
      throw new Error('Rate limit exceeded. Please wait before trying again.');
    } else if (error.message.includes('500')) {
      throw new Error('Server error. Please try again later.');
    } else if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
      throw new Error('Network error. Please check your connection.');
    }
    
    throw error;
  }

  // Convenience methods for common operations
  async getZoneOverview(zoneId) {
    try {
      const [zone, tasks, metrics] = await Promise.all([
        this.getZone(zoneId),
        this.getZoneTasks(zoneId),
        this.getPerformanceMetrics(zoneId, 7) // Last 7 days
      ]);

      return {
        zone,
        tasks,
        metrics,
        pendingTasks: tasks.filter(t => t.status === 'pending'),
        completedTasks: tasks.filter(t => ['completed', 'auto_completed'].includes(t.status))
      };
    } catch (error) {
      this.handleApiError(error, 'getZoneOverview');
    }
  }

  async getAllZonesOverview() {
    try {
      const zones = await this.getZones();
      const overviews = await Promise.all(
        zones.map(zone => this.getZoneOverview(zone.id))
      );
      
      return overviews;
    } catch (error) {
      this.handleApiError(error, 'getAllZonesOverview');
    }
  }
}
