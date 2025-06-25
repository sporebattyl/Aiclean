/**
 * Roo Notifications Component
 * Displays personality-based notifications and messages
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('roo-notifications')
export class RooNotifications extends LitElement {
  @property({ type: Array }) notifications = [];

  static get styles() {
    return css`
      :host {
        display: block;
        margin-bottom: 24px;
      }

      .notifications-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .notification-item {
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 12px;
        padding: 16px 20px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        animation: slideInDown 0.3s ease-out;
      }

      .notification-item:hover {
        border-color: var(--primary-color);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      }

      .notification-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
      }

      .notification-item.task-reminder::before {
        background: var(--warning-color);
      }

      .notification-item.completion-celebration::before {
        background: var(--success-color);
      }

      .notification-item.streak-milestone::before {
        background: var(--primary-color);
      }

      .notification-item.analysis-error::before {
        background: var(--error-color);
      }

      .notification-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 8px;
      }

      .notification-icon-title {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
      }

      .notification-icon {
        font-size: 24px;
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--secondary-background-color);
        flex-shrink: 0;
      }

      .notification-title-area {
        flex: 1;
      }

      .notification-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 4px;
      }

      .notification-subtitle {
        font-size: 12px;
        color: var(--secondary-text-color);
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .zone-badge {
        background: var(--primary-color);
        color: var(--text-primary-color);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 500;
      }

      .notification-time {
        font-size: 11px;
        color: var(--secondary-text-color);
        opacity: 0.7;
      }

      .notification-actions {
        display: flex;
        gap: 8px;
        opacity: 0;
        transition: opacity 0.2s ease;
      }

      .notification-item:hover .notification-actions {
        opacity: 1;
      }

      .action-btn {
        width: 28px;
        height: 28px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        transition: all 0.2s ease;
        background: var(--secondary-background-color);
        color: var(--secondary-text-color);
      }

      .action-btn:hover {
        background: var(--divider-color);
        color: var(--primary-text-color);
      }

      .action-btn.dismiss:hover {
        background: var(--error-color);
        color: white;
      }

      .notification-message {
        font-size: 14px;
        color: var(--primary-text-color);
        line-height: 1.5;
        margin-bottom: 12px;
      }

      .notification-message.snarky {
        font-style: italic;
      }

      .notification-message.encouraging {
        font-weight: 500;
      }

      .notification-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        font-size: 12px;
        color: var(--secondary-text-color);
        align-items: center;
      }

      .meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .personality-indicator {
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 500;
        text-transform: uppercase;
      }

      .personality-indicator.concise {
        background: var(--info-color);
        color: white;
      }

      .personality-indicator.snarky {
        background: var(--warning-color);
        color: white;
      }

      .personality-indicator.encouraging {
        background: var(--success-color);
        color: white;
      }

      .notification-actions-bar {
        display: flex;
        gap: 8px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--divider-color);
      }

      .notification-btn {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .notification-btn:hover {
        background: var(--primary-color-dark);
      }

      .notification-btn.secondary {
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
        border: 1px solid var(--divider-color);
      }

      .notification-btn.secondary:hover {
        background: var(--divider-color);
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
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
        color: var(--primary-text-color);
      }

      .empty-state-description {
        font-size: 14px;
        line-height: 1.5;
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .notification-header {
          flex-direction: column;
          gap: 12px;
        }

        .notification-actions {
          opacity: 1;
          justify-content: center;
        }

        .notification-meta {
          justify-content: center;
        }

        .notification-actions-bar {
          justify-content: center;
        }
      }

      /* Animations */
      @keyframes slideInDown {
        from {
          opacity: 0;
          transform: translateY(-20px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .notification-item.dismissing {
        animation: slideOutUp 0.3s ease-out forwards;
      }

      @keyframes slideOutUp {
        from {
          opacity: 1;
          transform: translateY(0);
          max-height: 200px;
        }
        to {
          opacity: 0;
          transform: translateY(-20px);
          max-height: 0;
          padding: 0;
          margin: 0;
        }
      }

      /* Notification type specific styling */
      .notification-item.completion-celebration {
        background: linear-gradient(135deg, var(--card-background-color) 0%, rgba(76, 175, 80, 0.05) 100%);
      }

      .notification-item.streak-milestone {
        background: linear-gradient(135deg, var(--card-background-color) 0%, rgba(33, 150, 243, 0.05) 100%);
      }

      .notification-item.analysis-error {
        background: linear-gradient(135deg, var(--card-background-color) 0%, rgba(244, 67, 54, 0.05) 100%);
      }
    `;
  }

  getNotificationIcon(type) {
    const icons = {
      'task_reminder': '📋',
      'completion_celebration': '🎉',
      'streak_milestone': '🔥',
      'analysis_error': '⚠️',
      'auto_completion': '✨'
    };
    return icons[type] || '📱';
  }

  getTimeAgo(timestamp) {
    if (!timestamp) return '';
    
    const now = new Date();
    const notificationTime = new Date(timestamp);
    const diffMs = now - notificationTime;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return notificationTime.toLocaleDateString();
  }

  dismissNotification(notification) {
    const element = this.shadowRoot.querySelector(`[data-notification-id="${notification.id}"]`);
    if (element) {
      element.classList.add('dismissing');
      setTimeout(() => {
        this.dispatchEvent(new CustomEvent('notification-dismissed', {
          detail: notification.id,
          bubbles: true,
          composed: true
        }));
      }, 300);
    }
  }

  handleNotificationAction(notification, action) {
    this.dispatchEvent(new CustomEvent('notification-action', {
      detail: { notification, action },
      bubbles: true,
      composed: true
    }));
  }

  render() {
    if (this.notifications.length === 0) {
      return this.renderEmptyState();
    }

    return html`
      <div class="notifications-container">
        ${this.notifications.map(notification => this.renderNotification(notification))}
      </div>
    `;
  }

  renderNotification(notification) {
    return html`
      <div 
        class="notification-item ${notification.type}"
        data-notification-id="${notification.id}"
      >
        <div class="notification-header">
          <div class="notification-icon-title">
            <div class="notification-icon">
              ${this.getNotificationIcon(notification.type)}
            </div>
            
            <div class="notification-title-area">
              <div class="notification-title">${notification.title}</div>
              <div class="notification-subtitle">
                ${notification.zone_name ? html`
                  <span class="zone-badge">${notification.zone_name}</span>
                ` : ''}
                <span class="personality-indicator ${notification.personality}">
                  ${notification.personality}
                </span>
                <span class="notification-time">
                  ${this.getTimeAgo(notification.timestamp)}
                </span>
              </div>
            </div>
          </div>
          
          <div class="notification-actions">
            <button 
              class="action-btn dismiss"
              @click=${() => this.dismissNotification(notification)}
              title="Dismiss notification"
            >
              ✕
            </button>
          </div>
        </div>

        <div class="notification-message ${notification.personality}">
          ${notification.message}
        </div>

        ${notification.metadata ? this.renderNotificationMeta(notification.metadata) : ''}
        
        ${notification.actions && notification.actions.length > 0 ? 
          this.renderNotificationActions(notification) : ''}
      </div>
    `;
  }

  renderNotificationMeta(metadata) {
    const metaItems = [];
    
    if (metadata.task_count) {
      metaItems.push(html`
        <div class="meta-item">
          <span>📋</span>
          <span>${metadata.task_count} tasks</span>
        </div>
      `);
    }
    
    if (metadata.cleanliness_score) {
      metaItems.push(html`
        <div class="meta-item">
          <span>📊</span>
          <span>Score: ${metadata.cleanliness_score}/100</span>
        </div>
      `);
    }
    
    if (metadata.streak_days) {
      metaItems.push(html`
        <div class="meta-item">
          <span>🔥</span>
          <span>${metadata.streak_days} day streak</span>
        </div>
      `);
    }

    if (metaItems.length === 0) return '';

    return html`
      <div class="notification-meta">
        ${metaItems}
      </div>
    `;
  }

  renderNotificationActions(notification) {
    return html`
      <div class="notification-actions-bar">
        ${notification.actions.map(action => html`
          <button 
            class="notification-btn ${action.style || ''}"
            @click=${() => this.handleNotificationAction(notification, action)}
          >
            ${action.title}
          </button>
        `)}
      </div>
    `;
  }

  renderEmptyState() {
    return html`
      <div class="empty-state">
        <div class="empty-state-icon">🔔</div>
        <div class="empty-state-title">No Recent Notifications</div>
        <div class="empty-state-description">
          You're all caught up! Notifications will appear here when there's something to report.
        </div>
      </div>
    `;
  }
}
