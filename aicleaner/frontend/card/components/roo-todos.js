/**
 * Roo Todos Component
 * Task list with completion tracking and progress visualization
 */

import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('roo-todos')
export class RooTodos extends LitElement {
  @property({ type: Array }) tasks = [];
  @property({ type: Object }) selectedZone = null;
  @property({ type: Boolean }) detailed = false;

  static get styles() {
    return css`
      :host {
        display: block;
        margin-bottom: 24px;
      }

      .todos-container {
        background: var(--card-background-color);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid var(--divider-color);
      }

      .todos-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
      }

      .todos-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin: 0;
      }

      .completion-indicator {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .circular-progress {
        position: relative;
        width: 60px;
        height: 60px;
      }

      .progress-ring {
        transform: rotate(-90deg);
      }

      .progress-ring-circle {
        fill: transparent;
        stroke: var(--divider-color);
        stroke-width: 4;
      }

      .progress-ring-progress {
        fill: transparent;
        stroke: var(--primary-color);
        stroke-width: 4;
        stroke-linecap: round;
        transition: stroke-dasharray 0.3s ease;
      }

      .progress-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 14px;
        font-weight: bold;
        color: var(--primary-color);
      }

      .completion-stats {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .completion-rate {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .completion-subtitle {
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .todos-summary {
        margin-bottom: 20px;
        padding: 12px 16px;
        background: var(--secondary-background-color);
        border-radius: 8px;
        font-size: 14px;
        color: var(--secondary-text-color);
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .summary-text {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .summary-icon {
        font-size: 16px;
      }

      .bulk-actions {
        display: flex;
        gap: 8px;
      }

      .bulk-action-btn {
        background: none;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 12px;
        cursor: pointer;
        color: var(--secondary-text-color);
        transition: all 0.2s ease;
      }

      .bulk-action-btn:hover {
        background: var(--secondary-background-color);
        border-color: var(--primary-color);
        color: var(--primary-color);
      }

      .todos-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .todo-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px;
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        transition: all 0.2s ease;
        position: relative;
      }

      .todo-item:hover {
        border-color: var(--primary-color);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      }

      .todo-item.completed {
        opacity: 0.6;
        background: var(--secondary-background-color);
      }

      .todo-item.completed .todo-description {
        text-decoration: line-through;
      }

      .todo-checkbox {
        width: 20px;
        height: 20px;
        border: 2px solid var(--divider-color);
        border-radius: 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        flex-shrink: 0;
        margin-top: 2px;
      }

      .todo-checkbox:hover {
        border-color: var(--primary-color);
      }

      .todo-checkbox.checked {
        background: var(--primary-color);
        border-color: var(--primary-color);
        color: white;
      }

      .todo-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .todo-description {
        font-size: 15px;
        color: var(--primary-text-color);
        line-height: 1.4;
        margin: 0;
      }

      .todo-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .todo-meta-item {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .todo-zone {
        background: var(--primary-color);
        color: var(--text-primary-color);
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
      }

      .todo-confidence {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .confidence-bar {
        width: 30px;
        height: 4px;
        background: var(--divider-color);
        border-radius: 2px;
        overflow: hidden;
      }

      .confidence-fill {
        height: 100%;
        background: var(--success-color);
        transition: width 0.3s ease;
      }

      .confidence-fill.medium {
        background: var(--warning-color);
      }

      .confidence-fill.low {
        background: var(--error-color);
      }

      .todo-priority {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .priority-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
      }

      .priority-indicator.high {
        background: var(--error-color);
      }

      .priority-indicator.medium {
        background: var(--warning-color);
      }

      .priority-indicator.low {
        background: var(--success-color);
      }

      .todo-actions {
        display: flex;
        gap: 8px;
        opacity: 0;
        transition: opacity 0.2s ease;
      }

      .todo-item:hover .todo-actions {
        opacity: 1;
      }

      .todo-action-btn {
        width: 32px;
        height: 32px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        transition: all 0.2s ease;
      }

      .todo-action-btn.ignore {
        background: var(--secondary-background-color);
        color: var(--secondary-text-color);
      }

      .todo-action-btn.ignore:hover {
        background: var(--warning-color);
        color: white;
      }

      .todo-action-btn.delete {
        background: var(--secondary-background-color);
        color: var(--secondary-text-color);
      }

      .todo-action-btn.delete:hover {
        background: var(--error-color);
        color: white;
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
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .todos-header {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }

        .completion-indicator {
          justify-content: center;
        }

        .todo-meta {
          flex-direction: column;
          gap: 8px;
        }

        .todo-actions {
          opacity: 1;
        }
      }

      /* Animation for new tasks */
      .todo-item {
        animation: slideInLeft 0.3s ease-out;
      }

      @keyframes slideInLeft {
        from {
          opacity: 0;
          transform: translateX(-20px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }

      /* Completion animation */
      .todo-item.completing {
        animation: completeTask 0.5s ease-out;
      }

      @keyframes completeTask {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); background: var(--success-color); }
        100% { transform: scale(1); }
      }
    `;
  }

