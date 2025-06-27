/**
 * AICleaner Card Editor
 * 
 * Configuration editor for the AICleaner Lovelace card
 */

class AICleanerCardEditor extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this._config = {};
        this._hass = {};
    }

    setConfig(config) {
        this._config = { ...config };
        this.render();
    }

    set hass(hass) {
        this._hass = hass;
    }

    render() {
        if (!this.shadowRoot) return;

        this.shadowRoot.innerHTML = `
            <style>
                .card-config {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    padding: 16px;
                }
                
                .config-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 16px;
                }
                
                .config-row label {
                    flex: 1;
                    font-weight: 500;
                }
                
                .config-row input,
                .config-row select {
                    flex: 2;
                    padding: 8px;
                    border: 1px solid var(--divider-color);
                    border-radius: 4px;
                    background: var(--card-background-color);
                    color: var(--primary-text-color);
                }
                
                .config-section {
                    border: 1px solid var(--divider-color);
                    border-radius: 8px;
                    padding: 16px;
                    margin: 8px 0;
                }
                
                .config-section h3 {
                    margin: 0 0 16px 0;
                    color: var(--primary-text-color);
                    font-size: 1.1em;
                }
                
                .checkbox-row {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .checkbox-row input[type="checkbox"] {
                    width: auto;
                    flex: none;
                }
                
                .help-text {
                    font-size: 0.9em;
                    color: var(--secondary-text-color);
                    margin-top: 4px;
                }
            </style>
            
            <div class="card-config">
                <div class="config-section">
                    <h3>Basic Settings</h3>
                    
                    <div class="config-row">
                        <label for="title">Card Title:</label>
                        <input 
                            type="text" 
                            id="title" 
                            .value="${this._config.title || 'AICleaner'}"
                            @input="${this._valueChanged}"
                        />
                    </div>
                    <div class="help-text">The title displayed at the top of the card</div>
                </div>
                
                <div class="config-section">
                    <h3>Display Options</h3>
                    
                    <div class="config-row checkbox-row">
                        <input 
                            type="checkbox" 
                            id="show_analytics" 
                            ?checked="${this._config.show_analytics !== false}"
                            @change="${this._valueChanged}"
                        />
                        <label for="show_analytics">Show Analytics Tab</label>
                    </div>
                    <div class="help-text">Display the analytics dashboard with charts and insights</div>
                    
                    <div class="config-row checkbox-row">
                        <input 
                            type="checkbox" 
                            id="show_config" 
                            ?checked="${this._config.show_config !== false}"
                            @change="${this._valueChanged}"
                        />
                        <label for="show_config">Show Settings Tab</label>
                    </div>
                    <div class="help-text">Display the configuration panel for managing settings</div>
                </div>
                
                <div class="config-section">
                    <h3>Theme</h3>
                    
                    <div class="config-row">
                        <label for="theme">Color Theme:</label>
                        <select id="theme" @change="${this._valueChanged}">
                            <option value="default" ?selected="${this._config.theme === 'default'}">Default</option>
                            <option value="dark" ?selected="${this._config.theme === 'dark'}">Dark</option>
                            <option value="light" ?selected="${this._config.theme === 'light'}">Light</option>
                            <option value="auto" ?selected="${this._config.theme === 'auto'}">Auto</option>
                        </select>
                    </div>
                    <div class="help-text">Choose the color theme for the card</div>
                </div>
                
                <div class="config-section">
                    <h3>Advanced</h3>
                    
                    <div class="config-row">
                        <label for="update_interval">Update Interval (seconds):</label>
                        <input 
                            type="number" 
                            id="update_interval" 
                            min="5" 
                            max="300" 
                            .value="${this._config.update_interval || 30}"
                            @input="${this._valueChanged}"
                        />
                    </div>
                    <div class="help-text">How often to refresh data from Home Assistant (5-300 seconds)</div>
                    
                    <div class="config-row checkbox-row">
                        <input 
                            type="checkbox" 
                            id="compact_mode" 
                            ?checked="${this._config.compact_mode === true}"
                            @change="${this._valueChanged}"
                        />
                        <label for="compact_mode">Compact Mode</label>
                    </div>
                    <div class="help-text">Use a more compact layout for smaller screens</div>
                </div>
            </div>
        `;
    }

    _valueChanged(ev) {
        if (!this._config || !this._hass) {
            return;
        }

        const target = ev.target;
        const configValue = target.type === 'checkbox' ? target.checked : target.value;
        
        if (this[`_${target.id}`] === configValue) {
            return;
        }
        
        const newConfig = {
            ...this._config,
            [target.id]: configValue
        };

        // Clean up undefined values
        Object.keys(newConfig).forEach(key => {
            if (newConfig[key] === undefined) {
                delete newConfig[key];
            }
        });

        this._config = newConfig;
        
        // Fire config changed event
        const event = new CustomEvent('config-changed', {
            detail: { config: this._config },
            bubbles: true,
            composed: true
        });
        this.dispatchEvent(event);
    }
}

customElements.define('aicleaner-card-editor', AICleanerCardEditor);
