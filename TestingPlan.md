# AI Cleaning Assistant v2.0 - Testing Plan

## Overview
This document defines comprehensive testing specifications for the v2.0 architecture following Test-Driven Development (TDD) principles. All tests follow AAA (Arrange, Act, Assert) pattern and component-based design.

## Testing Structure
```
tests/
├── unit/
│   ├── test_zone.py           # Zone class unit tests
│   ├── test_aicleaner.py      # AICleaner class unit tests
│   ├── test_state_manager.py  # State management unit tests
│   └── test_api_clients.py    # API client unit tests
├── integration/
│   ├── test_zone_integration.py     # Zone workflow integration tests
│   ├── test_multi_zone.py           # Multi-zone coordination tests
│   └── test_end_to_end.py           # Full application workflow tests
├── mocks/
│   ├── mock_ha_api.py         # Home Assistant API mocks
│   ├── mock_gemini_api.py     # Gemini API mocks
│   └── mock_filesystem.py     # File system operation mocks
└── fixtures/
    ├── test_configs.py        # Test configuration data
    ├── test_states.py         # Test state data
    └── test_images.py         # Test image data
```

## Component Testing Specifications

### 1. Zone Class Tests (tests/unit/test_zone.py)

#### Test Cases:
1. **test_zone_initialization**
   - **Arrange**: Valid zone config, state, HA client, Gemini client
   - **Act**: Create Zone instance
   - **Assert**: All attributes properly set, no exceptions

2. **test_zone_initialization_invalid_config**
   - **Arrange**: Invalid zone config (missing required fields)
   - **Act**: Attempt to create Zone instance
   - **Assert**: Raises ValueError with specific message

3. **test_get_camera_snapshot_success**
   - **Arrange**: Mock HA API to return valid image data
   - **Act**: Call get_camera_snapshot()
   - **Assert**: Returns valid file path, file exists, correct API call made

4. **test_get_camera_snapshot_api_failure**
   - **Arrange**: Mock HA API to return error response
   - **Act**: Call get_camera_snapshot()
   - **Assert**: Returns None, error logged, no file created

5. **test_analyze_image_for_completed_tasks_success**
   - **Arrange**: Valid image path, active tasks in state, mock Gemini response
   - **Act**: Call analyze_image_for_completed_tasks()
   - **Assert**: Returns list of completed task IDs, correct prompt sent

6. **test_analyze_image_for_completed_tasks_no_completions**
   - **Arrange**: Valid image path, active tasks, Gemini returns empty list
   - **Act**: Call analyze_image_for_completed_tasks()
   - **Assert**: Returns empty list, no errors

7. **test_analyze_image_for_new_tasks_success**
   - **Arrange**: Valid image path, existing tasks, ignore rules, mock Gemini response
   - **Act**: Call analyze_image_for_new_tasks()
   - **Assert**: Returns list of new task descriptions, ignore rules applied

8. **test_send_notification_task_created**
   - **Arrange**: Notification config, task creation context
   - **Act**: Call send_notification('task_created', context)
   - **Assert**: Correct HA notification service called with formatted message

9. **test_send_notification_disabled**
   - **Arrange**: Notifications disabled in config
   - **Act**: Call send_notification()
   - **Assert**: No API calls made, method returns early

10. **test_run_analysis_cycle_full_workflow**
    - **Arrange**: Mock all dependencies (camera, Gemini, HA API)
    - **Act**: Call run_analysis_cycle()
    - **Assert**: All steps executed in order, state updated, cleanup performed

### 2. AICleaner Class Tests (tests/unit/test_aicleaner.py)

#### Test Cases:
1. **test_aicleaner_initialization_addon_environment**
   - **Arrange**: Set SUPERVISOR_TOKEN environment variable, mock config
   - **Act**: Create AICleaner instance
   - **Assert**: Loads config from environment, creates zone instances

2. **test_aicleaner_initialization_local_environment**
   - **Arrange**: No SUPERVISOR_TOKEN, valid config.yaml file
   - **Act**: Create AICleaner instance
   - **Assert**: Loads config from YAML, creates zone instances

3. **test_load_persistent_state_file_exists**
   - **Arrange**: Valid state.json file with test data
   - **Act**: Call _load_persistent_state()
   - **Assert**: Returns correct state dictionary

4. **test_load_persistent_state_file_missing**
   - **Arrange**: No state.json file
   - **Act**: Call _load_persistent_state()
   - **Assert**: Returns empty dictionary, no errors

5. **test_save_persistent_state_atomic_operation**
   - **Arrange**: State data to save
   - **Act**: Call _save_persistent_state()
   - **Assert**: Creates .tmp file first, then renames, final file has correct content

6. **test_save_persistent_state_write_failure**
   - **Arrange**: Read-only directory or disk full scenario
   - **Act**: Call _save_persistent_state()
   - **Assert**: Handles error gracefully, logs error, doesn't corrupt existing file

### 3. State Management Tests (tests/unit/test_state_manager.py)

#### Test Cases:
1. **test_task_id_generation**
   - **Arrange**: Zone name, timestamp
   - **Act**: Generate task ID
   - **Assert**: Follows format "task_{timestamp}_{zone}_{index}"

2. **test_task_state_transitions**
   - **Arrange**: Task in "active" state
   - **Act**: Mark as completed
   - **Assert**: Status changes to "completed", completed_at timestamp set

3. **test_state_validation**
   - **Arrange**: Invalid state data (missing required fields)
   - **Act**: Validate state
   - **Assert**: Returns validation errors

### 4. API Integration Tests (tests/unit/test_api_clients.py)

#### Test Cases:
1. **test_ha_api_authentication**
   - **Arrange**: Valid HA token and URL
   - **Act**: Make authenticated API call
   - **Assert**: Correct Authorization header sent

2. **test_gemini_api_prompt_formatting**
   - **Arrange**: Task data and image
   - **Act**: Format prompt for Gemini
   - **Assert**: Prompt follows exact specification from DesignDocument.md

## Integration Testing Specifications

### 1. Zone Integration Tests (tests/integration/test_zone_integration.py)

#### Test Cases:
1. **test_complete_analysis_workflow**
   - **Arrange**: Real-like test environment with mocked external APIs
   - **Act**: Run complete zone analysis cycle
   - **Assert**: All components work together, state persisted correctly

2. **test_error_recovery**
   - **Arrange**: Simulate various failure scenarios
   - **Act**: Run analysis cycle
   - **Assert**: Graceful error handling, partial state recovery

### 2. Multi-Zone Tests (tests/integration/test_multi_zone.py)

#### Test Cases:
1. **test_concurrent_zone_analysis**
   - **Arrange**: Multiple zones with different schedules
   - **Act**: Run scheduler
   - **Assert**: Zones analyzed independently, no state conflicts

## Mock Requirements

### Home Assistant API Mock
- Camera snapshot endpoint
- Todo list add/update endpoints
- Sensor state update endpoint
- Notification service endpoint

### Gemini API Mock
- Vision analysis with configurable responses
- Error scenarios (rate limiting, invalid responses)

### File System Mock
- Atomic file operations
- Disk space scenarios
- Permission scenarios

## Test Data Requirements

### Configuration Fixtures
- Valid multi-zone configurations
- Invalid configurations for error testing
- Edge case configurations

### State Fixtures
- Empty state
- State with active tasks
- State with completed tasks
- Corrupted state data

### Image Fixtures
- Test images for analysis
- Invalid image files
- Large image files

## Success Criteria
- All tests pass in isolation
- All tests pass when run together
- 100% code coverage for critical paths
- All error scenarios handled gracefully
- Performance benchmarks met
