/**
 * Roo Header Component
 * Navigation and zone selection header
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('roo-header')
export class RooHeader extends LitElement {
  @property({ type: Array }) zones = [];
  @property({ type: Object }) selectedZone = null;
  @property({ type: String }) viewMode = 'dashboard';
  @property({ type: Object }) lastUpdate = null;

  static get styles() {
    return css`
      :host {
        display: block;
        background: var(--primary-color);
        color: var(--text-primary-color);
        padding: 16px;
        border-radius: var(--ha-card-border-radius, 12px) var(--ha-card-border-radius, 12px) 0 0;
      }

      .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 16px;
      }

      .header-left {
        display: flex;
        align-items: center;
        gap: 16px;
        flex: 1;
      }

      .header-right {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .logo {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 20px;
        font-weight: bold;
      }

      .logo-icon {
        font-size: 24px;
      }

      .zone-selector {
        position: relative;
      }

      .zone-dropdown {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        color: var(--text-primary-color);
        padding: 8px 12px;
        font-size: 14px;
        cursor: pointer;
        min-width: 150px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
      }

      .zone-dropdown:hover {
        background: rgba(255, 255, 255, 0.15);
      }

      .zone-dropdown-icon {
        font-size: 16px;
        transition: transform 0.2s ease;
      }

      .zone-dropdown.open .zone-dropdown-icon {
        transform: rotate(180deg);
      }

      .zone-list {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        box-shadow: var(--ha-card-box-shadow);
        z-index: 1000;
        max-height: 300px;
        overflow-y: auto;
        margin-top: 4px;
      }

      .zone-item {
        padding: 12px 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: var(--primary-text-color);
        border-bottom: 1px solid var(--divider-color);
      }

      .zone-item:last-child {
        border-bottom: none;
      }

      .zone-item:hover {
        background: var(--secondary-background-color);
      }

      .zone-item.selected {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }

      .zone-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .zone-name {
        font-weight: 500;
      }

      .zone-status {
        font-size: 12px;
        opacity: 0.8;
      }

      .zone-badge {
        background: var(--error-color);
        color: white;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: bold;
        min-width: 16px;
        text-align: center;
      }

      .zone-badge.clean {
        background: var(--success-color);
      }

      .view-tabs {
        display: flex;
        gap: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 4px;
      }

      .view-tab {
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s ease;
        white-space: nowrap;
      }

      .view-tab:hover {
        background: rgba(255, 255, 255, 0.1);
      }

      .view-tab.active {
        background: rgba(255, 255, 255, 0.2);
        font-weight: 500;
      }

      .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        opacity: 0.8;
      }

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--success-color);
      }

      .status-dot.updating {
        background: var(--warning-color);
        animation: pulse 1.5s infinite;
      }

      .status-dot.error {
        background: var(--error-color);
      }

      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }

      .last-update {
        font-size: 11px;
        opacity: 0.7;
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .header-container {
          flex-direction: column;
          gap: 12px;
        }

        .header-left {
          width: 100%;
          justify-content: space-between;
        }

        .header-right {
          width: 100%;
          justify-content: center;
        }

        .view-tabs {
          width: 100%;
          justify-content: center;
        }

        .view-tab {
          flex: 1;
          text-align: center;
        }

        .logo {
          font-size: 18px;
        }

        .zone-dropdown {
          min-width: 120px;
        }
      }

      /* Hidden class for dropdown */
      .hidden {
        display: none;
      }
    `;
  }

  constructor() {
    super();
    this.dropdownOpen = false;
  }

  connectedCallback() {
    super.connectedCallback();
    document.addEventListener('click', this.handleDocumentClick.bind(this));
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener('click', this.handleDocumentClick.bind(this));
  }

  handleDocumentClick(event) {
    if (!this.contains(event.target)) {
      this.dropdownOpen = false;
      this.requestUpdate();
    }
  }

  toggleDropdown() {
    this.dropdownOpen = !this.dropdownOpen;
    this.requestUpdate();
  }

  selectZone(zone) {
    this.dropdownOpen = false;
    this.dispatchEvent(new CustomEvent('zone-selected', {
      detail: zone,
      bubbles: true,
      composed: true
    }));
  }

  selectViewMode(mode) {
    this.dispatchEvent(new CustomEvent('view-mode-changed', {
      detail: mode,
      bubbles: true,
      composed: true
    }));
  }

  getZoneStatusText(zone) {
    const pendingTasks = zone.pending_tasks || 0;
    const score = zone.cleanliness_score || 0;
    
    if (pendingTasks === 0) {
      return `Clean (${score}/100)`;
    } else {
      return `${pendingTasks} task${pendingTasks === 1 ? '' : 's'} • ${score}/100`;
    }
  }

  getZoneBadgeCount(zone) {
    return zone.pending_tasks || 0;
  }

  getLastUpdateText() {
    if (!this.lastUpdate) return '';
    
    const now = new Date();
    const diff = now - this.lastUpdate;
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes === 1) return '1 min ago';
    if (minutes < 60) return `${minutes} mins ago`;
    
    const hours = Math.floor(minutes / 60);
    if (hours === 1) return '1 hour ago';
    if (hours < 24) return `${hours} hours ago`;
    
    return this.lastUpdate.toLocaleDateString();
  }

  render() {
    return html`
      <div class="header-container">
        <div class="header-left">
          <div class="logo">
            <span class="logo-icon">🤖</span>
            <span>Roo Assistant</span>
          </div>

          ${this.zones.length > 0 ? html`
            <div class="zone-selector">
              <div 
                class="zone-dropdown ${this.dropdownOpen ? 'open' : ''}"
                @click=${this.toggleDropdown}
              >
                <span>${this.selectedZone?.display_name || 'Select Zone'}</span>
                <span class="zone-dropdown-icon">▼</span>
              </div>
              
              <div class="zone-list ${this.dropdownOpen ? '' : 'hidden'}">
                ${this.zones.map(zone => html`
                  <div 
                    class="zone-item ${zone.id === this.selectedZone?.id ? 'selected' : ''}"
                    @click=${() => this.selectZone(zone)}
                  >
                    <div class="zone-info">
                      <div class="zone-name">${zone.display_name}</div>
                      <div class="zone-status">${this.getZoneStatusText(zone)}</div>
                    </div>
                    ${this.getZoneBadgeCount(zone) > 0 ? html`
                      <div class="zone-badge">
                        ${this.getZoneBadgeCount(zone)}
                      </div>
                    ` : html`
                      <div class="zone-badge clean">✓</div>
                    `}
                  </div>
                `)}
              </div>
            </div>
          ` : ''}
        </div>

        <div class="header-right">
          <div class="view-tabs">
            <div 
              class="view-tab ${this.viewMode === 'dashboard' ? 'active' : ''}"
              @click=${() => this.selectViewMode('dashboard')}
            >
              Dashboard
            </div>
            <div 
              class="view-tab ${this.viewMode === 'zone' ? 'active' : ''}"
              @click=${() => this.selectViewMode('zone')}
            >
              Zone
            </div>
            <div 
              class="view-tab ${this.viewMode === 'config' ? 'active' : ''}"
              @click=${() => this.selectViewMode('config')}
            >
              Config
            </div>
          </div>

          <div class="status-indicator">
            <div class="status-dot"></div>
            <div class="last-update">${this.getLastUpdateText()}</div>
          </div>
        </div>
      </div>
    `;
  }
}
