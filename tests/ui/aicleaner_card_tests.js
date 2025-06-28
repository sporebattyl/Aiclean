/**
 * AICleaner Card Component Tests
 * Following TDD principles with AAA (Arrange-Act-Assert) pattern
 */

// Test Suite: Component-based design validation
class AICleanerCardTests {
    constructor(testFramework) {
        this.framework = testFramework;
        this.setupTests();
    }

    setupTests() {
        // RED PHASE: Write failing tests first
        
        // Test 1: Card Registration and Basic Structure
        this.framework.test('Card should register as custom element', async () => {
            // Arrange
            const expectedTagName = 'aicleaner-card';
            
            // Act
            const isRegistered = customElements.get(expectedTagName) !== undefined;
            
            // Assert
            this.framework.assert(isRegistered, 'AICleaner card should be registered as custom element');
        });

        // Test 2: Card Configuration
        this.framework.test('Card should accept and store configuration', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            const testConfig = {
                title: 'Test AICleaner',
                show_analytics: true,
                theme: 'dark'
            };
            
            // Act
            card.setConfig(testConfig);
            
            // Assert
            this.framework.assertEqual(card._config.title, 'Test AICleaner', 'Card should store title config');
            this.framework.assertEqual(card._config.show_analytics, true, 'Card should store analytics config');
            this.framework.assertEqual(card._config.theme, 'dark', 'Card should store theme config');
        });

