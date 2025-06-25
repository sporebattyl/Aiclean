/**
 * Roo Image Viewer Component
 * Visual analysis pane showing camera feed and AI analysis overlay
 */

import { LitElement, html, css } from 'lit';
import { customElement, property, state } from 'lit/decorators.js';

@customElement('roo-image-viewer')
export class RooImageViewer extends LitElement {
  @property({ type: Object }) zone = null;
  @property({ type: Object }) apiService = null;
  @state() imageUrl = null;
  @state() loading = false;
  @state() error = null;
  @state() analysisOverlay = false;
  @state() lastAnalysis = null;

  static get styles() {
    return css`
      :host {
        display: block;
        margin-bottom: 24px;
      }

      .image-viewer-container {
        background: var(--card-background-color);
        border-radius: 12px;
        border: 1px solid var(--divider-color);
        overflow: hidden;
      }

      .viewer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        background: var(--secondary-background-color);
        border-bottom: 1px solid var(--divider-color);
      }

      .viewer-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin: 0;
      }

      .viewer-controls {
        display: flex;
        gap: 8px;
        align-items: center;
      }

      .control-btn {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: all 0.2s ease;
      }

      .control-btn:hover {
        background: var(--primary-color-dark);
      }

      .control-btn:disabled {
        background: var(--disabled-text-color);
        cursor: not-allowed;
      }

      .control-btn.secondary {
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
        border: 1px solid var(--divider-color);
      }

      .control-btn.secondary:hover {
        background: var(--divider-color);
      }

      .overlay-toggle {
        background: none;
        border: 1px solid var(--divider-color);
        border-radius: 6px;
        padding: 6px 10px;
        color: var(--secondary-text-color);
        cursor: pointer;
        font-size: 12px;
        transition: all 0.2s ease;
      }

      .overlay-toggle.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }

      .image-container {
        position: relative;
        width: 100%;
        min-height: 300px;
        background: var(--secondary-background-color);
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .camera-image {
        width: 100%;
        height: auto;
        max-height: 500px;
        object-fit: contain;
        border-radius: 0;
      }

      .image-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
      }

      .image-overlay.visible {
        opacity: 1;
      }

      .analysis-marker {
        position: absolute;
        width: 12px;
        height: 12px;
        background: var(--error-color);
        border: 2px solid white;
        border-radius: 50%;
        transform: translate(-50%, -50%);
        animation: pulse 2s infinite;
      }

      .analysis-marker.completed {
        background: var(--success-color);
        animation: none;
      }

      @keyframes pulse {
        0%, 100% { transform: translate(-50%, -50%) scale(1); }
        50% { transform: translate(-50%, -50%) scale(1.2); }
      }

      .marker-tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        white-space: nowrap;
        margin-bottom: 8px;
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: auto;
      }

      .analysis-marker:hover .marker-tooltip {
        opacity: 1;
      }

      .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 300px;
        color: var(--secondary-text-color);
      }

      .loading-spinner {
        width: 40px;
        height: 40px;
        border: 3px solid var(--divider-color);
        border-top: 3px solid var(--primary-color);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 16px;
      }

      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }

      .error-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 300px;
        color: var(--error-color);
        text-align: center;
        padding: 20px;
      }

      .error-icon {
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.5;
      }

      .no-image-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 300px;
        color: var(--secondary-text-color);
        text-align: center;
      }

      .no-image-icon {
        font-size: 64px;
        margin-bottom: 16px;
        opacity: 0.3;
      }

      .image-info {
        padding: 16px 20px;
        background: var(--secondary-background-color);
        border-top: 1px solid var(--divider-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .image-meta {
        display: flex;
        gap: 16px;
      }

      .image-actions {
        display: flex;
        gap: 8px;
      }

      .action-btn {
        background: none;
        border: 1px solid var(--divider-color);
        border-radius: 4px;
        padding: 4px 8px;
        color: var(--secondary-text-color);
        cursor: pointer;
        font-size: 11px;
        transition: all 0.2s ease;
      }

      .action-btn:hover {
        background: var(--divider-color);
        color: var(--primary-text-color);
      }

      .analysis-summary {
        padding: 16px 20px;
        background: var(--card-background-color);
        border-top: 1px solid var(--divider-color);
      }

      .summary-title {
        font-size: 14px;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 8px;
      }

      .summary-content {
        display: flex;
        gap: 20px;
        align-items: center;
      }

      .score-display {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .score-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
        color: white;
      }

      .score-circle.excellent {
        background: var(--success-color);
      }

      .score-circle.good {
        background: var(--warning-color);
      }

      .score-circle.poor {
        background: var(--error-color);
      }

      .tasks-summary {
        font-size: 13px;
        color: var(--secondary-text-color);
      }

      /* Mobile responsive */
      @media (max-width: 768px) {
        .viewer-header {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }

        .viewer-controls {
          justify-content: center;
        }

        .image-info {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }

        .summary-content {
          flex-direction: column;
          gap: 12px;
          align-items: stretch;
        }
      }
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    this.loadImage();
  }

  async loadImage() {
    if (!this.zone || !this.apiService) return;

    this.loading = true;
    this.error = null;

    try {
      // Get latest image for the zone
      const imageData = await this.apiService.getZoneImage(this.zone.id);
      this.imageUrl = imageData.url || this.generateCameraUrl();
      
      // Get latest analysis data
      const history = await this.apiService.getZoneHistory(this.zone.id, 1);
      this.lastAnalysis = history[0] || null;
      
    } catch (error) {
      console.error('Failed to load zone image:', error);
      this.error = 'Failed to load camera image';
      this.imageUrl = null;
    } finally {
      this.loading = false;
    }
  }

  generateCameraUrl() {
    // Generate Home Assistant camera proxy URL
    if (!this.zone?.camera_entity_id) return null;
    
    const baseUrl = window.location.origin;
    return `${baseUrl}/api/camera_proxy/${this.zone.camera_entity_id}?t=${Date.now()}`;
  }

  async refreshImage() {
    await this.loadImage();
  }

  async triggerAnalysis() {
    if (!this.zone || !this.apiService) return;

    try {
      this.loading = true;
      await this.apiService.triggerAnalysis(this.zone.id);
      
      // Refresh image and analysis after a short delay
      setTimeout(() => {
        this.loadImage();
      }, 2000);
      
    } catch (error) {
      console.error('Failed to trigger analysis:', error);
      this.error = 'Failed to trigger analysis';
    }
  }

  toggleOverlay() {
    this.analysisOverlay = !this.analysisOverlay;
  }

  downloadImage() {
    if (!this.imageUrl) return;
    
    const link = document.createElement('a');
    link.href = this.imageUrl;
    link.download = `${this.zone.name}_${new Date().toISOString().split('T')[0]}.jpg`;
    link.click();
  }

  getScoreClass(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    return 'poor';
  }

  getScoreText(score) {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    return 'Needs Work';
  }

  renderAnalysisMarkers() {
    if (!this.lastAnalysis || !this.analysisOverlay) return '';

    // Generate sample markers for demonstration
    const markers = [
      { x: 25, y: 30, task: 'Pick up clothes from floor', completed: false },
      { x: 60, y: 45, task: 'Make the bed', completed: true },
      { x: 80, y: 70, task: 'Organize desk items', completed: false }
    ];

    return html`
      <div class="image-overlay ${this.analysisOverlay ? 'visible' : ''}">
        ${markers.map(marker => html`
          <div 
            class="analysis-marker ${marker.completed ? 'completed' : ''}"
            style="left: ${marker.x}%; top: ${marker.y}%;"
          >
            <div class="marker-tooltip">${marker.task}</div>
          </div>
        `)}
      </div>
    `;
  }

  render() {
    return html`
      <div class="image-viewer-container">
        ${this.renderHeader()}
        ${this.renderImageArea()}
        ${this.renderImageInfo()}
        ${this.lastAnalysis ? this.renderAnalysisSummary() : ''}
      </div>
    `;
  }

  renderHeader() {
    return html`
      <div class="viewer-header">
        <h3 class="viewer-title">
          📷 ${this.zone?.display_name || 'Zone'} Camera
        </h3>
        
        <div class="viewer-controls">
          <button 
            class="control-btn"
            @click=${this.refreshImage}
            ?disabled=${this.loading}
          >
            🔄 Refresh
          </button>
          
          <button 
            class="control-btn"
            @click=${this.triggerAnalysis}
            ?disabled=${this.loading}
          >
            🤖 Analyze
          </button>
          
          <button 
            class="overlay-toggle ${this.analysisOverlay ? 'active' : ''}"
            @click=${this.toggleOverlay}
            ?disabled=${!this.lastAnalysis}
          >
            🎯 Overlay
          </button>
        </div>
      </div>
    `;
  }

  renderImageArea() {
    if (this.loading) {
      return html`
        <div class="image-container">
          <div class="loading-state">
            <div class="loading-spinner"></div>
            <div>Loading camera image...</div>
          </div>
        </div>
      `;
    }

    if (this.error) {
      return html`
        <div class="image-container">
          <div class="error-state">
            <div class="error-icon">📷</div>
            <div>${this.error}</div>
            <button class="control-btn" @click=${this.refreshImage}>
              Try Again
            </button>
          </div>
        </div>
      `;
    }

    if (!this.imageUrl) {
      return html`
        <div class="image-container">
          <div class="no-image-state">
            <div class="no-image-icon">📷</div>
            <div>No camera image available</div>
            <div style="font-size: 12px; margin-top: 8px;">
              Check camera configuration for ${this.zone?.display_name}
            </div>
          </div>
        </div>
      `;
    }

    return html`
      <div class="image-container">
        <img 
          class="camera-image"
          src="${this.imageUrl}"
          alt="${this.zone?.display_name} camera view"
          @error=${() => this.error = 'Failed to load image'}
        />
        ${this.renderAnalysisMarkers()}
      </div>
    `;
  }

  renderImageInfo() {
    if (!this.imageUrl) return '';

    return html`
      <div class="image-info">
        <div class="image-meta">
          <span>📅 ${new Date().toLocaleString()}</span>
          <span>📷 ${this.zone?.camera_entity_id}</span>
        </div>
        
        <div class="image-actions">
          <button class="action-btn" @click=${this.downloadImage}>
            💾 Download
          </button>
          <button class="action-btn" @click=${this.refreshImage}>
            🔄 Refresh
          </button>
        </div>
      </div>
    `;
  }

  renderAnalysisSummary() {
    const score = this.lastAnalysis.cleanliness_score || 0;
    const tasksCount = this.lastAnalysis.tasks_detected || 0;
    
    return html`
      <div class="analysis-summary">
        <div class="summary-title">Latest Analysis</div>
        <div class="summary-content">
          <div class="score-display">
            <div class="score-circle ${this.getScoreClass(score)}">
              ${score}
            </div>
            <div>
              <div style="font-weight: 500;">${this.getScoreText(score)}</div>
              <div style="font-size: 11px; color: var(--secondary-text-color);">
                Cleanliness Score
              </div>
            </div>
          </div>
          
          <div class="tasks-summary">
            <div>${tasksCount} tasks detected</div>
            <div style="font-size: 11px; color: var(--secondary-text-color);">
              ${new Date(this.lastAnalysis.created_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>
    `;
  }
}
