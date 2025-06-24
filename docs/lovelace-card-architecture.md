# Lovelace Card Architecture - Roo AI Cleaning Assistant v2.0

## Overview

The Roo Lovelace card provides a comprehensive, all-in-one dashboard for managing multiple zones, viewing tasks, analyzing performance, and configuring the system. The card is designed to match the modern aesthetic shown in the user mockups while providing rich functionality and real-time updates.

## Design Principles

1. **Modular Architecture**: Each section is a self-contained component
2. **Real-time Updates**: WebSocket integration for live data
3. **Responsive Design**: Works on mobile, tablet, and desktop
4. **Theme Integration**: Supports Home Assistant light/dark themes
5. **Performance Optimized**: Lazy loading and efficient rendering
6. **User-Friendly**: Intuitive interface matching the mockup design

## Component Architecture

### Main Card Structure

```javascript
// roo-card.js - Main card component
class RooCard extends LitElement {
  static properties = {
    config: { type: Object },
    hass: { type: Object },
    zones: { type: Array },
    selectedZone: { type: Object },
    viewMode: { type: String } // 'dashboard', 'zone', 'config'
  }
  
  render() {
    return html`
      <ha-card>
        <div class="roo-card-container">
          ${this.renderHeader()}
          ${this.renderContent()}
        </div>
      </ha-card>
    `;
  }
}
```

### Component Hierarchy

```
RooCard (main)
├── RooHeader (title, zone selector, view switcher)
├── RooNotifications (personality-based messages)
├── RooSpaces (zone overview and management)
├── RooTodos (task list with progress tracking)
├── RooPerformance (charts and analytics)
├── RooImageViewer (visual analysis pane)
└── RooConfig (settings and ignore rules)
```

## Individual Components

### 1. Notifications Component

```javascript
// components/roo-notifications.js
class RooNotifications extends LitElement {
  static properties = {
    notifications: { type: Array },
    personalityMode: { type: String }
  }
  
  render() {
    return html`
      <div class="notifications-container">
        ${this.notifications.map(notification => html`
          <div class="notification-item ${notification.type}">
            <div class="notification-icon">
              ${this.getIconForType(notification.type)}
            </div>
            <div class="notification-content">
              <div class="notification-title">${notification.title}</div>
              <div class="notification-message">${notification.message}</div>
              <div class="notification-time">${notification.time}</div>
            </div>
            <div class="notification-actions">
              <mwc-icon-button icon="close" @click=${() => this.dismissNotification(notification.id)}>
              </mwc-icon-button>
            </div>
          </div>
        `)}
      </div>
    `;
  }
}
```

### 2. Spaces Component

