# Roo - Home Assistant AI Cleaning Assistant
## Project Plan & Development Documentation

---

### 1. Project Overview

**Project Name:** Roo

**Concept:** A Home Assistant add-on that leverages the Google Gemini Vision model to analyze the cleanliness of a room. It takes a snapshot from a user-specified camera entity, submits it to Gemini for a "cleanliness score," and generates an actionable to-do list within Home Assistant to help users tidy up.

**Core Features:**
-   Connects to any Home Assistant camera entity.
-   Securely uses a user-provided Google Gemini API key.
-   Periodically captures an image and sends it for AI analysis.
-   Receives a cleanliness score (e.g., 1-100) and a list of suggested cleaning tasks.
-   Creates a sensor in Home Assistant to track the cleanliness score over time.
-   Populates a selected Home Assistant `todo` list with the generated tasks.
-   Provides configuration options for camera selection, API keys, to-do list selection, and analysis frequency.

**Target User:** Home Assistant users who want to automate and gamify the process of keeping their home tidy.

---

### 2. Guiding AI-Assisted Development

*This section incorporates best practices for ensuring the AI assistant adheres to the project's architecture and coding standards.*

**A. The Design Document (`DesignDocument.md`)**

This file is the single source of truth for all code structure, patterns, and style. The AI assistant **must** read and adhere to this document at all times.

**B. AI Role Definition & "Power Steering"**

When initiating a coding session with the AI, establish a role that forces it to reference our design document. Add this to the AI's system prompt or initial instructions:

> "...You are an expert Home Assistant developer who writes clean, efficient Python code following modern design patterns and best practices. **You must continuously read and refer to the `DesignDocument.md` file to keep your code compliant with its standards and practices. You will not deviate from the examples and structures within it. You will not write to or modify `DesignDocument.md`.**"

**C. Initial Prompting**

Begin each development session with a clear directive that points to the design document:

> "In this project, read and understand `DesignDocument.md` to ensure all generated code aligns with our established architecture. Now, let's work on [specific task]."

**D. File Protection**

To prevent accidental modification by the AI, it is recommended to set the `DesignDocument.md` file to "Read-only" in your operating system.

---

### 3. Keys to Success: A Practical Development Guide

*Follow these principles to ensure a smooth and successful development process.*

**1. Adopt an "Inch-by-Inch" Mindset**
Build the add-on in tiny, individually testable pieces. Before implementing a full feature, break it down into the smallest possible steps. For example, instead of "build the API integration," your first step is "read one value from the config and log it." This makes debugging simple and provides constant forward momentum.

**2. Master Your Logs**
Your logs are your only window into the add-on's behavior.
* **Log Extensively:** Use `bashio::log.info` in `run.sh` and Python's `logging` module to print variable contents, state changes ("Calling API..."), and success/error messages at every critical step.
* **Check Both Log Files:** Remember there are two logs. The **Add-on Log** shows your script's output. The **Supervisor Log** (found in Settings > System > Logs) shows errors related to the add-on's container itself, such as an invalid `config.yaml` or Docker build failure.

**3. Mock Dependencies First**
Before calling external services like Gemini or Home Assistant's API, build mock versions of them first.
* **Mock Gemini:** Create a function that returns a hard-coded, valid JSON response without making a real API call.
* **Mock Camera Snapshots:** Use a static `test_image.jpg` file from within your project instead of calling the `camera.snapshot` service.
This allows you to verify your entire data processing and integration logic independently of network issues or API key problems.

**4. Don't Reinvent the Wheel**
When you get stuck, look at the code for official and popular community add-ons on GitHub. Analyzing their `Dockerfile`, `config.yaml`, and `run.sh` files is the best way to learn proven patterns and solve common problems.

---

### 4. Development Phases & Timeline

This project is broken down into four distinct phases. The estimated timeline is a guideline for a single developer.

* **Phase 1: Project Setup & Design Definition (2-3 Days)**
* **Phase 2: Core Logic - Image Capture & AI Analysis (3-5 Days)**
* **Phase 3: Home Assistant Integration - To-Do List & Sensor (2-3 Days)**
* **Phase 4: Testing, Documentation & Deployment (2-4 Days)**

### Phase 1: Project Setup & Design Definition

*Goal: Create the basic add-on structure and define the coding standards in `DesignDocument.md`.*

**Tasks:**

1.  **Create GitHub Repository & Add-on Directory Structure:**
    * Initialize a new public GitHub repository (`hass-addon-aicleaner`).
    * Create the main add-on directory (`aicleaner/`).
    * Inside `aicleaner/`, create the initial required files: `Dockerfile`, `config.yaml`, `run.sh`, `build.yaml`.

