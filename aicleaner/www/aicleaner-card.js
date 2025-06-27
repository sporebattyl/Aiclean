/**
 * AICleaner Custom Lovelace Card
 * 
 * A comprehensive Home Assistant Lovelace card for managing AICleaner v2.0
 * Features: Zone management, task tracking, analytics, and configuration
 */

class AICleanerCard extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this._config = {};
        this._hass = {};
        this.currentView = 'dashboard'; // dashboard, zone, config, analytics
        this.selectedZone = null;
        this.autoRefreshInterval = null;
        this.isLoading = false;
        this.lastUpdateTime = null;

        // Initialize default data structures for TDD
        this.zones = [];
        this.systemStatus = {
            status: 'inactive',
            totalZones: 0,
            totalActiveTasks: 0,
            totalCompletedTasks: 0,
            globalCompletionRate: 0,
            version: '2.0'
        };
    }

    /**
     * Called when the card configuration is set
     */
    setConfig(config) {
        if (!config) {
            throw new Error('Invalid configuration');
        }
        
        this._config = {
            title: config.title || 'AICleaner',
            zones: config.zones || [],
            show_analytics: config.show_analytics !== false,
            show_config: config.show_config !== false,
            theme: config.theme || 'default',
            ...config
        };
        
        this.render();
    }

    /**
     * Called when Home Assistant state updates
     */
    set hass(hass) {
        this._hass = hass;
        this.updateData();
        this.render();
    }

    /**
     * Extract data from Home Assistant entities
     */
    updateData() {
        this.zones = [];
        this.systemStatus = {};

        // Ensure we have hass and states
        if (!this._hass || !this._hass.states) {
            return;
        }

        // Get zone data from sensors
        Object.keys(this._hass.states).forEach(entityId => {
            if (entityId.startsWith('sensor.aicleaner_') && entityId.endsWith('_tasks')) {
                const zoneName = entityId.replace('sensor.aicleaner_', '').replace('_tasks', '');
                const entity = this._hass.states[entityId];
                
                if (entity && entity.attributes) {
                    this.zones.push({
                        name: zoneName,
                        displayName: entity.attributes.zone_name || zoneName,
                        tasks: entity.attributes.tasks || [],
                        activeTasks: entity.attributes.active_tasks || 0,
                        completedTasks: entity.attributes.completed_tasks || 0,
                        completionRate: entity.attributes.completion_rate || 0,
                        efficiencyScore: entity.attributes.efficiency_score || 0,
                        lastAnalysis: entity.attributes.last_analysis,
                        status: entity.state,
                        camera: entity.attributes.camera_entity,
                        purpose: entity.attributes.purpose
                    });
                }
            }
        });
        
        // Get system status
        const systemEntity = this._hass.states['sensor.aicleaner_system_status'];
        if (systemEntity) {
            this.systemStatus = {
                status: systemEntity.state,
                totalZones: systemEntity.attributes.total_zones || 0,
                totalActiveTasks: systemEntity.attributes.total_active_tasks || 0,
                totalCompletedTasks: systemEntity.attributes.total_completed_tasks || 0,
                globalCompletionRate: systemEntity.attributes.global_completion_rate || 0,
                averageEfficiencyScore: systemEntity.attributes.average_efficiency_score || 0,
                lastGlobalAnalysis: systemEntity.attributes.last_analysis,
                version: systemEntity.attributes.version || '2.0'
            };
        }
    }

    /**
     * Main render method
     */
    render() {
        if (!this.shadowRoot) return;
        
        this.shadowRoot.innerHTML = `
            ${this.getStyles()}
            <div class="aicleaner-card">
                ${this.renderHeader()}
                ${this.renderNavigation()}
                ${this.renderContent()}
            </div>
        `;

        this.attachEventListeners();

        // Initialize charts if we're on the analytics view
        if (this.currentView === 'analytics') {
            // Delay chart initialization to ensure DOM is ready
            setTimeout(() => this.initializeCharts(), 100);
        }
    }

    /**
     * CSS Styles for the card
     */
    getStyles() {
        return `
            <style>
                .aicleaner-card {
                    background: var(--card-background-color, #fff);
                    border-radius: var(--ha-card-border-radius, 12px);
                    box-shadow: var(--ha-card-box-shadow, 0 2px 8px rgba(0,0,0,0.1));
                    padding: 16px;
                    font-family: var(--paper-font-body1_-_font-family);
                    color: var(--primary-text-color);
                }
                
                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 16px;
                    padding-bottom: 12px;
                    border-bottom: 1px solid var(--divider-color);
                }
                
                .title {
                    font-size: 1.5em;
                    font-weight: 500;
                    color: var(--primary-text-color);
                }
                
                .system-status {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 0.9em;
                    color: var(--secondary-text-color);
                }

                .status-indicator {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: var(--success-color, #4caf50);
                    position: relative;
                    animation: pulse 2s infinite;
                }

                .status-indicator.warning {
                    background: var(--warning-color, #ff9800);
                    animation: pulse-warning 1.5s infinite;
                }

                .status-indicator.error {
                    background: var(--error-color, #f44336);
                    animation: pulse-error 1s infinite;
                }

                .status-indicator.inactive {
                    background: var(--disabled-text-color, #999);
                    animation: none;
                }

                .system-metrics {
                    display: flex;
                    gap: 16px;
                    align-items: center;
                }

                .metric-item {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    font-size: 0.85em;
                }

                .metric-icon {
                    font-size: 0.9em;
                    opacity: 0.8;
                }

                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.6; }
                }

                @keyframes pulse-warning {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.4; }
                }

                @keyframes pulse-error {
                    0%, 100% { opacity: 1; }
                    25%, 75% { opacity: 0.3; }
                }

                .quick-actions-panel {
                    background: var(--card-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 20px;
                }

                .quick-actions-title {
                    font-size: 1.1em;
                    font-weight: 600;
                    margin-bottom: 12px;
                    color: var(--primary-text-color);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .quick-actions-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 12px;
                }

                .quick-action-btn {
                    padding: 16px;
                    border: none;
                    border-radius: 8px;
                    background: var(--secondary-background-color);
                    color: var(--primary-text-color);
                    cursor: pointer;
                    transition: all 0.2s ease;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                    text-align: center;
                    border: 1px solid var(--divider-color);
                }

                .quick-action-btn:hover {
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }

                .quick-action-icon {
                    font-size: 1.5em;
                }

                .quick-action-label {
                    font-size: 0.9em;
                    font-weight: 500;
                }

                .quick-action-desc {
                    font-size: 0.75em;
                    opacity: 0.8;
                    line-height: 1.2;
                }

                .quick-action-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                    transform: none !important;
                    box-shadow: none !important;
                }

                .quick-action-btn:disabled:hover {
                    background: var(--secondary-background-color);
                    color: var(--primary-text-color);
                }

                /* Zone Detail View Styles */
                .zone-detail-header {
                    margin-bottom: 24px;
                }

                .back-button {
                    background: var(--secondary-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 8px;
                    padding: 8px 16px;
                    color: var(--primary-text-color);
                    cursor: pointer;
                    margin-bottom: 16px;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                }

                .back-button:hover {
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                }

                .zone-detail-title {
                    display: flex;
                    align-items: center;
                    gap: 16px;
                }

                .zone-detail-icon {
                    font-size: 2.5em;
                }

                .zone-detail-title h2 {
                    margin: 0;
                    font-size: 1.8em;
                    color: var(--primary-text-color);
                }

                .zone-purpose {
                    margin: 4px 0 0 0;
                    color: var(--secondary-text-color);
                    font-style: italic;
                }

                .zone-detail-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    grid-template-rows: auto auto;
                    gap: 20px;
                }

                .zone-stats-panel,
                .zone-tasks-panel,
                .zone-controls-panel {
                    background: var(--card-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 12px;
                    padding: 20px;
                }

                .zone-tasks-panel {
                    grid-row: span 2;
                }

                .zone-detail-grid h3 {
                    margin: 0 0 16px 0;
                    font-size: 1.1em;
                    color: var(--primary-text-color);
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 12px;
                    margin-bottom: 16px;
                }

                .stat-card {
                    background: var(--secondary-background-color);
                    border-radius: 8px;
                    padding: 16px;
                    text-align: center;
                }

                .stat-value {
                    font-size: 1.8em;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin-bottom: 4px;
                }

                .stat-label {
                    font-size: 0.8em;
                    color: var(--secondary-text-color);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .last-analysis-info {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9em;
                    color: var(--secondary-text-color);
                    background: var(--secondary-background-color);
                    padding: 12px;
                    border-radius: 8px;
                }

                /* Task List Styles */
                .no-tasks {
                    text-align: center;
                    padding: 40px 20px;
                    color: var(--secondary-text-color);
                }

                .no-tasks-icon {
                    font-size: 3em;
                    margin-bottom: 12px;
                }

                .no-tasks-text {
                    font-size: 1.2em;
                    font-weight: 500;
                    margin-bottom: 4px;
                }

                .no-tasks-desc {
                    font-size: 0.9em;
                    opacity: 0.8;
                }

                .task-list {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    max-height: 400px;
                    overflow-y: auto;
                }

                .task-item {
                    background: var(--secondary-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 8px;
                    padding: 16px;
                    transition: all 0.2s ease;
                }

                .task-item:hover {
                    border-color: var(--primary-color);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }

                .task-content {
                    margin-bottom: 12px;
                }

                .task-header {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 6px;
                }

                .task-priority {
                    font-size: 0.9em;
                }

                .task-description {
                    flex: 1;
                    font-weight: 500;
                    color: var(--primary-text-color);
                }

                .task-meta {
                    font-size: 0.8em;
                    color: var(--secondary-text-color);
                }

                .task-actions {
                    display: flex;
                    gap: 8px;
                }

                .task-action-btn {
                    flex: 1;
                    padding: 8px 12px;
                    border: none;
                    border-radius: 6px;
                    font-size: 0.8em;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .task-action-btn.complete {
                    background: var(--success-color, #4caf50);
                    color: white;
                }

                .task-action-btn.dismiss {
                    background: var(--secondary-background-color);
                    color: var(--secondary-text-color);
                    border: 1px solid var(--divider-color);
                }

                .task-action-btn:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
                }

                /* Zone Controls Styles */
                .zone-controls {
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }

                .control-btn {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 16px;
                    border: 1px solid var(--divider-color);
                    border-radius: 8px;
                    background: var(--secondary-background-color);
                    color: var(--primary-text-color);
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-align: left;
                }

                .control-btn:hover {
                    border-color: var(--primary-color);
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                    transform: translateY(-1px);
                }

                .control-btn.primary {
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                    border-color: var(--primary-color);
                }

                .control-icon {
                    font-size: 1.2em;
                    min-width: 24px;
                }

                .control-content {
                    flex: 1;
                }

                .control-label {
                    font-weight: 500;
                    margin-bottom: 2px;
                }

                .control-desc {
                    font-size: 0.8em;
                    opacity: 0.8;
                }

                /* Configuration Panel Styles */
                .config-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                }

                .config-section {
                    background: var(--card-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 12px;
                    padding: 20px;
                }

                .config-section h3 {
                    margin: 0 0 16px 0;
                    font-size: 1.1em;
                    color: var(--primary-text-color);
                }

                .personality-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 12px;
                    margin-bottom: 16px;
                }

                .personality-card {
                    background: var(--secondary-background-color);
                    border: 2px solid var(--divider-color);
                    border-radius: 8px;
                    padding: 16px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .personality-card:hover {
                    border-color: var(--primary-color);
                    transform: translateY(-2px);
                }

                .personality-card.selected {
                    border-color: var(--primary-color);
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                }

                .personality-icon {
                    font-size: 1.5em;
                    margin-bottom: 8px;
                }

                .personality-name {
                    font-weight: 500;
                    margin-bottom: 4px;
                }

                .personality-desc {
                    font-size: 0.8em;
                    opacity: 0.8;
                }

                .config-input-group {
                    margin-bottom: 16px;
                }

                .config-label {
                    display: block;
                    margin-bottom: 6px;
                    font-weight: 500;
                    color: var(--primary-text-color);
                }

                .config-input {
                    width: 100%;
                    padding: 10px;
                    border: 1px solid var(--divider-color);
                    border-radius: 6px;
                    background: var(--secondary-background-color);
                    color: var(--primary-text-color);
                    font-size: 0.9em;
                }

                .config-input:focus {
                    outline: none;
                    border-color: var(--primary-color);
                }

                .config-checkbox {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 12px;
                }

                .config-checkbox input {
                    width: auto;
                }

                .ignore-rule-item {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 8px;
                    background: var(--secondary-background-color);
                    border-radius: 6px;
                    margin-bottom: 8px;
                }

                .ignore-rule-text {
                    flex: 1;
                    font-size: 0.9em;
                }

                .remove-rule-btn {
                    background: var(--error-color, #f44336);
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 4px 8px;
                    cursor: pointer;
                    font-size: 0.8em;
                }

                .add-rule-form {
                    display: flex;
                    gap: 8px;
                    margin-top: 12px;
                }

                .add-rule-input {
                    flex: 1;
                }

                .add-rule-btn {
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                    border: none;
                    border-radius: 6px;
                    padding: 10px 16px;
                    cursor: pointer;
                    font-size: 0.9em;
                }

                /* Analytics Dashboard Styles */
                .analytics-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 20px;
                }

                .analytics-section {
                    background: var(--card-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 12px;
                    padding: 20px;
                }

                .analytics-section h3 {
                    margin: 0 0 16px 0;
                    font-size: 1.1em;
                    color: var(--primary-text-color);
                }

                .chart-container {
                    position: relative;
                    height: 300px;
                    width: 100%;
                }

                .chart-container canvas {
                    max-height: 100%;
                    max-width: 100%;
                }

                .insights-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 16px;
                }

                .insight-card {
                    background: var(--secondary-background-color);
                    border-radius: 8px;
                    padding: 16px;
                    text-align: center;
                }

                .insight-value {
                    font-size: 1.8em;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin-bottom: 4px;
                }

                .insight-label {
                    font-size: 0.8em;
                    color: var(--secondary-text-color);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .insight-trend {
                    font-size: 0.75em;
                    margin-top: 4px;
                }

                .insight-trend.up {
                    color: var(--success-color, #4caf50);
                }

                .insight-trend.down {
                    color: var(--error-color, #f44336);
                }

                .insight-trend.neutral {
                    color: var(--secondary-text-color);
                }
                
                .navigation {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 16px;
                }
                
                .nav-button {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 20px;
                    background: var(--secondary-background-color);
                    color: var(--secondary-text-color);
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-size: 0.9em;
                }
                
                .nav-button:hover {
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                }
                
                .nav-button.active {
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                }
                
                .content {
                    min-height: 200px;
                }
                
                .zone-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 16px;
                    margin-top: 8px;
                }

                .zone-card {
                    background: var(--card-background-color);
                    border: 1px solid var(--divider-color);
                    border-radius: 12px;
                    padding: 20px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }

                .zone-card:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                    border-color: var(--primary-color);
                }

                .zone-card::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 4px;
                    background: linear-gradient(90deg, var(--primary-color), var(--accent-color, var(--primary-color)));
                }
                
                .zone-name {
                    font-size: 1.3em;
                    font-weight: 600;
                    margin-bottom: 12px;
                    color: var(--primary-text-color);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .zone-icon {
                    font-size: 1.1em;
                    opacity: 0.8;
                }

                .zone-stats {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 12px;
                    margin-bottom: 16px;
                }

                .stat-item {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 12px;
                    background: var(--secondary-background-color);
                    border-radius: 8px;
                    transition: background 0.2s ease;
                }

                .stat-number {
                    font-size: 1.8em;
                    font-weight: 700;
                    line-height: 1;
                    margin-bottom: 4px;
                }

                .stat-label {
                    font-size: 0.8em;
                    color: var(--secondary-text-color);
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }

                .stat-item.active .stat-number { color: var(--warning-color, #ff9800); }
                .stat-item.completed .stat-number { color: var(--success-color, #4caf50); }
                
                .zone-progress {
                    margin-bottom: 16px;
                }

                .progress-bar {
                    width: 100%;
                    height: 6px;
                    background: var(--divider-color);
                    border-radius: 3px;
                    overflow: hidden;
                    margin-bottom: 6px;
                }

                .progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, var(--success-color), var(--primary-color));
                    transition: width 0.3s ease;
                }

                .progress-text {
                    font-size: 0.8em;
                    color: var(--secondary-text-color);
                    text-align: center;
                }

                .efficiency-score {
                    font-size: 0.75em;
                    color: var(--primary-color);
                    text-align: center;
                    margin-top: 4px;
                    font-weight: 500;
                }

                .efficiency-icon {
                    margin-right: 4px;
                }

                .last-analysis {
                    font-size: 0.85em;
                    color: var(--secondary-text-color);
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    margin-bottom: 16px;
                    padding: 8px;
                    background: var(--secondary-background-color);
                    border-radius: 6px;
                }

                .analysis-icon {
                    opacity: 0.7;
                }
                
                .quick-actions {
                    display: flex;
                    gap: 8px;
                    margin-top: 12px;
                }
                
                .action-button {
                    flex: 1;
                    padding: 12px 16px;
                    border: none;
                    border-radius: 8px;
                    background: var(--primary-color);
                    color: var(--text-primary-color);
                    cursor: pointer;
                    font-size: 0.85em;
                    font-weight: 500;
                    transition: all 0.2s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                }

                .action-button:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                }

                .action-button.secondary {
                    background: var(--secondary-background-color);
                    color: var(--primary-text-color);
                    border: 1px solid var(--divider-color);
                }

                .action-button.secondary:hover {
                    background: var(--divider-color);
                }

                .button-icon {
                    font-size: 0.9em;
                }
                
                @media (max-width: 768px) {
                    .zone-grid {
                        grid-template-columns: 1fr;
                    }

                    .navigation {
                        flex-wrap: wrap;
                    }

                    .nav-button {
                        flex: 1;
                        min-width: 80px;
                    }

                    .system-metrics {
                        flex-direction: column;
                        gap: 8px;
                        align-items: flex-start;
                    }

                    .quick-actions-grid {
                        grid-template-columns: 1fr 1fr;
                    }

                    .zone-detail-grid {
                        grid-template-columns: 1fr;
                        grid-template-rows: auto;
                    }

                    .zone-tasks-panel {
                        grid-row: auto;
                    }

                    .stats-grid {
                        grid-template-columns: 1fr 1fr;
                    }

                    .task-actions {
                        flex-direction: column;
                    }

                    .zone-detail-title {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 12px;
                    }

                    .zone-detail-icon {
                        font-size: 2em;
                    }
                }

                @media (max-width: 480px) {
                    .quick-actions-grid {
                        grid-template-columns: 1fr;
                    }

                    .stats-grid {
                        grid-template-columns: 1fr;
                    }

                    .system-metrics {
                        display: none;
                    }

                    .zone-card {
                        padding: 16px;
                    }

                    .zone-stats {
                        grid-template-columns: 1fr;
                        gap: 8px;
                    }
                }
            </style>
        `;
    }

    /**
     * Render the card header
     */
    renderHeader() {
        const status = this.systemStatus.status || 'inactive';
        const statusClass = status === 'active' ? '' :
                           status === 'busy' ? 'warning' :
                           status === 'warning' ? 'warning' :
                           status === 'inactive' ? 'inactive' : 'error';

        const statusText = {
            'active': 'System Active',
            'busy': 'System Busy',
            'warning': 'Needs Attention',
            'error': 'System Error',
            'inactive': 'System Inactive'
        }[status] || 'Unknown Status';

        const lastAnalysis = this.systemStatus.lastGlobalAnalysis ?
            this.formatRelativeTime(new Date(this.systemStatus.lastGlobalAnalysis)) : 'Never';

        return `
            <div class="header">
                <div class="title">${this._config.title}</div>
                <div class="system-status">
                    <div class="status-indicator ${statusClass}" title="${statusText}"></div>
                    <div class="system-metrics">
                        <div class="metric-item">
                            <span class="metric-icon">🏠</span>
                            <span>${this.systemStatus.totalZones || 0} zones</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-icon">📋</span>
                            <span>${this.systemStatus.totalActiveTasks || 0} active</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-icon">✅</span>
                            <span>${this.systemStatus.totalCompletedTasks || 0} completed</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-icon">🕒</span>
                            <span>${lastAnalysis}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render navigation buttons
     */
    renderNavigation() {
        const views = [
            { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
            { id: 'analytics', label: 'Analytics', icon: '📊' },
            { id: 'config', label: 'Settings', icon: '⚙️' }
        ];
        
        return `
            <div class="navigation">
                ${views.map(view => `
                    <button class="nav-button ${this.currentView === view.id ? 'active' : ''}" 
                            data-view="${view.id}">
                        ${view.icon} ${view.label}
                    </button>
                `).join('')}
            </div>
        `;
    }

    /**
     * Render main content based on current view
     */
    renderContent() {
        switch (this.currentView) {
            case 'dashboard':
                return this.renderDashboard();
            case 'zone':
                return this.renderZoneDetail();
            case 'analytics':
                return this.renderAnalytics();
            case 'config':
                return this.renderConfig();
            default:
                return this.renderDashboard();
        }
    }

    /**
     * Render dashboard view with zone overview
     */
    renderDashboard() {
        if (!this.zones || this.zones.length === 0) {
            return `
                <div class="content">
                    <div style="text-align: center; padding: 40px; color: var(--secondary-text-color);">
                        <div style="font-size: 3em; margin-bottom: 16px;">🏠</div>
                        <div style="font-size: 1.2em; margin-bottom: 8px;">No zones configured</div>
                        <div>Add zones in your AICleaner configuration to get started</div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="content">
                ${this.renderQuickActions()}
                <div class="zone-grid">
                    ${this.zones.map(zone => this.renderZoneCard(zone)).join('')}
                </div>
            </div>
        `;
    }

    /**
     * Render quick actions panel
     */
    renderQuickActions() {
        const totalActiveTasks = this.systemStatus.totalActiveTasks || 0;
        const hasZones = this.zones && this.zones.length > 0;

        return `
            <div class="quick-actions-panel">
                <div class="quick-actions-title">
                    <span>⚡</span>
                    Quick Actions
                </div>
                <div class="quick-actions-grid">
                    <button class="quick-action-btn" data-action="analyze-all" ${!hasZones ? 'disabled' : ''}>
                        <div class="quick-action-icon">🔍</div>
                        <div class="quick-action-label">Analyze All Zones</div>
                        <div class="quick-action-desc">Run analysis on all configured zones</div>
                    </button>
                    <button class="quick-action-btn" data-action="refresh">
                        <div class="quick-action-icon">🔄</div>
                        <div class="quick-action-label">Refresh Data</div>
                        <div class="quick-action-desc">Update all sensor data from Home Assistant</div>
                    </button>
                    <button class="quick-action-btn" data-action="complete-all" ${totalActiveTasks === 0 ? 'disabled' : ''}>
                        <div class="quick-action-icon">✅</div>
                        <div class="quick-action-label">Mark All Complete</div>
                        <div class="quick-action-desc">Mark all active tasks as completed</div>
                    </button>
                    <button class="quick-action-btn" data-action="system-info">
                        <div class="quick-action-icon">ℹ️</div>
                        <div class="quick-action-label">System Info</div>
                        <div class="quick-action-desc">View system status and diagnostics</div>
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render individual zone card
     */
    renderZoneCard(zone) {
        const lastAnalysis = zone.lastAnalysis ?
            this.formatRelativeTime(new Date(zone.lastAnalysis)) : 'Never';

        // Get zone icon or use default
        const zoneIcon = this.getZoneIcon(zone.name);

        // Use completion rate from zone data or calculate if not available
        const completionRate = zone.completionRate !== undefined ?
            Math.round(zone.completionRate * 100) :
            (() => {
                const totalTasks = zone.activeTasks + zone.completedTasks;
                return totalTasks > 0 ? Math.round((zone.completedTasks / totalTasks) * 100) : 0;
            })();

        return `
            <div class="zone-card" data-zone="${zone.name}">
                <div class="zone-name">
                    <span class="zone-icon">${zoneIcon}</span>
                    ${zone.displayName}
                </div>
                <div class="zone-stats">
                    <div class="stat-item active">
                        <div class="stat-number">${zone.activeTasks}</div>
                        <div class="stat-label">Active</div>
                    </div>
                    <div class="stat-item completed">
                        <div class="stat-number">${zone.completedTasks}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                </div>
                <div class="zone-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${completionRate}%"></div>
                    </div>
                    <div class="progress-text">${completionRate}% completion rate</div>
                    ${zone.efficiencyScore !== undefined ? `
                        <div class="efficiency-score">
                            <span class="efficiency-icon">⚡</span>
                            ${Math.round(zone.efficiencyScore * 100)}% efficiency
                        </div>
                    ` : ''}
                </div>
                <div class="last-analysis">
                    <span class="analysis-icon">🕒</span>
                    Last analysis: ${lastAnalysis}
                </div>
                <div class="quick-actions">
                    <button class="action-button" data-action="analyze" data-zone="${zone.name}">
                        <span class="button-icon">🔍</span>
                        Analyze Now
                    </button>
                    <button class="action-button secondary" data-action="view" data-zone="${zone.name}">
                        <span class="button-icon">👁️</span>
                        View Details
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render zone detail view
     */
    renderZoneDetail() {
        if (!this.selectedZone) {
            return this.renderDashboard();
        }

        const zone = this.zones.find(z => z.name === this.selectedZone);
        if (!zone) {
            return this.renderDashboard();
        }

        const zoneIcon = this.getZoneIcon(zone.name);
        const lastAnalysis = zone.lastAnalysis ?
            this.formatRelativeTime(new Date(zone.lastAnalysis)) : 'Never';

        return `
            <div class="content">
                <div class="zone-detail-header">
                    <button class="back-button" data-action="back">
                        <span>←</span> Back to Dashboard
                    </button>
                    <div class="zone-detail-title">
                        <span class="zone-detail-icon">${zoneIcon}</span>
                        <div>
                            <h2>${zone.displayName}</h2>
                            <p class="zone-purpose">${zone.purpose || 'Keep everything tidy and clean'}</p>
                        </div>
                    </div>
                </div>

                <div class="zone-detail-grid">
                    <div class="zone-stats-panel">
                        <h3>📊 Zone Statistics</h3>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${zone.activeTasks}</div>
                                <div class="stat-label">Active Tasks</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${zone.completedTasks}</div>
                                <div class="stat-label">Completed</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${Math.round((zone.completionRate || 0) * 100)}%</div>
                                <div class="stat-label">Completion Rate</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${Math.round((zone.efficiencyScore || 0) * 100)}%</div>
                                <div class="stat-label">Efficiency</div>
                            </div>
                        </div>
                        <div class="last-analysis-info">
                            <span class="analysis-icon">🕒</span>
                            Last analysis: ${lastAnalysis}
                        </div>
                    </div>

                    <div class="zone-tasks-panel">
                        <h3>📋 Active Tasks</h3>
                        ${this.renderTaskList(zone)}
                    </div>

                    <div class="zone-controls-panel">
                        <h3>⚙️ Zone Controls</h3>
                        ${this.renderZoneControls(zone)}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render task list for zone detail view
     */
    renderTaskList(zone) {
        const tasks = zone.tasks || [];

        if (tasks.length === 0) {
            return `
                <div class="no-tasks">
                    <div class="no-tasks-icon">✨</div>
                    <div class="no-tasks-text">No active tasks</div>
                    <div class="no-tasks-desc">This zone is all clean!</div>
                </div>
            `;
        }

        return `
            <div class="task-list">
                ${tasks.map(task => this.renderTaskItem(task, zone.name)).join('')}
            </div>
        `;
    }

    /**
     * Render individual task item
     */
    renderTaskItem(task, zoneName) {
        const priority = task.priority || 'normal';
        const priorityIcon = {
            'high': '🔴',
            'normal': '🟡',
            'low': '🟢'
        }[priority] || '🟡';

        const createdAt = task.created_at ?
            this.formatRelativeTime(new Date(task.created_at)) : 'Unknown';

        return `
            <div class="task-item" data-task-id="${task.id}">
                <div class="task-content">
                    <div class="task-header">
                        <span class="task-priority">${priorityIcon}</span>
                        <span class="task-description">${task.description}</span>
                    </div>
                    <div class="task-meta">
                        <span class="task-created">Created ${createdAt}</span>
                    </div>
                </div>
                <div class="task-actions">
                    <button class="task-action-btn complete" data-action="complete-task" data-task-id="${task.id}" data-zone="${zoneName}">
                        ✅ Complete
                    </button>
                    <button class="task-action-btn dismiss" data-action="dismiss-task" data-task-id="${task.id}" data-zone="${zoneName}">
                        ❌ Dismiss
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render zone controls panel
     */
    renderZoneControls(zone) {
        return `
            <div class="zone-controls">
                <button class="control-btn primary" data-action="analyze" data-zone="${zone.name}">
                    <span class="control-icon">🔍</span>
                    <div class="control-content">
                        <div class="control-label">Analyze Zone</div>
                        <div class="control-desc">Run AI analysis now</div>
                    </div>
                </button>

                <button class="control-btn" data-action="view-camera" data-zone="${zone.name}">
                    <span class="control-icon">📷</span>
                    <div class="control-content">
                        <div class="control-label">View Camera</div>
                        <div class="control-desc">See current snapshot</div>
                    </div>
                </button>

                <button class="control-btn" data-action="zone-settings" data-zone="${zone.name}">
                    <span class="control-icon">⚙️</span>
                    <div class="control-content">
                        <div class="control-label">Zone Settings</div>
                        <div class="control-desc">Configure this zone</div>
                    </div>
                </button>
            </div>
        `;
    }

    /**
     * Render analytics view with real charts
     */
    renderAnalytics() {
        return `
            <div class="content">
                <div class="analytics-grid">
                    <div class="analytics-section">
                        <h3>📈 Task Completion Trends</h3>
                        <div class="chart-container">
                            <canvas id="completion-trend-chart"></canvas>
                        </div>
                    </div>

                    <div class="analytics-section">
                        <h3>🏆 Zone Performance</h3>
                        <div class="chart-container">
                            <canvas id="zone-performance-chart"></canvas>
                        </div>
                    </div>

                    <div class="analytics-section">
                        <h3>📊 System Insights</h3>
                        ${this.renderSystemInsights()}
                    </div>

                    <div class="analytics-section">
                        <h3>⏱️ Activity Timeline</h3>
                        <div class="chart-container">
                            <canvas id="activity-timeline-chart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render configuration view
     */
    renderConfig() {
        return `
            <div class="content">
                <div class="config-grid">
                    <div class="config-section">
                        <h3>🔔 Notification Settings</h3>
                        ${this.renderNotificationSettings()}
                    </div>

                    <div class="config-section">
                        <h3>🚫 Ignore Rules</h3>
                        ${this.renderIgnoreRules()}
                    </div>

                    <div class="config-section">
                        <h3>⏰ Analysis Schedule</h3>
                        ${this.renderScheduleSettings()}
                    </div>

                    <div class="config-section">
                        <h3>🔧 System Settings</h3>
                        ${this.renderSystemSettings()}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render notification personality selector
     */
    renderNotificationSettings() {
        const personalities = [
            { id: 'default', name: 'Default', icon: '🤖', desc: 'Standard notifications' },
            { id: 'snarky', name: 'Snarky', icon: '😏', desc: 'Witty and sarcastic' },
            { id: 'jarvis', name: 'Jarvis', icon: '🎩', desc: 'Professional assistant' },
            { id: 'roaster', name: 'Roaster', icon: '🔥', desc: 'Playfully critical' },
            { id: 'butler', name: 'Butler', icon: '🤵', desc: 'Formal and polite' },
            { id: 'coach', name: 'Coach', icon: '💪', desc: 'Motivational' },
            { id: 'zen', name: 'Zen', icon: '🧘', desc: 'Calm and mindful' }
        ];

        const currentPersonality = this.getCurrentPersonality();

        return `
            <div class="personality-grid">
                ${personalities.map(p => `
                    <div class="personality-card ${p.id === currentPersonality ? 'selected' : ''}"
                         data-personality="${p.id}">
                        <div class="personality-icon">${p.icon}</div>
                        <div class="personality-name">${p.name}</div>
                        <div class="personality-desc">${p.desc}</div>
                    </div>
                `).join('')}
            </div>
            <div class="config-checkbox">
                <input type="checkbox" id="notifications-enabled" checked>
                <label for="notifications-enabled">Enable notifications</label>
            </div>
        `;
    }

    /**
     * Render ignore rules management
     */
    renderIgnoreRules() {
        const ignoreRules = this.getIgnoreRules();

        return `
            <div class="ignore-rules-list">
                ${ignoreRules.map((rule, index) => `
                    <div class="ignore-rule-item">
                        <span class="ignore-rule-text">${rule}</span>
                        <button class="remove-rule-btn" data-rule-index="${index}">Remove</button>
                    </div>
                `).join('')}
                ${ignoreRules.length === 0 ? '<div style="color: var(--secondary-text-color); font-style: italic;">No ignore rules configured</div>' : ''}
            </div>
            <div class="add-rule-form">
                <input type="text" class="config-input add-rule-input" placeholder="Enter item to ignore (e.g., 'pet toys', 'decorative items')">
                <button class="add-rule-btn">Add Rule</button>
            </div>
        `;
    }

    /**
     * Render schedule settings
     */
    renderScheduleSettings() {
        return `
            <div class="config-input-group">
                <label class="config-label">Analysis Frequency</label>
                <select class="config-input" id="analysis-frequency">
                    <option value="15">Every 15 minutes</option>
                    <option value="30" selected>Every 30 minutes</option>
                    <option value="60">Every hour</option>
                    <option value="120">Every 2 hours</option>
                    <option value="240">Every 4 hours</option>
                </select>
            </div>
            <div class="config-checkbox">
                <input type="checkbox" id="auto-analysis" checked>
                <label for="auto-analysis">Enable automatic analysis</label>
            </div>
            <div class="config-checkbox">
                <input type="checkbox" id="quiet-hours">
                <label for="quiet-hours">Enable quiet hours (10 PM - 7 AM)</label>
            </div>
        `;
    }

    /**
     * Render system settings
     */
    renderSystemSettings() {
        return `
            <div class="config-input-group">
                <label class="config-label">AI Confidence Threshold</label>
                <input type="range" class="config-input" min="0.1" max="1.0" step="0.1" value="0.7" id="confidence-threshold">
                <div style="font-size: 0.8em; color: var(--secondary-text-color);">Current: 70%</div>
            </div>
            <div class="config-input-group">
                <label class="config-label">Max Tasks Per Zone</label>
                <input type="number" class="config-input" min="1" max="20" value="10" id="max-tasks">
            </div>
            <div class="config-checkbox">
                <input type="checkbox" id="debug-mode">
                <label for="debug-mode">Enable debug logging</label>
            </div>
            <div style="margin-top: 16px;">
                <button class="control-btn primary" data-action="save-settings">
                    <span class="control-icon">💾</span>
                    <div class="control-content">
                        <div class="control-label">Save Settings</div>
                        <div class="control-desc">Apply configuration changes</div>
                    </div>
                </button>
            </div>
        `;
    }

    /**
     * Get current notification personality
     */
    getCurrentPersonality() {
        // In a real implementation, this would read from the system state
        return 'default';
    }

    /**
     * Get current ignore rules
     */
    getIgnoreRules() {
        // In a real implementation, this would read from the system state
        return ['pet toys', 'decorative plants', 'artwork'];
    }

    /**
     * Render system insights panel
     */
    renderSystemInsights() {
        const totalTasks = this.systemStatus.totalActiveTasks + this.systemStatus.totalCompletedTasks;
        const completionRate = totalTasks > 0 ? Math.round((this.systemStatus.totalCompletedTasks / totalTasks) * 100) : 0;
        const avgEfficiency = Math.round((this.systemStatus.averageEfficiencyScore || 0) * 100);

        // Calculate uptime (mock data for now)
        const uptimeHours = 24 * 7; // Mock 7 days uptime
        const analysisCount = this.zones.length * 48; // Mock analysis count

        return `
            <div class="insights-grid">
                <div class="insight-card">
                    <div class="insight-value">${completionRate}%</div>
                    <div class="insight-label">Completion Rate</div>
                    <div class="insight-trend up">↗ +5% this week</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${avgEfficiency}%</div>
                    <div class="insight-label">Avg Efficiency</div>
                    <div class="insight-trend neutral">→ Stable</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${uptimeHours}h</div>
                    <div class="insight-label">System Uptime</div>
                    <div class="insight-trend up">↗ 99.9%</div>
                </div>
                <div class="insight-card">
                    <div class="insight-value">${analysisCount}</div>
                    <div class="insight-label">Analyses Run</div>
                    <div class="insight-trend up">↗ +12 today</div>
                </div>
            </div>
        `;
    }

    /**
     * Initialize charts after render
     */
    initializeCharts() {
        // Load Chart.js if not already loaded
        if (typeof Chart === 'undefined') {
            this.loadChartJS().then(() => {
                this.createCharts();
            });
        } else {
            this.createCharts();
        }
    }

    /**
     * Load Chart.js library
     */
    loadChartJS() {
        return new Promise((resolve, reject) => {
            if (typeof Chart !== 'undefined') {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * Create all charts
     */
    createCharts() {
        try {
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js not loaded, skipping chart creation');
                return;
            }

            this.createCompletionTrendChart();
            this.createZonePerformanceChart();
            this.createActivityTimelineChart();
        } catch (error) {
            console.error('Error creating charts:', error);
        }
    }

    /**
     * Create task completion trend chart
     */
    createCompletionTrendChart() {
        try {
            const canvas = this.shadowRoot.getElementById('completion-trend-chart');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');

        // Generate mock data for the last 7 days
        const labels = [];
        const completedData = [];
        const activeData = [];

        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { weekday: 'short' }));

            // Mock data with some variation
            completedData.push(Math.floor(Math.random() * 10) + 5);
            activeData.push(Math.floor(Math.random() * 8) + 2);
        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Tasks Completed',
                    data: completedData,
                    borderColor: 'rgb(76, 175, 80)',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'New Tasks',
                    data: activeData,
                    borderColor: 'rgb(255, 152, 0)',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        });
        } catch (error) {
            console.error('Error creating completion trend chart:', error);
        }
    }

    /**
     * Create zone performance chart
     */
    createZonePerformanceChart() {
        const canvas = this.shadowRoot.getElementById('zone-performance-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Use real zone data
        const zoneNames = this.zones.map(zone => zone.displayName);
        const completionRates = this.zones.map(zone => Math.round((zone.completionRate || 0) * 100));
        const efficiencyScores = this.zones.map(zone => Math.round((zone.efficiencyScore || 0) * 100));

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: zoneNames,
                datasets: [{
                    label: 'Completion Rate (%)',
                    data: completionRates,
                    backgroundColor: 'rgba(76, 175, 80, 0.8)',
                    borderColor: 'rgb(76, 175, 80)',
                    borderWidth: 1
                }, {
                    label: 'Efficiency Score (%)',
                    data: efficiencyScores,
                    backgroundColor: 'rgba(33, 150, 243, 0.8)',
                    borderColor: 'rgb(33, 150, 243)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        });
    }

    /**
     * Create activity timeline chart
     */
    createActivityTimelineChart() {
        const canvas = this.shadowRoot.getElementById('activity-timeline-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Generate hourly activity data for today
        const hours = [];
        const activityData = [];

        for (let i = 0; i < 24; i++) {
            hours.push(`${i.toString().padStart(2, '0')}:00`);
            // Mock activity data with peaks during typical cleaning times
            let activity = Math.random() * 3;
            if (i >= 8 && i <= 10) activity += 5; // Morning cleaning
            if (i >= 14 && i <= 16) activity += 3; // Afternoon cleaning
            if (i >= 18 && i <= 20) activity += 4; // Evening cleaning
            activityData.push(Math.round(activity));
        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: hours,
                datasets: [{
                    label: 'Analysis Activity',
                    data: activityData,
                    borderColor: 'rgb(156, 39, 176)',
                    backgroundColor: 'rgba(156, 39, 176, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                }
            }
        });
    }

    /**
     * Attach event listeners for user interactions
     */
    attachEventListeners() {
        // Navigation buttons
        this.shadowRoot.querySelectorAll('.nav-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.currentView = e.target.dataset.view;
                this.render();
            });
        });

        // Zone cards
        this.shadowRoot.querySelectorAll('.zone-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.action-button')) {
                    this.selectedZone = e.currentTarget.dataset.zone;
                    this.currentView = 'zone';
                    this.render();
                }
            });
        });

        // Action buttons
        this.shadowRoot.querySelectorAll('.action-button').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = e.target.dataset.action;
                const zone = e.target.dataset.zone;
                this.handleAction(action, zone);
            });
        });

        // Quick action buttons
        this.shadowRoot.querySelectorAll('.quick-action-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = e.target.dataset.action;
                if (!e.target.disabled) {
                    this.handleQuickAction(action);
                }
            });
        });

        // Back button
        this.shadowRoot.querySelectorAll('.back-button').forEach(button => {
            button.addEventListener('click', (e) => {
                this.currentView = 'dashboard';
                this.selectedZone = null;
                this.render();
            });
        });

        // Task action buttons
        this.shadowRoot.querySelectorAll('.task-action-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = e.target.dataset.action;
                const taskId = e.target.dataset.taskId;
                const zone = e.target.dataset.zone;
                this.handleTaskAction(action, taskId, zone);
            });
        });

        // Control buttons
        this.shadowRoot.querySelectorAll('.control-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = e.target.dataset.action;
                const zone = e.target.dataset.zone;
                this.handleControlAction(action, zone);
            });
        });

        // Personality cards
        this.shadowRoot.querySelectorAll('.personality-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const personality = e.currentTarget.dataset.personality;
                this.selectPersonality(personality);
            });
        });

        // Add ignore rule button
        this.shadowRoot.querySelectorAll('.add-rule-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const input = this.shadowRoot.querySelector('.add-rule-input');
                if (input && input.value.trim()) {
                    this.addIgnoreRule(input.value.trim());
                    input.value = '';
                }
            });
        });

        // Remove ignore rule buttons
        this.shadowRoot.querySelectorAll('.remove-rule-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const ruleIndex = parseInt(e.target.dataset.ruleIndex);
                this.removeIgnoreRule(ruleIndex);
            });
        });
    }

    /**
     * Handle user actions
     */
    handleAction(action, zone) {
        switch (action) {
            case 'analyze':
                this.triggerAnalysis(zone);
                break;
            case 'view':
                this.selectedZone = zone;
                this.currentView = 'zone';
                this.render();
                break;
        }
    }

    /**
     * Handle quick action buttons
     */
    handleQuickAction(action) {
        switch (action) {
            case 'analyze-all':
                this.triggerAnalysisAll();
                break;
            case 'refresh':
                this.refreshData();
                break;
            case 'complete-all':
                this.completeAllTasks();
                break;
            case 'system-info':
                this.showSystemInfo();
                break;
        }
    }

    /**
     * Trigger zone analysis via Home Assistant service
     */
    triggerAnalysis(zoneName) {
        if (this._hass && this._hass.callService) {
            this._hass.callService('aicleaner', 'run_analysis', {
                zone: zoneName
            });

            // Show feedback
            this.showToast(`Analysis started for ${zoneName}`);
        }
    }

    /**
     * Trigger analysis for all zones
     */
    triggerAnalysisAll() {
        if (this._hass && this._hass.callService) {
            this._hass.callService('aicleaner', 'run_analysis', {});
            this.showToast(`Analysis started for all zones`);
        }
    }

    /**
     * Refresh data from Home Assistant
     */
    refreshData() {
        this.updateData();
        this.render();
        this.showToast('Data refreshed');
    }

    /**
     * Complete all active tasks
     */
    completeAllTasks() {
        if (this._hass && this._hass.callService) {
            // Call service to complete all tasks
            this._hass.callService('aicleaner', 'complete_all_tasks', {});
            this.showToast('Marking all tasks as completed');
        }
    }

    /**
     * Show system information dialog
     */
    showSystemInfo() {
        const info = `
AICleaner v${this.systemStatus.version || '2.0'}
Total Zones: ${this.systemStatus.totalZones || 0}
Active Tasks: ${this.systemStatus.totalActiveTasks || 0}
Completed Tasks: ${this.systemStatus.totalCompletedTasks || 0}
Completion Rate: ${Math.round((this.systemStatus.globalCompletionRate || 0) * 100)}%
Last Analysis: ${this.systemStatus.lastGlobalAnalysis ?
    new Date(this.systemStatus.lastGlobalAnalysis).toLocaleString() : 'Never'}
        `.trim();

        alert(info); // Simple implementation - could be enhanced with a modal
    }

    /**
     * Handle task actions (complete, dismiss)
     */
    handleTaskAction(action, taskId, zoneName) {
        if (!this._hass || !this._hass.callService) return;

        switch (action) {
            case 'complete-task':
                this._hass.callService('aicleaner', 'complete_task', {
                    zone: zoneName,
                    task_id: taskId
                });
                this.showToast(`Task marked as completed`);
                break;
            case 'dismiss-task':
                this._hass.callService('aicleaner', 'dismiss_task', {
                    zone: zoneName,
                    task_id: taskId
                });
                this.showToast(`Task dismissed`);
                break;
        }
    }

    /**
     * Handle control actions (camera, settings, etc.)
     */
    handleControlAction(action, zoneName) {
        switch (action) {
            case 'analyze':
                this.triggerAnalysis(zoneName);
                break;
            case 'view-camera':
                this.showCameraSnapshot(zoneName);
                break;
            case 'zone-settings':
                this.showZoneSettings(zoneName);
                break;
        }
    }

    /**
     * Show camera snapshot (placeholder)
     */
    showCameraSnapshot(zoneName) {
        const zone = this.zones.find(z => z.name === zoneName);
        if (zone && zone.camera) {
            // In a real implementation, this would show a modal with the camera feed
            this.showToast(`Camera view for ${zone.displayName} - Feature coming soon!`);
        } else {
            this.showToast(`No camera configured for ${zoneName}`);
        }
    }

    /**
     * Show zone settings (placeholder)
     */
    showZoneSettings(zoneName) {
        this.showToast(`Zone settings for ${zoneName} - Feature coming soon!`);
    }

    /**
     * Select notification personality
     */
    selectPersonality(personality) {
        if (this._hass && this._hass.callService) {
            this._hass.callService('aicleaner', 'set_notification_personality', {
                personality: personality
            });
            this.showToast(`Notification personality changed to ${personality}`);

            // Update UI
            this.shadowRoot.querySelectorAll('.personality-card').forEach(card => {
                card.classList.remove('selected');
            });
            this.shadowRoot.querySelector(`[data-personality="${personality}"]`)?.classList.add('selected');
        }
    }

    /**
     * Add ignore rule
     */
    addIgnoreRule(rule) {
        if (this._hass && this._hass.callService) {
            this._hass.callService('aicleaner', 'add_ignore_rule', {
                rule: rule
            });
            this.showToast(`Added ignore rule: ${rule}`);

            // Re-render the config section
            setTimeout(() => this.render(), 500);
        }
    }

    /**
     * Remove ignore rule
     */
    removeIgnoreRule(ruleIndex) {
        const rules = this.getIgnoreRules();
        const rule = rules[ruleIndex];

        if (this._hass && this._hass.callService && rule) {
            this._hass.callService('aicleaner', 'remove_ignore_rule', {
                rule: rule
            });
            this.showToast(`Removed ignore rule: ${rule}`);

            // Re-render the config section
            setTimeout(() => this.render(), 500);
        }
    }

    /**
     * Get appropriate icon for zone
     */
    getZoneIcon(zoneName) {
        const zoneIcons = {
            'kitchen': '🍳',
            'living_room': '🛋️',
            'bedroom': '🛏️',
            'bathroom': '🚿',
            'office': '💼',
            'garage': '🚗',
            'laundry': '🧺',
            'dining_room': '🍽️',
            'basement': '🏠',
            'attic': '📦'
        };

        const normalizedName = zoneName.toLowerCase().replace(/\s+/g, '_');
        return zoneIcons[normalizedName] || '🏠';
    }

    /**
     * Format time relative to now
     */
    formatRelativeTime(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString();
    }

    /**
     * Show toast notification
     */
    showToast(message) {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--primary-color);
            color: var(--text-primary-color);
            padding: 12px 24px;
            border-radius: 24px;
            z-index: 1000;
            font-size: 0.9em;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;

        document.body.appendChild(toast);
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 3000);
    }

    /**
     * Return card size for Lovelace layout
     */
    getCardSize() {
        return 3;
    }

    /**
     * Return configuration schema for card editor
     */
    static getConfigElement() {
        return document.createElement('aicleaner-card-editor');
    }

    /**
     * Return stub configuration for card picker
     */
    static getStubConfig() {
        return {
            type: 'custom:aicleaner-card',
            title: 'AICleaner'
        };
    }
}

// Register the custom card
customElements.define('aicleaner-card', AICleanerCard);

// Register with card picker
window.customCards = window.customCards || [];
window.customCards.push({
    type: 'aicleaner-card',
    name: 'AICleaner Card',
    description: 'A comprehensive card for managing AICleaner zones and tasks',
    preview: true
});

// Register the custom element
customElements.define('aicleaner-card', AICleanerCard);

console.info(
    '%c🏠 AICleaner Card %cv2.0',
    'color: #4caf50; font-weight: bold;',
    'color: #888; font-weight: normal;'
);
