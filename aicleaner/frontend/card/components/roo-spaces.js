/**
 * Roo Spaces Component
 * Displays zone overview cards matching the mockup design
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('roo-spaces')
export class RooSpaces extends LitElement {
  @property({ type: Array }) zones = [];
  @property({ type: Object }) selectedZone = null;

  static get styles() {
    return css`
      :host {
        display: block;
        margin-bottom: 24px;
      }

      .spaces-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
      }

      .spaces-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin: 0;
      }

      .add-zone-button {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s ease;
      }

      .add-zone-button:hover {
        background: var(--primary-color-dark);
        transform: translateY(-1px);
      }

      .spaces-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
      }

      .space-card {
        background: var(--card-background-color);
        border: 2px solid var(--divider-color);
        border-radius: 12px;
        padding: 16px;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
      }

      .space-card:hover {
        border-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      }

      .space-card.selected {
        border-color: var(--primary-color);
        background: var(--primary-color);
        color: var(--text-primary-color);
      }

      .space-card.selected .space-name,
      .space-card.selected .space-status,
      .space-card.selected .space-score {
        color: var(--text-primary-color);
      }

      .space-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }

      .space-icon-name {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .space-icon {
        font-size: 24px;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--secondary-background-color);
      }

      .space-card.selected .space-icon {
        background: rgba(255, 255, 255, 0.2);
      }

      .space-name {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin: 0;
      }

      .space-badge {
        min-width: 24px;
        height: 24px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        color: white;
      }

      .space-badge.tasks {
        background: var(--error-color);
      }

      .space-badge.clean {
        background: var(--success-color);
      }

      .space-info {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .space-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        color: var(--secondary-text-color);
      }

      .status-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
      }

      .status-indicator.clean {
        background: var(--success-color);
      }

      .status-indicator.needs-attention {
        background: var(--warning-color);
      }

      .status-indicator.messy {
        background: var(--error-color);
      }

      .status-indicator.offline {
        background: var(--disabled-text-color);
      }

      .space-score {
        font-size: 14px;
        color: var(--secondary-text-color);
        font-weight: 500;
      }

      .space-card.selected .space-score {
        opacity: 0.9;
      }

      .space-progress {
        margin-top: 12px;
        height: 4px;
        background: var(--divider-color);
        border-radius: 2px;
        overflow: hidden;
      }

      .space-card.selected .space-progress {
        background: rgba(255, 255, 255, 0.3);
      }

      .space-progress-bar {
        height: 100%;
        border-radius: 2px;
        transition: width 0.3s ease;
      }

      .space-progress-bar.excellent {
        background: var(--success-color);
      }

      .space-progress-bar.good {
        background: var(--warning-color);
      }

      .space-progress-bar.poor {
        background: var(--error-color);
      }

      .space-card.selected .space-progress-bar {
        background: rgba(255, 255, 255, 0.8);
      }

      .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: var(--secondary-text-color);
      }

      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
      }

      .empty-state-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 8px;
        color: var(--primary-text-color);
      }

      .empty-state-description {
        font-size: 14px;
        line-height: 1.5;
        margin-bottom: 20px;
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .spaces-grid {
          grid-template-columns: 1fr;
        }

        .spaces-header {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }

        .add-zone-button {
          justify-content: center;
        }
      }

      /* Animation for new cards */
      .space-card {
        animation: slideInUp 0.3s ease-out;
      }

      @keyframes slideInUp {
        from {
          opacity: 0;
          transform: translateY(20px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
  }

  getZoneIcon(zoneName) {
    const iconMap = {
      'living_room': '🛋️',
      'kitchen': '🍳',
      'bedroom': '🛏️',
      'bathroom': '🚿',
      'office': '💻',
      'dining_room': '🍽️',
      'garage': '🚗',
      'laundry': '🧺',
      'basement': '🏠',
      'attic': '🏠'
    };

    const normalizedName = zoneName.toLowerCase().replace(/\s+/g, '_');
    return iconMap[normalizedName] || '🏠';
  }

  getStatusIndicatorClass(zone) {
    const score = zone.cleanliness_score || 0;
    const pendingTasks = zone.pending_tasks || 0;

    if (!zone.enabled) return 'offline';
    if (pendingTasks === 0 && score >= 80) return 'clean';
    if (score >= 70) return 'needs-attention';
    return 'messy';
  }

  getStatusText(zone) {
    const pendingTasks = zone.pending_tasks || 0;
    
    if (!zone.enabled) return 'Offline';
    if (pendingTasks === 0) return 'Clean';
    return `${pendingTasks} task${pendingTasks === 1 ? '' : 's'}`;
  }

  getProgressBarClass(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    return 'poor';
  }

  selectZone(zone) {
    this.dispatchEvent(new CustomEvent('zone-selected', {
      detail: zone,
      bubbles: true,
      composed: true
    }));
  }

  addZone() {
    this.dispatchEvent(new CustomEvent('add-zone', {
      bubbles: true,
      composed: true
    }));
  }

  render() {
    if (this.zones.length === 0) {
      return this.renderEmptyState();
    }

    return html`
      <div class="spaces-header">
        <h3 class="spaces-title">Spaces</h3>
        <button class="add-zone-button" @click=${this.addZone}>
          <span>➕</span>
          <span>Add Zone</span>
        </button>
      </div>

      <div class="spaces-grid">
        ${this.zones.map(zone => this.renderZoneCard(zone))}
      </div>
    `;
  }

  renderZoneCard(zone) {
    const isSelected = this.selectedZone?.id === zone.id;
    const score = zone.cleanliness_score || 0;
    const pendingTasks = zone.pending_tasks || 0;

    return html`
      <div 
        class="space-card ${isSelected ? 'selected' : ''}"
        @click=${() => this.selectZone(zone)}
      >
        <div class="space-header">
          <div class="space-icon-name">
            <div class="space-icon">
              ${this.getZoneIcon(zone.name)}
            </div>
            <h4 class="space-name">${zone.display_name}</h4>
          </div>
          
          <div class="space-badge ${pendingTasks > 0 ? 'tasks' : 'clean'}">
            ${pendingTasks > 0 ? pendingTasks : '✓'}
          </div>
        </div>

        <div class="space-info">
          <div class="space-status">
            <div class="status-indicator ${this.getStatusIndicatorClass(zone)}"></div>
            <span>${this.getStatusText(zone)}</span>
          </div>
          
          <div class="space-score">
            Score: ${score}/100
          </div>
        </div>

        <div class="space-progress">
          <div 
            class="space-progress-bar ${this.getProgressBarClass(score)}"
            style="width: ${score}%"
          ></div>
        </div>
      </div>
    `;
  }

  renderEmptyState() {
    return html`
      <div class="empty-state">
        <div class="empty-state-icon">🏠</div>
        <div class="empty-state-title">No Zones Configured</div>
        <div class="empty-state-description">
          Get started by adding your first zone to monitor.<br>
          Each zone can have its own camera, settings, and personality.
        </div>
        <button class="add-zone-button" @click=${this.addZone}>
          <span>➕</span>
          <span>Add Your First Zone</span>
        </button>
      </div>
    `;
  }
}
