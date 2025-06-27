# AICleaner Lovelace Card

A comprehensive Home Assistant Lovelace card for managing AICleaner v2.0 zones and tasks.

## Features

- **Zone Overview**: View all zones with task counts and status
- **Task Management**: Interactive task completion and management
- **Analytics Dashboard**: Charts and insights (coming soon)
- **Configuration Panel**: Manage settings and preferences (coming soon)
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live data from Home Assistant sensors

## Installation

### Method 1: Manual Installation

1. Copy the card files to your Home Assistant `www` folder:
   ```
   /config/www/aicleaner-card.js
   /config/www/aicleaner-card-editor.js
   ```

2. Add the resource to your Lovelace configuration:
   ```yaml
   resources:
     - url: /local/aicleaner-card.js
       type: module
   ```

3. Add the card to your dashboard:
   ```yaml
   type: custom:aicleaner-card
   title: AICleaner
   ```

### Method 2: Via AICleaner Addon

If you're using the AICleaner addon, the card files are automatically served at:
- `/addons/aicleaner/aicleaner-card.js`
- `/addons/aicleaner/aicleaner-card-editor.js`

Add this resource to your Lovelace configuration:
```yaml
resources:
  - url: /addons/aicleaner/aicleaner-card.js
    type: module
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `title` | string | "AICleaner" | Card title |
| `show_analytics` | boolean | true | Show analytics tab |
| `show_config` | boolean | true | Show settings tab |
| `theme` | string | "default" | Color theme (default, dark, light, auto) |
| `update_interval` | number | 30 | Update interval in seconds |
| `compact_mode` | boolean | false | Use compact layout |

## Example Configuration

```yaml
type: custom:aicleaner-card
title: "Home Cleaning Assistant"
show_analytics: true
show_config: true
theme: auto
update_interval: 15
compact_mode: false
```

## Required Entities

The card automatically detects AICleaner entities:

- `sensor.aicleaner_*_tasks` - Zone task sensors
- `sensor.aicleaner_system_status` - System status sensor

Make sure your AICleaner addon is properly configured and running.

## Views

### Dashboard View
- Overview of all zones
- Task counts and status indicators
- Quick action buttons for analysis
- Last analysis timestamps

### Zone Detail View (Coming Soon)
- Detailed task lists
- Task completion interface
- Zone-specific settings
- Camera snapshots

### Analytics View (Coming Soon)
- Task completion trends
- Zone performance metrics
- System insights and statistics

### Settings View (Coming Soon)
- Notification personality selection
- Ignore rules management
- System configuration

## Troubleshooting

### Card Not Loading
1. Check that the resource is properly added to Lovelace
2. Verify the file path is correct
3. Check browser console for JavaScript errors
4. Ensure AICleaner addon is running

### No Data Showing
1. Verify AICleaner sensors exist in Home Assistant
2. Check that zones are properly configured
3. Ensure the addon has completed at least one analysis cycle

### Styling Issues
1. Try different theme options
2. Check for CSS conflicts with other custom cards
3. Use compact mode for smaller screens

## Development

To modify the card:

1. Edit `aicleaner-card.js` for main functionality
2. Edit `aicleaner-card-editor.js` for configuration options
3. Test changes by refreshing your Lovelace dashboard
4. Use browser developer tools for debugging

## Support

For issues and feature requests, please visit the AICleaner GitHub repository.

## Version History

- **v2.0.0**: Initial release with dashboard view and zone overview
- **v2.1.0**: Coming soon - Zone detail view and task management
- **v2.2.0**: Coming soon - Analytics dashboard
- **v2.3.0**: Coming soon - Configuration panel
