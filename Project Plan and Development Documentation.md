Home Assistant AI Cleaning Assistant - v2.0
Project Plan and Development Documentation
1. Project Overview
Project Name: AIClean (Version 2.0)

Concept: An evolution of the original AIClean addon, transforming it into a comprehensive, multi-zone home management assistant. Version 2.0 uses the Google Gemini Vision model to not only generate cleaning tasks but also to track their completion statefully. It supports multiple, independent "zones," features a highly configurable notification engine with different personalities, and is managed through a central Lovelace UI card that mirrors the provided application screenshots.

Core Features v2.0:

Multi-Zone Management: Configure multiple independent "Spaces" or "Zones" (e.g., Kitchen, Living Room), each with its own camera, to-do list, and settings.

Stateful Task Tracking: The AI re-analyzes a room against its active to-do list. When a previously identified mess is no longer visible, the corresponding task is automatically marked as complete.

Configurable Notification Engine: Delivers optional, per-zone notifications for created and completed tasks with selectable "personalities" (e.g., Concise, Snarky, Jarvis, Roaster).

Comprehensive Lovelace UI: A central dashboard to view the latest analyzed image, manage interactive task lists, view performance statistics, and access addon settings, built to match the provided UI mockups.

Advanced In-UI Configuration: An accessible menu within the Lovelace card for managing ignore rules, notification preferences, and other addon settings.

Target User: Home Assistant users who want an intelligent, automated, and interactive system for managing and gamifying home cleanliness across multiple areas.

2. Development Workflow & Testing Mandate
1. Development Environment: All development and testing will occur within a Home Assistant OS environment with full root access. The addon's working directory is /root/addons/aiclean/.

2. Live Reload for Native Development: To enable a fast and efficient debugging loop, the addon must be configured for native live reloading. This allows changes to the Python source code to be reflected immediately in the running container without a full rebuild, providing instant feedback.
* Dockerfile: Create a working directory inside the container. All subsequent commands (COPY, CMD, etc.) will run from this directory.
* config.yaml: Map the addons directory into the container to give it access to the live source code.
* run.sh: The entrypoint script must execute the Python application from the mapped addons directory path: /addons/aiclean/aicleaner/aicleaner.py.

3. Terminal-Based Addon Management: All addon lifecycle management (restarting, rebuilding, viewing logs) will be handled via the Home Assistant CLI (ha) in the integrated VS Code terminal. This eliminates the need for the Home Assistant web UI during development.
* Addon Slug: The target for all commands is the addon's slug: local_aicleaner.
* Essential Commands:
* ha addons rebuild local_aicleaner: Use when Dockerfile or config.yaml changes.
* ha addons restart local_aicleaner: Use for quick restarts after changing Python code.
* ha addons logs local_aicleaner --follow: Use to view a live stream of the addon logs.
* ha supervisor reload: Use to make the supervisor recognize a new addon or changes to config.yaml.
* Automation (Optional but Recommended): Use a .vscode/tasks.json file to create shortcuts for these commands, enabling one-click rebuilds, restarts, and log viewing directly from the VS Code interface.

4. Iterative Build & Test Process: Development must follow an iterative process. For every new feature:
a. Write the code for the feature.
b. Write or update corresponding tests to validate the functionality.
c. Run the full test suite to confirm success and prevent regressions.

5. Comprehensive Test Suite: A robust testing suite using pytest is required and will be maintained in the /root/addons/aiclean/tests/ directory. It must include both Unit and Integration tests as outlined in DesignDocument.md.

3. Development Phases & Timeline (v2.0)
Phase 1: Core Architecture Refactor (4-6 Days)

Phase 2: Stateful AI & Task Completion Logic (5-7 Days)

Phase 3: Notification Engine (3-4 Days)

Phase 4: Lovelace UI Development (6-8 Days)

Phase 5: Advanced Features & Testing (4-6 Days)

4. Configuration (config.yaml) for v2.0
# config.yaml (v2.0)

name: "Roo AI Cleaning Assistant"
version: "2.0.0"
slug: "aicleaner"
description: "Intelligent, multi-zone cleanliness management for your home."
# ... other addon metadata ...
homeassistant_api: true
map:
  - "config:ro"
  - "share:rw"
  - "ssl:ro"
  - "media:rw"
  - "addons:rw"
  - "backup:ro"

options:
  gemini_api_key: null
  display_name: "User"
  zones: []
schema:
  gemini_api_key: secret
  display_name: str
  zones:
    - name: str
      icon: str
      purpose: str
      camera_entity: str
      todo_list_entity: str
      update_frequency: int(1, 168)
      notifications_enabled: bool
      notification_service: str
      notification_personality: list(default|roaster|comedian|jarvis|sargent|snarky)
      notify_on_create: bool
      notify_on_complete: bool

5. run.sh Logic
#!/usr/bin/with-contenv bashio
bashio::log.info "Starting Roo AI Cleaning Assistant v2.0 in LIVE RELOAD mode..."
# Execute from the mapped directory for live reloading
python3 /addons/aiclean/aicleaner/aicleaner.py

6. Lovelace UI Specification
Visual reference files are located in the workspace at /root/addons/aiclean/screenshots/

6.1 Main Dashboard View
Reference: image_f449fb.jpg

Components: Header (Greeting, Settings Icon), Stats Bar, "Spaces" Section (Zone buttons, Add button), "Todos" Section (Summary), Action Button (Camera Icon).

6.2 Space Detail View
Reference: image_f4497f.jpg

Components: Header (Space Name), "Todos" Section (Task list with checkboxes, Progress Circle), "Performance" Section (Line graph, Time window dropdown, Summary stats).

6.3 Create New Space View
Reference: image_f449d9.png

Components: Form fields for Space Name, Space Icon, Purpose, Capture Frequency, and other zone-specific settings.

6.4 Settings View
Reference: image_f44a34.png

Components: Profile (Display Name), Notifications (Notification Style radio buttons, Toggles for event-based notifications).