/**
 * Roo Performance Component
 * Charts and analytics dashboard for zone performance metrics
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('roo-performance')
export class RooPerformance extends LitElement {
  @property({ type: Object }) metrics = {};
  @property({ type: Object }) selectedZone = null;
  @property({ type: Boolean }) detailed = false;
  @state() timeRange = '30';
  @state() chartType = 'line';

  static get styles() {
    return css`
      :host {
        display: block;
        margin-bottom: 24px;
      }

      .performance-container {
        background: var(--card-background-color);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid var(--divider-color);
      }

      .performance-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
      }

      .performance-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin: 0;
      }

      .performance-controls {
        display: flex;
        gap: 12px;
        align-items: center;
      }

      .time-range-selector {
        background: var(--secondary-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 14px;
        color: var(--primary-text-color);
        cursor: pointer;
      }

      .chart-type-toggle {
        display: flex;
        background: var(--secondary-background-color);
        border-radius: 6px;
        padding: 2px;
      }

      .chart-type-btn {
        padding: 6px 12px;
        border: none;
        background: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        color: var(--secondary-text-color);
        transition: all 0.2s ease;
      }

      .chart-type-btn.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }

      .performance-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
      }

      .metric-card {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
      }

      .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--primary-color);
      }

      .metric-card.positive::before {
        background: var(--success-color);
      }

      .metric-card.negative::before {
        background: var(--error-color);
      }

      .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: var(--primary-text-color);
        margin-bottom: 4px;
      }

      .metric-label {
        font-size: 12px;
        color: var(--secondary-text-color);
        margin-bottom: 8px;
      }

      .metric-change {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        font-size: 12px;
        font-weight: 500;
      }

      .metric-change.positive {
        color: var(--success-color);
      }

      .metric-change.negative {
        color: var(--error-color);
      }

      .metric-change.neutral {
        color: var(--secondary-text-color);
      }

      .chart-container {
        background: var(--card-background-color);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 20px;
        min-height: 300px;
        position: relative;
      }

      .chart-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 300px;
        color: var(--secondary-text-color);
        text-align: center;
      }

      .chart-placeholder-icon {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
      }

      .chart-placeholder-text {
        font-size: 16px;
        margin-bottom: 8px;
      }

      .chart-placeholder-subtext {
        font-size: 14px;
        opacity: 0.7;
      }

      .simple-chart {
        width: 100%;
        height: 300px;
        position: relative;
        overflow: hidden;
      }

      .chart-bars {
        display: flex;
        align-items: end;
        height: 250px;
        gap: 4px;
        padding: 20px 0;
      }

      .chart-bar {
        flex: 1;
        background: var(--primary-color);
        border-radius: 2px 2px 0 0;
        min-height: 4px;
        position: relative;
        transition: all 0.3s ease;
        cursor: pointer;
      }

      .chart-bar:hover {
        background: var(--primary-color-dark);
        transform: scaleY(1.05);
      }

      .chart-bar-value {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        font-size: 10px;
        color: var(--secondary-text-color);
        margin-bottom: 4px;
        opacity: 0;
        transition: opacity 0.2s ease;
      }

      .chart-bar:hover .chart-bar-value {
        opacity: 1;
      }

      .chart-labels {
        display: flex;
        justify-content: space-between;
        padding: 0 2px;
        font-size: 10px;
        color: var(--secondary-text-color);
      }

      .performance-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        justify-content: center;
        margin-top: 16px;
      }

      .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 2px;
      }

      .legend-color.tasks-created {
        background: var(--primary-color);
      }

      .legend-color.tasks-completed {
        background: var(--success-color);
      }

      .legend-color.cleanliness-score {
        background: var(--warning-color);
      }

      .insights-section {
        margin-top: 20px;
      }

      .insights-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 12px;
      }

      .insights-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .insight-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        background: var(--secondary-background-color);
        border-radius: 6px;
        font-size: 14px;
        color: var(--primary-text-color);
      }

      .insight-icon {
        font-size: 16px;
      }

      .insight-icon.positive {
        color: var(--success-color);
      }

      .insight-icon.negative {
        color: var(--error-color);
      }

      .insight-icon.neutral {
        color: var(--warning-color);
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .performance-header {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }

        .performance-controls {
          justify-content: center;
        }

        .performance-summary {
          grid-template-columns: repeat(2, 1fr);
        }

        .chart-container {
          padding: 12px;
        }

        .simple-chart {
          height: 250px;
        }

        .chart-bars {
          height: 200px;
        }
      }

      /* Animation for metrics */
      .metric-card {
        animation: fadeInUp 0.3s ease-out;
      }

      @keyframes fadeInUp {
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

  get chartData() {
    // Generate sample data for demonstration
    const days = parseInt(this.timeRange);
    const data = [];
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      data.push({
        date: date.toISOString().split('T')[0],
        cleanliness_score: Math.floor(Math.random() * 30) + 70,
        tasks_created: Math.floor(Math.random() * 8) + 1,
        tasks_completed: Math.floor(Math.random() * 6) + 1
      });
    }
    
    return data;
  }

  get summaryMetrics() {
    const data = this.chartData;
    const latest = data[data.length - 1] || {};
    const previous = data[data.length - 2] || {};
    
    return {
      avgScore: {
        value: Math.round(data.reduce((sum, d) => sum + d.cleanliness_score, 0) / data.length),
        change: latest.cleanliness_score - previous.cleanliness_score,
        label: 'Avg Cleanliness'
      },
      totalTasks: {
        value: data.reduce((sum, d) => sum + d.tasks_created, 0),
        change: latest.tasks_created - previous.tasks_created,
        label: 'Total Tasks'
      },
      completionRate: {
        value: Math.round((data.reduce((sum, d) => sum + d.tasks_completed, 0) / 
                          data.reduce((sum, d) => sum + d.tasks_created, 0)) * 100),
        change: 5, // Sample change
        label: 'Completion Rate'
      },
      streak: {
        value: 7, // Sample streak
        change: 1,
        label: 'Clean Streak'
      }
    };
  }

  changeTimeRange(event) {
    this.timeRange = event.target.value;
  }

  changeChartType(type) {
    this.chartType = type;
  }

  getChangeIcon(change) {
    if (change > 0) return '📈';
    if (change < 0) return '📉';
    return '➡️';
  }

  getChangeClass(change) {
    if (change > 0) return 'positive';
    if (change < 0) return 'negative';
    return 'neutral';
  }

  formatChange(change, isPercentage = false) {
    const sign = change > 0 ? '+' : '';
    const suffix = isPercentage ? '%' : '';
    return `${sign}${change}${suffix}`;
  }

  generateInsights() {
    const metrics = this.summaryMetrics;
    const insights = [];

    if (metrics.avgScore.value >= 85) {
      insights.push({
        icon: '🌟',
        type: 'positive',
        text: 'Excellent cleanliness maintenance this period!'
      });
    }

    if (metrics.completionRate.value >= 80) {
      insights.push({
        icon: '🎯',
        type: 'positive',
        text: 'Great task completion rate - keep it up!'
      });
    }

    if (metrics.streak.value >= 7) {
      insights.push({
        icon: '🔥',
        type: 'positive',
        text: `Amazing ${metrics.streak.value}-day clean streak!`
      });
    }

    if (metrics.avgScore.change < -5) {
      insights.push({
        icon: '⚠️',
        type: 'negative',
        text: 'Cleanliness score has dropped recently'
      });
    }

    if (insights.length === 0) {
      insights.push({
        icon: '📊',
        type: 'neutral',
        text: 'Steady performance - room for improvement'
      });
    }

    return insights;
  }

  render() {
    return html`
      <div class="performance-container">
        ${this.renderHeader()}
        ${this.renderSummary()}
        ${this.renderChart()}
        ${this.detailed ? this.renderInsights() : ''}
      </div>
    `;
  }

  renderHeader() {
    return html`
      <div class="performance-header">
        <h3 class="performance-title">Performance</h3>
        
        <div class="performance-controls">
          <select 
            class="time-range-selector"
            .value=${this.timeRange}
            @change=${this.changeTimeRange}
          >
            <option value="7">7 days</option>
            <option value="30">30 days</option>
            <option value="90">90 days</option>
          </select>
          
          <div class="chart-type-toggle">
            <button 
              class="chart-type-btn ${this.chartType === 'line' ? 'active' : ''}"
              @click=${() => this.changeChartType('line')}
            >
              📈
            </button>
            <button 
              class="chart-type-btn ${this.chartType === 'bar' ? 'active' : ''}"
              @click=${() => this.changeChartType('bar')}
            >
              📊
            </button>
          </div>
        </div>
      </div>
    `;
  }

  renderSummary() {
    const metrics = this.summaryMetrics;
    
    return html`
      <div class="performance-summary">
        ${Object.entries(metrics).map(([key, metric]) => html`
          <div class="metric-card ${this.getChangeClass(metric.change)}">
            <div class="metric-value">${metric.value}${key === 'completionRate' ? '%' : ''}</div>
            <div class="metric-label">${metric.label}</div>
            <div class="metric-change ${this.getChangeClass(metric.change)}">
              <span>${this.getChangeIcon(metric.change)}</span>
              <span>${this.formatChange(metric.change, key === 'completionRate')} from last period</span>
            </div>
          </div>
        `)}
      </div>
    `;
  }

  renderChart() {
    const data = this.chartData;
    const maxValue = Math.max(...data.map(d => Math.max(d.cleanliness_score, d.tasks_created * 10, d.tasks_completed * 10)));
    
    return html`
      <div class="chart-container">
        ${data.length > 0 ? html`
          <div class="simple-chart">
            <div class="chart-bars">
              ${data.map(point => html`
                <div 
                  class="chart-bar"
                  style="height: ${(point.cleanliness_score / maxValue) * 100}%"
                  title="${point.date}: ${point.cleanliness_score}/100"
                >
                  <div class="chart-bar-value">${point.cleanliness_score}</div>
                </div>
              `)}
            </div>
            <div class="chart-labels">
              ${data.map((point, index) => {
                if (index % Math.ceil(data.length / 5) === 0) {
                  return html`<span>${new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>`;
                }
                return html`<span></span>`;
              })}
            </div>
          </div>
          
          <div class="performance-legend">
            <div class="legend-item">
              <div class="legend-color cleanliness-score"></div>
              <span>Cleanliness Score</span>
            </div>
            <div class="legend-item">
              <div class="legend-color tasks-created"></div>
              <span>Tasks Created (${data.reduce((sum, d) => sum + d.tasks_created, 0)} total)</span>
            </div>
            <div class="legend-item">
              <div class="legend-color tasks-completed"></div>
              <span>Tasks Completed (${data.reduce((sum, d) => sum + d.tasks_completed, 0)} total)</span>
            </div>
          </div>
        ` : html`
          <div class="chart-placeholder">
            <div class="chart-placeholder-icon">📊</div>
            <div class="chart-placeholder-text">No Data Available</div>
            <div class="chart-placeholder-subtext">
              Performance data will appear here after some analysis cycles
            </div>
          </div>
        `}
      </div>
    `;
  }

  renderInsights() {
    const insights = this.generateInsights();
    
    return html`
      <div class="insights-section">
        <h4 class="insights-title">Insights</h4>
        <div class="insights-list">
          ${insights.map(insight => html`
            <div class="insight-item">
              <span class="insight-icon ${insight.type}">${insight.icon}</span>
              <span>${insight.text}</span>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}
