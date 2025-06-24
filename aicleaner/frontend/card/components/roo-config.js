/**
 * Roo Configuration Component
 * Settings and configuration management interface
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('roo-config')
export class RooConfig extends LitElement {
  @property({ type: Array }) zones = [];
  @property({ type: Object }) config = {};
  @property({ type: Object }) apiService = null;
  @state() activeTab = 'zones';
  @state() editingZone = null;
  @state() showAddZone = false;
  @state() ignoreRules = [];
  @state() notificationSettings = {};

  static get styles() {
    return css`
      :host {
        display: block;
      }

      .config-container {
        background: var(--card-background-color);
        border-radius: 12px;
        border: 1px solid var(--divider-color);
        overflow: hidden;
      }

      .config-tabs {
        display: flex;
        background: var(--secondary-background-color);
        border-bottom: 1px solid var(--divider-color);
      }

      .config-tab {
        flex: 1;
        padding: 16px 20px;
        border: none;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
        border-bottom: 2px solid transparent;
      }

      .config-tab:hover {
        background: var(--divider-color);
        color: var(--primary-text-color);
      }

      .config-tab.active {
        color: var(--primary-color);
        border-bottom-color: var(--primary-color);
        background: var(--card-background-color);
      }

      .config-content {
        padding: 20px;
      }

      .section-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .add-button {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s ease;
      }

      .add-button:hover {
        background: var(--primary-color-dark);
      }

      .zones-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .zone-config-item {
        background: var(--secondary-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 16px;
        transition: all 0.2s ease;
      }

      .zone-config-item:hover {
        border-color: var(--primary-color);
      }

      .zone-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }

      .zone-info {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .zone-icon {
        font-size: 24px;
        width: 40px;
        height: 40px;
        border-radius: 8px;
        background: var(--card-background-color);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .zone-details {
        flex: 1;
      }

      .zone-name {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 4px;
      }

      .zone-status {
        font-size: 12px;
        color: var(--secondary-text-color);
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--success-color);
      }

      .status-dot.disabled {
        background: var(--disabled-text-color);
      }

      .zone-actions {
        display: flex;
        gap: 8px;
      }

      .action-btn {
        background: none;
        border: 1px solid var(--divider-color);
        border-radius: 4px;
        padding: 6px 10px;
        color: var(--secondary-text-color);
        cursor: pointer;
        font-size: 12px;
        transition: all 0.2s ease;
      }

      .action-btn:hover {
        background: var(--divider-color);
        color: var(--primary-text-color);
      }

      .action-btn.primary {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }

      .action-btn.danger {
        color: var(--error-color);
        border-color: var(--error-color);
      }

      .action-btn.danger:hover {
        background: var(--error-color);
        color: white;
      }

      .zone-settings {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--divider-color);
      }

      .setting-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .setting-label {
        font-size: 12px;
        color: var(--secondary-text-color);
        font-weight: 500;
      }

      .setting-value {
        font-size: 14px;
        color: var(--primary-text-color);
      }

      .form-container {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
      }

      .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
      }

      .form-group {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .form-label {
        font-size: 14px;
        font-weight: 500;
        color: var(--primary-text-color);
      }

      .form-input {
        padding: 10px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 14px;
      }

      .form-input:focus {
        outline: none;
        border-color: var(--primary-color);
      }

      .form-select {
        padding: 10px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        background: var(--card-background-color);
        color: var(--primary-text-color);
        font-size: 14px;
        cursor: pointer;
      }

      .form-checkbox {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
      }

      .checkbox-input {
        width: 16px;
        height: 16px;
        cursor: pointer;
      }

      .form-actions {
        display: flex;
        gap: 12px;
        justify-content: flex-end;
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid var(--divider-color);
      }

      .btn {
        padding: 10px 20px;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .btn-primary {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }

      .btn-primary:hover {
        background: var(--primary-color-dark);
      }

      .btn-secondary {
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
        border: 1px solid var(--divider-color);
      }

      .btn-secondary:hover {
        background: var(--divider-color);
      }

      .ignore-rules-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .ignore-rule-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        background: var(--secondary-background-color);
        border-radius: 6px;
        border: 1px solid var(--divider-color);
      }

      .rule-info {
        flex: 1;
      }

      .rule-type {
        font-size: 12px;
        color: var(--primary-color);
        font-weight: 500;
        text-transform: uppercase;
      }

      .rule-value {
        font-size: 14px;
        color: var(--primary-text-color);
        margin: 2px 0;
      }

      .rule-description {
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .notification-settings {
        display: flex;
        flex-direction: column;
        gap: 20px;
      }

      .setting-section {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 16px;
      }

      .setting-section-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 12px;
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .config-tabs {
          flex-direction: column;
        }

        .zone-header {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }

        .zone-actions {
          justify-content: center;
        }

        .form-grid {
          grid-template-columns: 1fr;
        }

        .form-actions {
          flex-direction: column;
        }
      }
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadIgnoreRules();
    this.loadNotificationSettings();
  }

  async loadIgnoreRules() {
    if (!this.apiService) return;
    
    try {
      // Load ignore rules for all zones
      const allRules = [];
      for (const zone of this.zones) {
        const rules = await this.apiService.getIgnoreRules(zone.id);
        allRules.push(...rules.map(rule => ({ ...rule, zone_name: zone.display_name })));
      }
      this.ignoreRules = allRules;
    } catch (error) {
      console.error('Failed to load ignore rules:', error);
    }
  }

  async loadNotificationSettings() {
    if (!this.apiService) return;
    
    try {
      this.notificationSettings = await this.apiService.getNotificationSettings();
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    }
  }

  selectTab(tab) {
    this.activeTab = tab;
  }

  editZone(zone) {
    this.editingZone = { ...zone };
    this.showAddZone = false;
  }

  addZone() {
    this.editingZone = {
      name: '',
      display_name: '',
      camera_entity_id: '',
      todo_list_entity_id: '',
      sensor_entity_id: '',
      enabled: true,
      notification_enabled: true,
      personality_mode: 'concise',
      update_frequency: 60,
      cleanliness_threshold: 70,
      max_tasks_per_analysis: 10
    };
    this.showAddZone = true;
  }

  cancelEdit() {
    this.editingZone = null;
    this.showAddZone = false;
  }

  async saveZone() {
    if (!this.editingZone || !this.apiService) return;

    try {
      if (this.showAddZone) {
        await this.apiService.createZone(this.editingZone);
      } else {
        await this.apiService.updateZone(this.editingZone.id, this.editingZone);
      }
      
      this.dispatchEvent(new CustomEvent('zones-updated', {
        bubbles: true,
        composed: true
      }));
      
      this.cancelEdit();
    } catch (error) {
      console.error('Failed to save zone:', error);
    }
  }

  async deleteZone(zone) {
    if (!confirm(`Are you sure you want to delete ${zone.display_name}?`)) return;
    
    try {
      await this.apiService.deleteZone(zone.id);
      this.dispatchEvent(new CustomEvent('zones-updated', {
        bubbles: true,
        composed: true
      }));
    } catch (error) {
      console.error('Failed to delete zone:', error);
    }
  }

  updateEditingZone(field, value) {
    this.editingZone = { ...this.editingZone, [field]: value };
  }

  render() {
    return html`
      <div class="config-container">
        ${this.renderTabs()}
        ${this.renderContent()}
      </div>
    `;
  }

  renderTabs() {
    const tabs = [
      { id: 'zones', label: '🏠 Zones', icon: '🏠' },
      { id: 'rules', label: '🚫 Ignore Rules', icon: '🚫' },
      { id: 'notifications', label: '🔔 Notifications', icon: '🔔' },
      { id: 'system', label: '⚙️ System', icon: '⚙️' }
    ];

    return html`
      <div class="config-tabs">
        ${tabs.map(tab => html`
          <button 
            class="config-tab ${this.activeTab === tab.id ? 'active' : ''}"
            @click=${() => this.selectTab(tab.id)}
          >
            ${tab.label}
          </button>
        `)}
      </div>
    `;
  }

  renderContent() {
    return html`
      <div class="config-content">
        ${this.activeTab === 'zones' ? this.renderZonesConfig() : ''}
        ${this.activeTab === 'rules' ? this.renderIgnoreRules() : ''}
        ${this.activeTab === 'notifications' ? this.renderNotificationSettings() : ''}
        ${this.activeTab === 'system' ? this.renderSystemSettings() : ''}
      </div>
    `;
  }

  renderZonesConfig() {
    return html`
      <div class="section-title">
        Zone Configuration
        <button class="add-button" @click=${this.addZone}>
          ➕ Add Zone
        </button>
      </div>

      ${this.editingZone ? this.renderZoneForm() : ''}

      <div class="zones-list">
        ${this.zones.map(zone => this.renderZoneItem(zone))}
      </div>
    `;
  }

  renderZoneItem(zone) {
    return html`
      <div class="zone-config-item">
        <div class="zone-header">
          <div class="zone-info">
            <div class="zone-icon">🏠</div>
            <div class="zone-details">
              <div class="zone-name">${zone.display_name}</div>
              <div class="zone-status">
                <div class="status-dot ${zone.enabled ? '' : 'disabled'}"></div>
                <span>${zone.enabled ? 'Active' : 'Disabled'}</span>
                <span>•</span>
                <span>${zone.personality_mode}</span>
              </div>
            </div>
          </div>
          
          <div class="zone-actions">
            <button class="action-btn primary" @click=${() => this.editZone(zone)}>
              ✏️ Edit
            </button>
            <button class="action-btn danger" @click=${() => this.deleteZone(zone)}>
              🗑️ Delete
            </button>
          </div>
        </div>

        <div class="zone-settings">
          <div class="setting-item">
            <div class="setting-label">Camera Entity</div>
            <div class="setting-value">${zone.camera_entity_id}</div>
          </div>
          <div class="setting-item">
            <div class="setting-label">Update Frequency</div>
            <div class="setting-value">${zone.update_frequency} minutes</div>
          </div>
          <div class="setting-item">
            <div class="setting-label">Cleanliness Threshold</div>
            <div class="setting-value">${zone.cleanliness_threshold}/100</div>
          </div>
          <div class="setting-item">
            <div class="setting-label">Max Tasks</div>
            <div class="setting-value">${zone.max_tasks_per_analysis}</div>
          </div>
        </div>
      </div>
    `;
  }

  renderZoneForm() {
    return html`
      <div class="form-container">
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">Zone Name</label>
            <input 
              class="form-input"
              type="text"
              .value=${this.editingZone.name}
              @input=${(e) => this.updateEditingZone('name', e.target.value)}
              placeholder="e.g., living_room"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Display Name</label>
            <input 
              class="form-input"
              type="text"
              .value=${this.editingZone.display_name}
              @input=${(e) => this.updateEditingZone('display_name', e.target.value)}
              placeholder="e.g., Living Room"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Camera Entity ID</label>
            <input 
              class="form-input"
              type="text"
              .value=${this.editingZone.camera_entity_id}
              @input=${(e) => this.updateEditingZone('camera_entity_id', e.target.value)}
              placeholder="camera.living_room"
            />
          </div>

          <div class="form-group">
            <label class="form-label">Personality Mode</label>
            <select 
              class="form-select"
              .value=${this.editingZone.personality_mode}
              @change=${(e) => this.updateEditingZone('personality_mode', e.target.value)}
            >
              <option value="concise">Concise</option>
              <option value="snarky">Snarky</option>
              <option value="encouraging">Encouraging</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">Update Frequency (minutes)</label>
            <input 
              class="form-input"
              type="number"
              min="5"
              max="1440"
              .value=${this.editingZone.update_frequency}
              @input=${(e) => this.updateEditingZone('update_frequency', parseInt(e.target.value))}
            />
          </div>

          <div class="form-group">
            <label class="form-label">Cleanliness Threshold</label>
            <input 
              class="form-input"
              type="number"
              min="0"
              max="100"
              .value=${this.editingZone.cleanliness_threshold}
              @input=${(e) => this.updateEditingZone('cleanliness_threshold', parseInt(e.target.value))}
            />
          </div>
        </div>

        <div class="form-checkbox">
          <input 
            class="checkbox-input"
            type="checkbox"
            .checked=${this.editingZone.enabled}
            @change=${(e) => this.updateEditingZone('enabled', e.target.checked)}
          />
          <label>Zone Enabled</label>
        </div>

        <div class="form-checkbox">
          <input 
            class="checkbox-input"
            type="checkbox"
            .checked=${this.editingZone.notification_enabled}
            @change=${(e) => this.updateEditingZone('notification_enabled', e.target.checked)}
          />
          <label>Notifications Enabled</label>
        </div>

        <div class="form-actions">
          <button class="btn btn-secondary" @click=${this.cancelEdit}>
            Cancel
          </button>
          <button class="btn btn-primary" @click=${this.saveZone}>
            ${this.showAddZone ? 'Create Zone' : 'Save Changes'}
          </button>
        </div>
      </div>
    `;
  }

  renderIgnoreRules() {
    return html`
      <div class="section-title">
        Ignore Rules
        <button class="add-button">
          ➕ Add Rule
        </button>
      </div>

      <div class="ignore-rules-list">
        ${this.ignoreRules.map(rule => html`
          <div class="ignore-rule-item">
            <div class="rule-info">
              <div class="rule-type">${rule.rule_type}</div>
              <div class="rule-value">${rule.rule_value}</div>
              <div class="rule-description">${rule.rule_description || 'No description'}</div>
            </div>
            <div class="zone-actions">
              <button class="action-btn">✏️ Edit</button>
              <button class="action-btn danger">🗑️ Delete</button>
            </div>
          </div>
        `)}
      </div>
    `;
  }

  renderNotificationSettings() {
    return html`
      <div class="section-title">Notification Settings</div>
      
      <div class="notification-settings">
        <div class="setting-section">
          <div class="setting-section-title">General Settings</div>
          <p>Notification configuration will be implemented here.</p>
        </div>
      </div>
    `;
  }

  renderSystemSettings() {
    return html`
      <div class="section-title">System Settings</div>
      <p>System configuration options will be implemented here.</p>
    `;
  }
}
