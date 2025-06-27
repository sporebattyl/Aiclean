# AICleaner v2.0 Lovelace UI Setup Guide

This guide will help you set up the beautiful AICleaner Lovelace card in your Home Assistant dashboard.

## 🎯 Quick Setup

### Step 1: Install the AICleaner Addon
1. Install and configure the AICleaner v2.0 addon
2. Ensure it's running and has created zone sensors

### Step 2: Add the Lovelace Resource
1. Go to **Settings** → **Dashboards** → **Resources**
2. Click **Add Resource**
3. Add this URL: `/addons/aicleaner/aicleaner-card.js`
4. Set Resource Type to **JavaScript Module**
5. Click **Create**

### Step 3: Add the Card to Your Dashboard
1. Edit your dashboard
2. Click **Add Card**
3. Search for "AICleaner Card" or scroll to find it
4. Configure the card settings
5. Save your dashboard

## 🎨 Card Configuration

### Basic Configuration
```yaml
type: custom:aicleaner-card
title: "AICleaner"
```

### Advanced Configuration
```yaml
type: custom:aicleaner-card
title: "Home Cleaning Assistant"
show_analytics: true
show_config: true
theme: auto
update_interval: 15
compact_mode: false
```

## 📱 Features

### Dashboard View
- **Zone Overview**: See all your zones at a glance
- **Task Counts**: Active and completed task indicators
- **Quick Actions**: Analyze zones with one click
- **Status Indicators**: Visual health status for each zone
- **Last Analysis**: Timestamps for recent activity

### Navigation
- **🏠 Dashboard**: Main zone overview
- **📊 Analytics**: Performance charts (coming soon)
- **⚙️ Settings**: Configuration panel (coming soon)

### Interactive Elements
- **Zone Cards**: Click to view detailed zone information
- **Analyze Button**: Trigger immediate zone analysis
- **View Button**: Navigate to zone details
- **Real-time Updates**: Live data from Home Assistant

## 🔧 Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "AICleaner" | Card title displayed at the top |
| `show_analytics` | boolean | true | Show/hide analytics tab |
| `show_config` | boolean | true | Show/hide settings tab |
| `theme` | string | "default" | Color theme (default/dark/light/auto) |
| `update_interval` | number | 30 | Data refresh interval (5-300 seconds) |
| `compact_mode` | boolean | false | Use compact layout for mobile |

## 🎨 Themes

The card supports multiple themes that integrate with your Home Assistant theme:

- **Default**: Uses your current HA theme colors
- **Dark**: Optimized for dark themes
- **Light**: Optimized for light themes  
- **Auto**: Automatically adapts to your theme

## 📱 Mobile Support

The card is fully responsive and includes:
- **Adaptive Grid**: Zones stack on smaller screens
- **Touch-friendly**: Large buttons and touch targets
- **Compact Mode**: Optional condensed layout
- **Flexible Navigation**: Wrapping navigation buttons

## 🔍 Troubleshooting

### Card Not Appearing
1. **Check Resource**: Verify the resource URL is correct
2. **Clear Cache**: Hard refresh your browser (Ctrl+F5)
3. **Check Console**: Look for JavaScript errors in browser dev tools
4. **Addon Status**: Ensure AICleaner addon is running

### No Data Showing
1. **Sensor Check**: Verify `sensor.aicleaner_*_tasks` entities exist
2. **Zone Config**: Ensure zones are properly configured in addon
3. **Analysis Run**: Run at least one analysis cycle
4. **Entity Names**: Check entity naming matches expected pattern

### Styling Issues
1. **Theme Conflicts**: Try different theme options
2. **CSS Conflicts**: Check for conflicts with other custom cards
3. **Mobile Issues**: Enable compact mode for small screens
4. **Browser Support**: Ensure modern browser with ES6 support

## 🚀 Coming Soon

### Zone Detail View
- Detailed task lists with completion buttons
- Zone-specific settings and configuration
- Camera snapshot integration
- Task history and trends

### Analytics Dashboard
- Task completion rate charts
- Zone performance comparisons
- Time-based analysis trends
- System health metrics

### Configuration Panel
- Notification personality selection
- Ignore rules management
- Analysis schedule configuration
- System settings and preferences

## 📋 Required Entities

The card automatically detects these entities created by AICleaner:

### Zone Sensors
- `sensor.aicleaner_kitchen_tasks`
- `sensor.aicleaner_living_room_tasks`
- `sensor.aicleaner_bedroom_tasks`
- *(one for each configured zone)*

### System Sensor
- `sensor.aicleaner_system_status`

### Service Calls
- `aicleaner.run_analysis`
- `aicleaner.complete_task`
- `aicleaner.dismiss_task`

## 💡 Tips & Best Practices

### Dashboard Layout
- Place the card prominently on your main dashboard
- Consider using a full-width layout for better zone visibility
- Group with other cleaning/maintenance cards

### Performance
- Use reasonable update intervals (15-30 seconds)
- Enable compact mode on mobile devices
- Consider hiding unused tabs to reduce clutter

### Integration
- Combine with automation cards for scheduled cleaning
- Add camera cards for visual zone monitoring
- Include notification history cards for task updates

## 🆘 Support

If you encounter issues:

1. **Check Logs**: Review AICleaner addon logs
2. **Browser Console**: Check for JavaScript errors
3. **GitHub Issues**: Report bugs on the project repository
4. **Community**: Ask for help on Home Assistant forums

## 📝 Version History

- **v2.0.0**: Initial release with dashboard view
- **v2.1.0**: Coming soon - Zone detail view
- **v2.2.0**: Coming soon - Analytics dashboard
- **v2.3.0**: Coming soon - Configuration panel

---

**Enjoy your new AICleaner Lovelace card!** 🏠✨
