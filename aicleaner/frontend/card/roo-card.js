/**
 * Roo AI Cleaning Assistant v2.0 - Main Lovelace Card
 * 
 * A comprehensive dashboard card for managing multiple zones, viewing tasks,
 * analyzing performance, and configuring the system.
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

// Import components
import './components/roo-header.js';
import './components/roo-notifications.js';
import './components/roo-spaces.js';
import './components/roo-todos.js';
import './components/roo-performance.js';
import './components/roo-config.js';
import './components/roo-image-viewer.js';

// Import services
import { RooApiService } from './services/api-service.js';
import { RooWebSocketService } from './services/websocket-service.js';

@customElement('roo-card')
export class RooCard extends LitElement {
  @property({ type: Object }) hass;
  @property({ type: Object }) config;
  
  @state() zones = [];
  @state() selectedZone = null;
  @state() viewMode = 'dashboard'; // dashboard, zone, config
  @state() loading = false;
  @state() error = null;
  @state() notifications = [];
  @state() tasks = [];
  @state() metrics = {};
  @state() lastUpdate = null;

  constructor() {
    super();
    this.apiService = null;
    this.wsService = null;
    this.updateInterval = null;
  }

  static get styles() {
    return css`
      :host {
        display: block;
        background: var(--card-background-color, var(--primary-background-color));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,0.1));
        overflow: hidden;
        font-family: var(--primary-font-family);
      }

      .roo-card-container {
        display: flex;
        flex-direction: column;
        min-height: 400px;
      }

      .roo-content {
        flex: 1;
        padding: 16px;
        overflow-y: auto;
      }

      .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
        color: var(--primary-color);
      }

      .error-message {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: var(--error-color);
        text-align: center;
        padding: 16px;
      }

      .error-icon {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
      }

      .retry-button {
        margin-top: 16px;
        padding: 8px 16px;
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }

      .retry-button:hover {
        background: var(--primary-color-dark);
      }

      /* Responsive design */
      @media (max-width: 768px) {
        .roo-content {
          padding: 12px;
        }
      }

      /* Theme support */
      :host([theme="dark"]) {
        --card-background-color: var(--primary-background-color);
        --text-primary-color: var(--primary-text-color);
      }

      /* Animation for smooth transitions */
      .roo-content > * {
        transition: opacity 0.3s ease-in-out;
      }

      .fade-in {
        animation: fadeIn 0.3s ease-in-out;
      }

      @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }

      .zone-transition {
        animation: slideIn 0.3s ease-in-out;
      }

      @keyframes slideIn {
        from { transform: translateX(20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    this.initializeServices();
    this.loadInitialData();
    this.setupUpdateInterval();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.cleanup();
  }

  initializeServices() {
    if (!this.hass) return;

    try {
      // Initialize API service
      this.apiService = new RooApiService(
        this.hass.hassUrl || window.location.origin,
        this.hass.auth?.accessToken
      );

      // Initialize WebSocket service
      this.wsService = new RooWebSocketService(
        this.hass.hassUrl || window.location.origin,
        this.hass.auth?.accessToken
      );

      // Set up WebSocket event listeners
      this.setupWebSocketListeners();

    } catch (error) {
      console.error('Failed to initialize Roo services:', error);
      this.error = 'Failed to initialize services';
    }
  }

  setupWebSocketListeners() {
    if (!this.wsService) return;

    this.wsService.on('zone_updated', (data) => {
      this.handleZoneUpdate(data);
    });

    this.wsService.on('task_completed', (data) => {
      this.handleTaskUpdate(data);
    });

    this.wsService.on('analysis_complete', (data) => {
      this.handleAnalysisComplete(data);
    });

    this.wsService.on('metrics_updated', (data) => {
      this.handleMetricsUpdate(data);
    });

    this.wsService.on('notification', (data) => {
      this.handleNotification(data);
    });

    // Connect WebSocket
    this.wsService.connect();
  }

  async loadInitialData() {
    if (!this.apiService) return;

    this.loading = true;
    this.error = null;

    try {
      // Load zones
      const zones = await this.apiService.getZones();
      this.zones = zones || [];

      // Select first zone if none selected
      if (this.zones.length > 0 && !this.selectedZone) {
        this.selectedZone = this.zones[0];
      }

      // Load data for selected zone
      if (this.selectedZone) {
        await this.loadZoneData(this.selectedZone.id);
      }

      // Load recent notifications
      await this.loadNotifications();

      this.lastUpdate = new Date();

    } catch (error) {
      console.error('Failed to load initial data:', error);
      this.error = 'Failed to load data. Please check your connection.';
    } finally {
      this.loading = false;
    }
  }

  async loadZoneData(zoneId) {
    if (!this.apiService) return;

    try {
      // Load tasks for zone
      const tasks = await this.apiService.getZoneTasks(zoneId);
      this.tasks = tasks || [];

      // Load performance metrics
      const metrics = await this.apiService.getPerformanceMetrics(zoneId);
      this.metrics = metrics || {};

    } catch (error) {
      console.error(`Failed to load data for zone ${zoneId}:`, error);
    }
  }

  async loadNotifications() {
    if (!this.apiService) return;

    try {
      const notifications = await this.apiService.getNotifications();
      this.notifications = notifications || [];
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  }

  setupUpdateInterval() {
    const updateFrequency = this.config?.update_interval || 30; // seconds
    
    this.updateInterval = setInterval(() => {
      this.refreshData();
    }, updateFrequency * 1000);
  }

  async refreshData() {
    if (this.loading) return;

    try {
      if (this.selectedZone) {
        await this.loadZoneData(this.selectedZone.id);
      }
      await this.loadNotifications();
      this.lastUpdate = new Date();
    } catch (error) {
      console.error('Failed to refresh data:', error);
    }
  }

  cleanup() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }

    if (this.wsService) {
      this.wsService.disconnect();
    }
  }

  // Event handlers
  handleZoneUpdate(data) {
    const zoneIndex = this.zones.findIndex(z => z.id === data.zone_id);
    if (zoneIndex >= 0) {
      this.zones[zoneIndex] = { ...this.zones[zoneIndex], ...data };
      this.requestUpdate();
    }
  }

  handleTaskUpdate(data) {
    if (this.selectedZone && data.zone_id === this.selectedZone.id) {
      this.loadZoneData(this.selectedZone.id);
    }
  }

  handleAnalysisComplete(data) {
    if (this.selectedZone && data.zone_id === this.selectedZone.id) {
      this.loadZoneData(this.selectedZone.id);
    }
    
    // Update zone in list
    this.handleZoneUpdate(data);
  }

  handleMetricsUpdate(data) {
    if (this.selectedZone && data.zone_id === this.selectedZone.id) {
      this.metrics = { ...this.metrics, ...data };
      this.requestUpdate();
    }
  }

  handleNotification(data) {
    this.notifications = [data, ...this.notifications.slice(0, 9)]; // Keep last 10
    this.requestUpdate();
  }

  // User interaction handlers
  onZoneSelected(zone) {
    if (zone.id !== this.selectedZone?.id) {
      this.selectedZone = zone;
      this.viewMode = 'zone';
      this.loadZoneData(zone.id);
    }
  }

  onViewModeChanged(mode) {
    this.viewMode = mode;
  }

  async onTaskCompleted(taskId) {
    if (!this.apiService) return;

    try {
      await this.apiService.completeTask(taskId);
      await this.loadZoneData(this.selectedZone.id);
    } catch (error) {
      console.error('Failed to complete task:', error);
    }
  }

  async onTaskIgnored(taskId) {
    if (!this.apiService) return;

    try {
      await this.apiService.ignoreTask(taskId);
      await this.loadZoneData(this.selectedZone.id);
    } catch (error) {
      console.error('Failed to ignore task:', error);
    }
  }

  onNotificationDismissed(notificationId) {
    this.notifications = this.notifications.filter(n => n.id !== notificationId);
    this.requestUpdate();
  }

  async onRetry() {
    await this.loadInitialData();
  }

  render() {
    if (this.loading && !this.zones.length) {
      return this.renderLoading();
    }

    if (this.error && !this.zones.length) {
      return this.renderError();
    }

    return html`
      <div class="roo-card-container">
        <roo-header
          .zones=${this.zones}
          .selectedZone=${this.selectedZone}
          .viewMode=${this.viewMode}
          .lastUpdate=${this.lastUpdate}
          @zone-selected=${(e) => this.onZoneSelected(e.detail)}
          @view-mode-changed=${(e) => this.onViewModeChanged(e.detail)}
        ></roo-header>

        <div class="roo-content fade-in">
          ${this.renderContent()}
        </div>
      </div>
    `;
  }

  renderContent() {
    switch (this.viewMode) {
      case 'dashboard':
        return this.renderDashboard();
      case 'zone':
        return this.renderZoneView();
      case 'config':
        return this.renderConfig();
      default:
        return this.renderDashboard();
    }
  }

  renderDashboard() {
    return html`
      <roo-notifications
        .notifications=${this.notifications}
        @notification-dismissed=${(e) => this.onNotificationDismissed(e.detail)}
      ></roo-notifications>

      <roo-spaces
        .zones=${this.zones}
        .selectedZone=${this.selectedZone}
        @zone-selected=${(e) => this.onZoneSelected(e.detail)}
      ></roo-spaces>

      <roo-todos
        .tasks=${this.tasks}
        .selectedZone=${this.selectedZone}
        @task-completed=${(e) => this.onTaskCompleted(e.detail)}
        @task-ignored=${(e) => this.onTaskIgnored(e.detail)}
      ></roo-todos>

      <roo-performance
        .metrics=${this.metrics}
        .selectedZone=${this.selectedZone}
      ></roo-performance>
    `;
  }

  renderZoneView() {
    if (!this.selectedZone) {
      return html`<div>No zone selected</div>`;
    }

    return html`
      <div class="zone-transition">
        <roo-image-viewer
          .zone=${this.selectedZone}
          .apiService=${this.apiService}
        ></roo-image-viewer>

        <roo-todos
          .tasks=${this.tasks}
          .selectedZone=${this.selectedZone}
          .detailed=${true}
          @task-completed=${(e) => this.onTaskCompleted(e.detail)}
          @task-ignored=${(e) => this.onTaskIgnored(e.detail)}
        ></roo-todos>

        <roo-performance
          .metrics=${this.metrics}
          .selectedZone=${this.selectedZone}
          .detailed=${true}
        ></roo-performance>
      </div>
    `;
  }

  renderConfig() {
    return html`
      <roo-config
        .zones=${this.zones}
        .config=${this.config}
        .apiService=${this.apiService}
        @zones-updated=${() => this.loadInitialData()}
      ></roo-config>
    `;
  }

  renderLoading() {
    return html`
      <div class="roo-card-container">
        <div class="loading-spinner">
          <ha-circular-progress active></ha-circular-progress>
        </div>
      </div>
    `;
  }

  renderError() {
    return html`
      <div class="roo-card-container">
        <div class="error-message">
          <div class="error-icon">⚠️</div>
          <div>${this.error}</div>
          <button class="retry-button" @click=${this.onRetry}>
            Retry
          </button>
        </div>
      </div>
    `;
  }

  // Configuration methods
  static getConfigElement() {
    return document.createElement('roo-card-editor');
  }

  static getStubConfig() {
    return {
      title: "Roo Assistant",
      zones: [],
      sections: ["notifications", "spaces", "todos", "performance"],
      layout: "default",
      update_interval: 30,
      show_images: true,
      theme: "auto"
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = { ...RooCard.getStubConfig(), ...config };
  }

  getCardSize() {
    return 6; // Standard card height units
  }
}

// Register the card with Home Assistant
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'roo-card',
  name: 'Roo AI Cleaning Assistant',
  description: 'Comprehensive dashboard for multi-zone home management',
  preview: true,
  documentationURL: 'https://github.com/sporebattyl/Aiclean'
});

console.info(
  '%c🤖 ROO-CARD %c2.0.0 ',
  'color: orange; font-weight: bold; background: black',
  'color: white; font-weight: bold; background: dimgray',
);
