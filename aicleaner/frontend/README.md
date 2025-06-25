# Roo AI Cleaning Assistant v2.0 - Lovelace Card

A comprehensive, modern Lovelace card for the Roo AI Cleaning Assistant that provides multi-zone management, real-time task tracking, performance analytics, and personality-based notifications.

## ✨ Features

### 🏠 **Multi-Zone Management**
- Visual zone overview with status indicators
- Individual zone configuration and settings
- Real-time zone status updates
- Easy zone creation and management

### 📋 **Interactive Task Management**
- Task list with completion tracking
- Circular progress indicators
- Bulk task operations
- Task confidence scoring and priority levels

### 📊 **Performance Analytics**
- Interactive charts and metrics
- Trend analysis and insights
- Customizable time ranges
- Performance summaries and statistics

### 🎭 **Personality-Based Notifications**
- Three distinct personality modes:
  - **Concise**: Direct and factual
  - **Snarky**: Humorous and witty
  - **Encouraging**: Positive and motivational
- Smart notification scheduling
- Interactive notification actions

### 📷 **Visual Analysis**
- Live camera feed integration
- AI analysis overlay with task markers
- Image capture and download
- Analysis trigger controls

### ⚙️ **Configuration Management**
- Zone settings and preferences
- Ignore rules management
- Notification configuration
- System settings

## 🚀 Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Frontend" section
3. Click the "+" button
4. Search for "Roo AI Cleaning Assistant"
5. Install the card
6. Add the card to your Lovelace dashboard

### Manual Installation

1. Download the latest release from GitHub
2. Copy `roo-card.js` to your `www` folder
3. Add the resource to your Lovelace configuration:

```yaml
resources:
  - url: /local/roo-card.js
    type: module
```

## 📝 Configuration

### Basic Configuration

```yaml
type: custom:roo-card
title: "Roo Assistant"
zones:
  - living_room
  - kitchen
  - bedroom
sections:
  - notifications
  - spaces
  - todos
  - performance
```

### Advanced Configuration

```yaml
type: custom:roo-card
config:
  title: "Roo Assistant"
  zones:
    - living_room
    - kitchen
    - bedroom
  sections:
    - notifications
    - spaces
    - todos
    - performance
  layout: "default"  # default, compact, minimal
  update_interval: 30  # seconds
  show_images: true
  theme: "auto"  # auto, light, dark
  notifications:
    enabled: true
    max_items: 5
    auto_dismiss: 300  # seconds
  performance:
    default_range: 30  # days
    show_trends: true
    chart_type: "line"  # line, bar, area
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "Roo Assistant" | Card title |
| `zones` | array | [] | List of zone IDs to display |
| `sections` | array | ["notifications", "spaces", "todos", "performance"] | Sections to show |
| `layout` | string | "default" | Layout mode |
| `update_interval` | number | 30 | Update frequency in seconds |
| `show_images` | boolean | true | Show camera images |
| `theme` | string | "auto" | Theme mode |

## 🎨 Customization

### CSS Custom Properties

The card supports extensive customization through CSS custom properties:

```css
roo-card {
  --roo-primary-color: #2196F3;
  --roo-success-color: #4CAF50;
  --roo-warning-color: #FF9800;
  --roo-error-color: #F44336;
  --roo-card-background: var(--card-background-color);
  --roo-text-primary: var(--primary-text-color);
  --roo-text-secondary: var(--secondary-text-color);
  --roo-border-radius: 12px;
  --roo-spacing: 16px;
}
```

### Theme Integration

The card automatically adapts to Home Assistant themes and supports:
- Light/dark mode detection
- Custom color schemes
- Typography scaling
- Responsive breakpoints

## 📱 Mobile Support

The card is fully responsive and optimized for:
- Mobile phones (portrait/landscape)
- Tablets
- Desktop displays
- Touch interactions
- Accessibility features

## 🔧 Development

### Prerequisites

- Node.js 16+ and npm
- Modern browser with ES2021 support

### Setup

```bash
cd aicleaner/frontend
npm install
```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Format code
npm run format
```

### Project Structure

```
frontend/
├── card/
│   ├── roo-card.js              # Main card component
│   ├── components/              # UI components
│   │   ├── roo-header.js        # Navigation header
│   │   ├── roo-spaces.js        # Zone overview
│   │   ├── roo-todos.js         # Task management
│   │   ├── roo-performance.js   # Analytics dashboard
│   │   ├── roo-config.js        # Configuration panel
│   │   ├── roo-image-viewer.js  # Visual analysis
│   │   └── roo-notifications.js # Notification system
│   └── services/                # Backend services
│       ├── api-service.js       # REST API client
│       └── websocket-service.js # Real-time updates
├── dist/                        # Built files
├── package.json                 # Dependencies
├── rollup.config.js            # Build configuration
└── README.md                   # This file
```

## 🔌 API Integration

The card communicates with the Roo backend through:

### REST API
- Zone management
- Task operations
- Configuration updates
- Performance metrics

### WebSocket
- Real-time task updates
- Live notifications
- Zone status changes
- System events

## 🎯 Usage Examples

### Dashboard View
- Overview of all zones
- Recent notifications
- Task summary
- Performance highlights

### Zone View
- Detailed zone information
- Camera feed with analysis overlay
- Zone-specific tasks
- Performance metrics

### Configuration View
- Zone settings
- Ignore rules
- Notification preferences
- System configuration

## 🐛 Troubleshooting

### Common Issues

**Card not loading**
- Check browser console for errors
- Verify resource is properly added
- Ensure Roo backend is running

**No data displayed**
- Check API connectivity
- Verify zone configuration
- Check Home Assistant logs

**WebSocket connection issues**
- Check network connectivity
- Verify WebSocket endpoint
- Check browser WebSocket support

### Debug Mode

Enable debug logging:

```javascript
window.rooDebug = true;
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Home Assistant community
- Lit web components framework
- Material Design principles
- Contributors and testers

## 📞 Support

- GitHub Issues: Report bugs and feature requests
- Discussions: Community support and questions
- Documentation: Comprehensive guides and examples

---

**Roo AI Cleaning Assistant v2.0** - Making home management intelligent, engaging, and fun! 🤖✨