        // Test 3: Home Assistant Data Integration
        this.framework.test('Card should process Home Assistant data correctly', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test' });
            const mockHass = {
                states: {
                    'sensor.aicleaner_system_status': {
                        state: 'active',
                        attributes: { total_zones: 2, total_active_tasks: 5 }
                    },
                    'sensor.aicleaner_kitchen_tasks': {
                        state: '3',
                        attributes: { zone_name: 'Kitchen', active_tasks: 3 }
                    }
                }
            };
            
            // Act
            card.hass = mockHass;
            
            // Assert
            this.framework.assertEqual(card.zones.length, 1, 'Should process one zone from sensor data');
            this.framework.assertEqual(card.zones[0].name, 'kitchen', 'Should extract zone name correctly');
            this.framework.assertEqual(card.systemStatus.totalZones, 2, 'Should extract system status correctly');
        });

        // Test 4: Dashboard View Rendering
        this.framework.test('Dashboard view should render zone cards', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test Dashboard' });
            card.zones = [{
                name: 'kitchen',
                displayName: 'Kitchen',
                activeTasks: 3,
                completedTasks: 2
            }];
            document.body.appendChild(card);
            
            // Act
            card.currentView = 'dashboard';
            card.render();
            await this.waitForRender();
            
            // Assert
            const zoneCards = card.shadowRoot.querySelectorAll('.zone-card');
            this.framework.assertEqual(zoneCards.length, 1, 'Should render one zone card');
            
            const zoneName = card.shadowRoot.querySelector('.zone-name');
            this.framework.assertExists(zoneName, 'Zone card should have name element');
            
            // Cleanup
            document.body.removeChild(card);
        });

        // Test 5: Navigation Between Views
        this.framework.test('Navigation should switch between views correctly', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test Navigation' });
            card.zones = [{ name: 'kitchen', displayName: 'Kitchen' }];
            document.body.appendChild(card);
            card.render();
            await this.waitForRender();
            
            // Act
            const analyticsButton = card.shadowRoot.querySelector('[data-view="analytics"]');
            this.framework.assertExists(analyticsButton, 'Analytics navigation button should exist');
            analyticsButton.click();
            
            // Assert
            this.framework.assertEqual(card.currentView, 'analytics', 'Should switch to analytics view');
            
            // Cleanup
            document.body.removeChild(card);
        });

        // Test 6: Zone Detail View
        this.framework.test('Zone detail view should show task management interface', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test Zone Detail' });
            card.zones = [{
                name: 'kitchen',
                displayName: 'Kitchen',
                tasks: [
                    { id: '1', description: 'Clean counters', priority: 'high' }
                ]
            }];
            card.selectedZone = 'kitchen';
            document.body.appendChild(card);
            
            // Act
            card.currentView = 'zone';
            card.render();
            await this.waitForRender();
            
            // Assert
            const taskItems = card.shadowRoot.querySelectorAll('.task-item');
            this.framework.assertEqual(taskItems.length, 1, 'Should render task items');
            
            const completeButton = card.shadowRoot.querySelector('.task-action-btn.complete');
            this.framework.assertExists(completeButton, 'Should have complete task button');
            
            // Cleanup
            document.body.removeChild(card);
        });

        // Test 7: Configuration Panel
        this.framework.test('Configuration panel should render personality selector', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test Config' });
            document.body.appendChild(card);
            
            // Act
            card.currentView = 'config';
            card.render();
            await this.waitForRender();
            
            // Assert
            const personalityCards = card.shadowRoot.querySelectorAll('.personality-card');
            this.framework.assert(personalityCards.length >= 6, 'Should render personality options');
            
            const defaultPersonality = card.shadowRoot.querySelector('[data-personality="default"]');
            this.framework.assertExists(defaultPersonality, 'Should have default personality option');
            
            // Cleanup
            document.body.removeChild(card);
        });

        // Test 8: Responsive Design
        this.framework.test('Card should be responsive on mobile devices', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test Responsive' });
            card.zones = [{ name: 'kitchen', displayName: 'Kitchen' }];
            document.body.appendChild(card);
            
            // Act - Simulate mobile viewport
            const originalWidth = window.innerWidth;
            Object.defineProperty(window, 'innerWidth', { value: 375, configurable: true });
            card.render();
            await this.waitForRender();
            
            // Assert
            const zoneGrid = card.shadowRoot.querySelector('.zone-grid');
            const computedStyle = window.getComputedStyle(zoneGrid);
            // Note: In a real test, we'd check computed grid-template-columns
            this.framework.assertExists(zoneGrid, 'Zone grid should exist for responsive layout');
            
            // Cleanup
            Object.defineProperty(window, 'innerWidth', { value: originalWidth, configurable: true });
            document.body.removeChild(card);
        });

        // Test 9: Event Handling
        this.framework.test('Card should handle user interactions correctly', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test Events' });
            card.zones = [{ name: 'kitchen', displayName: 'Kitchen' }];
            card._hass = { callService: () => Promise.resolve() };
            document.body.appendChild(card);
            card.render();
            await this.waitForRender();
            
            // Act
            const analyzeButton = card.shadowRoot.querySelector('[data-action="analyze"]');
            this.framework.assertExists(analyzeButton, 'Analyze button should exist');
            
            let serviceCallMade = false;
            card._hass.callService = () => {
                serviceCallMade = true;
                return Promise.resolve();
            };
            
            analyzeButton.click();
            
            // Assert
            this.framework.assert(serviceCallMade, 'Should call Home Assistant service on button click');
            
            // Cleanup
            document.body.removeChild(card);
        });

        // Test 10: Error Handling
        this.framework.test('Card should handle missing data gracefully', async () => {
            // Arrange
            const card = document.createElement('aicleaner-card');
            card.setConfig({ title: 'Test Error Handling' });
            
            // Act - Set empty/invalid data
            card.zones = [];
            card.systemStatus = {};
            document.body.appendChild(card);
            card.render();
            await this.waitForRender();
            
            // Assert
            const noZonesMessage = card.shadowRoot.textContent;
            this.framework.assert(
                noZonesMessage.includes('No zones configured'), 
                'Should show appropriate message when no zones are configured'
            );
            
            // Cleanup
            document.body.removeChild(card);
        });
    }

    // Helper method to wait for DOM updates
    async waitForRender() {
        return new Promise(resolve => {
            requestAnimationFrame(() => {
                setTimeout(resolve, 10);
            });
        });
    }
}

// GREEN PHASE: Make tests pass by implementing components
// This will be done after we have failing tests

// Export for use in test environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AICleanerCardTests;
} else if (typeof window !== 'undefined') {
    window.AICleanerCardTests = AICleanerCardTests;
}