```javascript
// components/roo-spaces.js
class RooSpaces extends LitElement {
  static properties = {
    zones: { type: Array },
    selectedZone: { type: Object }
  }
  
  render() {
    return html`
      <div class="spaces-container">
        <div class="spaces-header">
          <h3>Spaces</h3>
          <mwc-button @click=${this.addZone}>
            <mwc-icon slot="icon">add</mwc-icon>
            Add
          </mwc-button>
        </div>
        <div class="spaces-grid">
          ${this.zones.map(zone => html`
            <div class="space-card ${zone.id === this.selectedZone?.id ? 'selected' : ''}"
                 @click=${() => this.selectZone(zone)}>
              <div class="space-icon">
                <mwc-icon>${this.getZoneIcon(zone.name)}</mwc-icon>
              </div>
              <div class="space-info">
                <div class="space-name">${zone.display_name}</div>
                <div class="space-status">
                  <span class="status-indicator ${zone.status}"></span>
                  ${zone.pending_tasks} tasks
                </div>
                <div class="space-score">Score: ${zone.cleanliness_score}/100</div>
              </div>
              <div class="space-badge">
                ${zone.pending_tasks > 0 ? zone.pending_tasks : '✓'}
              </div>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}
```

### 3. Todos Component

```javascript
// components/roo-todos.js
class RooTodos extends LitElement {
  static properties = {
    tasks: { type: Array },
    completionRate: { type: Number },
    selectedZone: { type: Object }
  }
  
  render() {
    const pendingTasks = this.tasks.filter(t => t.status === 'pending');
    
    return html`
      <div class="todos-container">
        <div class="todos-header">
          <h3>Todos</h3>
          <div class="completion-indicator">
            <roo-circular-progress 
              .value=${this.completionRate}
              .max=${100}
              .label=${"${this.completionRate}%"}
            ></roo-circular-progress>
          </div>
        </div>
        <div class="todos-summary">
          ${pendingTasks.length} tasks remaining today
        </div>
        <div class="todos-list">
          ${pendingTasks.map(task => html`
            <div class="todo-item">
              <mwc-checkbox 
                @change=${(e) => this.toggleTask(task.id, e.target.checked)}
              ></mwc-checkbox>
              <div class="todo-content">
                <div class="todo-description">${task.description}</div>
                <div class="todo-meta">
                  <span class="todo-zone">${task.zone_name}</span>
                  <span class="todo-confidence">
                    Confidence: ${Math.round(task.confidence_score * 100)}%
                  </span>
                  ${task.detection_count > 1 ? html`
                    <span class="todo-detections">
                      Detected ${task.detection_count} times
                    </span>
                  ` : ''}
                </div>
              </div>
              <div class="todo-actions">
                <mwc-icon-button 
                  icon="visibility_off" 
                  title="Ignore this task"
                  @click=${() => this.ignoreTask(task.id)}
                ></mwc-icon-button>
              </div>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}
```

### 4. Performance Component

```javascript
// components/roo-performance.js
class RooPerformance extends LitElement {
  static properties = {
    metrics: { type: Object },
    chartData: { type: Array },
    timeRange: { type: String }
  }
  
  render() {
    return html`
      <div class="performance-container">
        <div class="performance-header">
          <h3>Performance</h3>
          <mwc-select @change=${this.changeTimeRange}>
            <mwc-list-item value="7">7 days</mwc-list-item>
            <mwc-list-item value="30" selected>30 days</mwc-list-item>
            <mwc-list-item value="90">90 days</mwc-list-item>
          </mwc-select>
        </div>
        <div class="performance-summary">
          <div class="metric-change ${this.metrics.trend > 0 ? 'positive' : 'negative'}">
            <mwc-icon>${this.metrics.trend > 0 ? 'trending_up' : 'trending_down'}</mwc-icon>
            ${Math.abs(this.metrics.trend)}% from last month
          </div>
        </div>
        <div class="performance-chart">
          <roo-chart 
            .data=${this.chartData}
            .type=${'line'}
            .options=${{
              responsive: true,
              scales: {
                y: { beginAtZero: true, max: 100 }
              }
            }}
          ></roo-chart>
        </div>
        <div class="performance-legend">
          <div class="legend-item">
            <span class="legend-color tasks-created"></span>
            <span class="legend-label">Tasks Created (${this.metrics.total_tasks_created} total)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color tasks-completed"></span>
            <span class="legend-label">Tasks Completed (${this.metrics.total_tasks_completed} total)</span>
          </div>
        </div>
      </div>
    `;
  }
}
```

## Data Flow Architecture

### API Service Layer

```javascript
// services/api-service.js
class RooApiService {
  constructor(hassUrl, accessToken) {
    this.baseUrl = `${hassUrl}/api/roo`;
    this.headers = {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    };
  }
  
  async getZones() {
    const response = await fetch(`${this.baseUrl}/zones`, {
      headers: this.headers
    });
    return response.json();
  }
  
  async getZoneTasks(zoneId) {
    const response = await fetch(`${this.baseUrl}/zones/${zoneId}/tasks`, {
      headers: this.headers
    });
    return response.json();
  }
  
  async completeTask(taskId) {
    const response = await fetch(`${this.baseUrl}/tasks/${taskId}/complete`, {
      method: 'POST',
      headers: this.headers
    });
    return response.json();
  }
  
  async getPerformanceMetrics(zoneId, days = 30) {
    const response = await fetch(`${this.baseUrl}/zones/${zoneId}/metrics?days=${days}`, {
      headers: this.headers
    });
    return response.json();
  }
}
```

### WebSocket Service

```javascript
// services/websocket-service.js
class RooWebSocketService {
  constructor(hassUrl, accessToken) {
    this.wsUrl = `${hassUrl.replace('http', 'ws')}/api/roo/ws`;
    this.accessToken = accessToken;
    this.listeners = new Map();
  }
  
  connect() {
    this.ws = new WebSocket(`${this.wsUrl}?token=${this.accessToken}`);
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
  }
  
  handleMessage(data) {
    const { type, payload } = data;
    
    switch (type) {
      case 'zone_updated':
        this.emit('zone_updated', payload);
        break;
      case 'task_completed':
        this.emit('task_completed', payload);
        break;
      case 'analysis_complete':
        this.emit('analysis_complete', payload);
        break;
      case 'metrics_updated':
        this.emit('metrics_updated', payload);
        break;
    }
  }
  
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }
  
  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    callbacks.forEach(callback => callback(data));
  }
}
```

## Configuration Schema

```yaml
# Card configuration in Lovelace
type: custom:roo-card
config:
  title: "Roo Assistant"
  zones:
    - living_room
    - kitchen
    - bedroom
  sections:
    - notifications
    - spaces
    - todos
    - performance
  layout: "default" # default, compact, minimal
  update_interval: 30 # seconds
  show_images: true
  theme: "auto" # auto, light, dark
  notifications:
    enabled: true
    max_items: 5
    auto_dismiss: 300 # seconds
  performance:
    default_range: 30 # days
    show_trends: true
    chart_type: "line" # line, bar, area
```

## Installation and Distribution

### HACS Integration

```json
{
  "name": "Roo AI Cleaning Assistant Card",
  "render_readme": true,
  "domains": ["sensor"],
  "iot_class": "Local Polling",
  "homeassistant": "2023.1.0"
}
```

### File Structure

```
roo-card/
├── dist/
│   └── roo-card.js (bundled)
├── src/
│   ├── roo-card.js
│   ├── components/
│   ├── services/
│   └── styles/
├── package.json
├── rollup.config.js
└── README.md
```

This architecture provides a solid foundation for the comprehensive Lovelace card that matches the user's vision while being maintainable, performant, and user-friendly.