  get pendingTasks() {
    return this.tasks.filter(task => task.status === 'pending');
  }

  get completedTasks() {
    return this.tasks.filter(task => ['completed', 'auto_completed'].includes(task.status));
  }

  get completionRate() {
    if (this.tasks.length === 0) return 100;
    return Math.round((this.completedTasks.length / this.tasks.length) * 100);
  }

  getConfidenceClass(score) {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
  }

  getPriorityText(priority) {
    const priorities = { 1: 'Low', 2: 'Medium', 3: 'High' };
    return priorities[priority] || 'Low';
  }

  getPriorityClass(priority) {
    if (priority >= 3) return 'high';
    if (priority >= 2) return 'medium';
    return 'low';
  }

  formatTimeAgo(date) {
    if (!date) return '';
    
    const now = new Date();
    const taskDate = new Date(date);
    const diffMs = now - taskDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  }

  toggleTask(task) {
    const taskElement = this.shadowRoot.querySelector(`[data-task-id="${task.id}"]`);
    if (taskElement) {
      taskElement.classList.add('completing');
      setTimeout(() => {
        taskElement.classList.remove('completing');
      }, 500);
    }

    this.dispatchEvent(new CustomEvent('task-completed', {
      detail: task.id,
      bubbles: true,
      composed: true
    }));
  }

  ignoreTask(task) {
    this.dispatchEvent(new CustomEvent('task-ignored', {
      detail: task.id,
      bubbles: true,
      composed: true
    }));
  }

  deleteTask(task) {
    this.dispatchEvent(new CustomEvent('task-deleted', {
      detail: task.id,
      bubbles: true,
      composed: true
    }));
  }

  completeAllTasks() {
    this.pendingTasks.forEach(task => {
      this.toggleTask(task);
    });
  }

  ignoreAllTasks() {
    this.pendingTasks.forEach(task => {
      this.ignoreTask(task);
    });
  }

  render() {
    if (this.tasks.length === 0) {
      return this.renderEmptyState();
    }

    return html`
      <div class="todos-container">
        ${this.renderHeader()}
        ${this.renderSummary()}
        ${this.renderTaskList()}
      </div>
    `;
  }

  renderHeader() {
    return html`
      <div class="todos-header">
        <h3 class="todos-title">
          ${this.detailed ? `${this.selectedZone?.display_name || 'Zone'} Tasks` : 'Todos'}
        </h3>
        
        <div class="completion-indicator">
          <div class="circular-progress">
            <svg class="progress-ring" width="60" height="60">
              <circle
                class="progress-ring-circle"
                cx="30"
                cy="30"
                r="26"
                stroke-width="4"
              />
              <circle
                class="progress-ring-progress"
                cx="30"
                cy="30"
                r="26"
                stroke-width="4"
                stroke-dasharray="${163.36 * this.completionRate / 100} 163.36"
              />
            </svg>
            <div class="progress-text">${this.completionRate}%</div>
          </div>
          
          <div class="completion-stats">
            <div class="completion-rate">${this.completionRate}%</div>
            <div class="completion-subtitle">Complete</div>
          </div>
        </div>
      </div>
    `;
  }