2.  **Define `build.yaml`:**
    * This file specifies the base images for building across different CPU architectures.
    * Example `build.yaml`:
      ```yaml
      build_from:
        aarch64: "ghcr.io/home-assistant/aarch64-base-python:3.12-alpine3.19"
        amd64: "ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.19"
        armv7: "ghcr.io/home-assistant/armv7-base-python:3.12-alpine3.19"
      ```

3.  **Define Initial `config.yaml`:**
    * Set up the basic add-on properties.
      ```yaml
      name: "Roo AI Cleaning Assistant"
      version: "0.1.0"
      slug: "aicleaner"
      description: "AI-powered room cleanliness analysis and to-do list generator."
      url: "[https://github.com/hass-addon-aicleaner](https://github.com/hass-addon-aicleaner)"
      arch:
        - aarch64
        - amd64
        - armv7
      startup: "application"
      boot: "auto"
      # We use 'init: false' because our add-on is a simple, single-process script
      # and does not require the full S6-Overlay init system.
      init: false
      homeassistant_api: true
      # Schema for user-configurable options
      options:
        camera_entity: null
        gemini_api_key: null
        todo_list_entity: null
        update_frequency: 24
      schema:
        camera_entity: str
        gemini_api_key: secret
        todo_list_entity: str
        update_frequency: int(1, 168)
      ```

4.  **Implement a Robust `run.sh`:**
    * This script is the entry point. It reads the configuration and executes the main application in a loop.
      ```bash
      #!/usr/bin/with-contenv bashio

      bashio::log.info "Starting Roo AI Cleaning Assistant..."

      # Read configuration into variables
      CAMERA_ENTITY=$(bashio::config 'camera_entity')
      API_KEY=$(bashio::config 'gemini_api_key')
      TODO_LIST=$(bashio::config 'todo_list_entity')
      # Default to 24 hours if not set, convert hours to seconds
      FREQUENCY=$(bashio::config.get 'update_frequency' 24)
      SLEEP_TIME=$((FREQUENCY * 3600))

      # Main execution loop
      while true; do
        bashio::log.info "Running cleanliness analysis..."

        # Export variables for the Python script to access
        export CAMERA_ENTITY API_KEY TODO_LIST

        # Execute the main Python application
        python3 /app/aicleaner.py

        bashio::log.info "Analysis complete. Sleeping for ${FREQUENCY} hour(s)."
        sleep "${SLEEP_TIME}"
      done
      ```

5.  **Create the Development Design Document (`DesignDocument.md`):**
    * In the project root, create a file named `DesignDocument.md`. This is your architectural blueprint. *Content examples from previous versions remain valid.*

---

### Phase 2: Core Logic - Image Capture & AI Analysis

*Goal: Implement the Python application (`aicleaner.py`) following the patterns in `DesignDocument.md`.*

---

### Phase 3: Home Assistant Integration - To-Do List & Sensor

*Goal: Make the add-on's analysis visible and actionable in Home Assistant.*

---

### Phase 4: Testing, Documentation & Deployment

*Goal: Ensure the add-on is stable, easy to use, and available for others.*

**Tasks:**

1.  **Comprehensive Testing Strategy:**
    * Follow the two-stage testing process (Local Devcontainer & Live Instance) as detailed in the previous version of this plan.

2.  **Enhance Security (AppArmor):**
    * For improved security and to follow best practices, create a basic AppArmor profile.
    * Create a file named `apparmor.txt` in the `aicleaner/` directory.
    * A minimal profile can restrict network access and file permissions. Start with:
      ```
      #include <tunables/global>

      profile hassio-addon-aicleaner flags=(attach_disconnected) {
        #include <abstractions/base>
        #include <abstractions/nameservice>
        #include <abstractions/python>

        # Allow network access for API calls
        network inet stream,
        network inet6 stream,

        # Allow reading config and writing to data
        /data/options.json r,
        /data/** rw,

        # Allow access to supervisor
        /run/supervisor/supervisor.sock rw,
      }
      ```

3.  **Branding & Documentation:**
    * Design and create `icon.png` and `logo.png`.
    * Write comprehensive `README.md` and `DOCS.md` files.

4.  **Prepare for Publishing:**
    * Create a `repository.yaml` file in the root of your GitHub repository.
    * Push all final code, documentation, and configuration to the `main` branch.

5.  **Final Test:**
    * Add your GitHub repository URL to your Home Assistant instance's add-on store.
    * Install and test the add-on as a final user would.

### 5. Project File Structure (Example)


hass-addon-aicleaner/
├── aicleaner/
│   ├── Dockerfile
│   ├── aicleaner.py
│   ├── apparmor.txt
│   ├── build.yaml
│   ├── config.yaml
│   ├── icon.png
│   ├── logo.png
│   └── run.sh
├── .devcontainer/
│   └── devcontainer.json
├── DesignDocument.md
├── README.md
└── repository.yaml