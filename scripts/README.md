# Scripts Directory

This directory contains utility scripts organized by type.

## Structure

- **python/** - Python utility scripts for Home Assistant integration
- **js/** - JavaScript scripts for testing MCP servers
- **utilities/** - General utility scripts

## Python Scripts

- `ha_addon_manager.py` - Home Assistant addon management utilities
- `ha_auth_component.py` - Authentication component setup
- `ha_service_manager.py` - Service management utilities
- `lovelace_card_installer.py` - Lovelace card installation utilities
- `setup_ha_auth.py` - Home Assistant authentication setup
- `setup_ha_service.py` - Service setup utilities
- `simple_ha_service_integration.py` - Simple service integration
- `debug_integration_test.py` - Integration debugging utilities
- `set_ha_token_env.py` - Environment token setup

## JavaScript Scripts

- `test-individual-services.js` - Individual MCP service testing
- `test-mcp-servers.js` - MCP server testing utilities

## Usage

Run scripts from the project root directory:
```bash
python scripts/python/script_name.py
node scripts/js/script_name.js
```