  renderSummary() {
    const pendingCount = this.pendingTasks.length;
    
    return html`
      <div class="todos-summary">
        <div class="summary-text">
          <span class="summary-icon">📋</span>
          <span>
            ${pendingCount === 0 
              ? 'All tasks completed! Great job!' 
              : `${pendingCount} task${pendingCount === 1 ? '' : 's'} remaining today`
            }
          </span>
        </div>
        
        ${pendingCount > 0 ? html`
          <div class="bulk-actions">
            <button class="bulk-action-btn" @click=${this.completeAllTasks}>
              Complete All
            </button>
            <button class="bulk-action-btn" @click=${this.ignoreAllTasks}>
              Ignore All
            </button>
          </div>
        ` : ''}
      </div>
    `;
  }

  renderTaskList() {
    const tasksToShow = this.detailed ? this.tasks : this.pendingTasks.slice(0, 5);
    
    return html`
      <div class="todos-list">
        ${tasksToShow.map(task => this.renderTask(task))}
      </div>
    `;
  }

  renderTask(task) {
    const isCompleted = ['completed', 'auto_completed'].includes(task.status);
    
    return html`
      <div 
        class="todo-item ${isCompleted ? 'completed' : ''}"
        data-task-id="${task.id}"
      >
        <div 
          class="todo-checkbox ${isCompleted ? 'checked' : ''}"
          @click=${() => !isCompleted && this.toggleTask(task)}
        >
          ${isCompleted ? '✓' : ''}
        </div>
        
        <div class="todo-content">
          <div class="todo-description">${task.description}</div>
          
          <div class="todo-meta">
            ${!this.detailed && task.zone_name ? html`
              <div class="todo-meta-item">
                <span class="todo-zone">${task.zone_name}</span>
              </div>
            ` : ''}
            
            <div class="todo-meta-item todo-confidence">
              <span>Confidence:</span>
              <div class="confidence-bar">
                <div 
                  class="confidence-fill ${this.getConfidenceClass(task.confidence_score)}"
                  style="width: ${(task.confidence_score * 100)}%"
                ></div>
              </div>
              <span>${Math.round(task.confidence_score * 100)}%</span>
            </div>
            
            <div class="todo-meta-item todo-priority">
              <div class="priority-indicator ${this.getPriorityClass(task.priority)}"></div>
              <span>${this.getPriorityText(task.priority)} Priority</span>
            </div>
            
            ${task.detection_count > 1 ? html`
              <div class="todo-meta-item">
                <span>🔄 Detected ${task.detection_count} times</span>
              </div>
            ` : ''}
            
            <div class="todo-meta-item">
              <span>⏰ ${this.formatTimeAgo(task.created_at)}</span>
            </div>
          </div>
        </div>
        
        ${!isCompleted ? html`
          <div class="todo-actions">
            <button 
              class="todo-action-btn ignore"
              @click=${() => this.ignoreTask(task)}
              title="Ignore this task"
            >
              👁️‍🗨️
            </button>
            <button 
              class="todo-action-btn delete"
              @click=${() => this.deleteTask(task)}
              title="Delete this task"
            >
              🗑️
            </button>
          </div>
        ` : ''}
      </div>
    `;
  }

  renderEmptyState() {
    return html`
      <div class="todos-container">
        <div class="empty-state">
          <div class="empty-state-icon">✨</div>
          <div class="empty-state-title">All Clean!</div>
          <div class="empty-state-description">
            No tasks detected. Your ${this.selectedZone?.display_name || 'space'} is looking great!
          </div>
        </div>
      </div>
    `;
  }
}
