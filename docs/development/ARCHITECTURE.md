# Architecture Overview

This document describes the technical architecture of the DEFA Balancer custom component for Home Assistant.

## Directory Structure

```text
custom_components/defa_balancer/
├── __init__.py              # Integration setup and unload
├── config_flow.py           # Config flow entry point
├── const.py                 # Constants and configuration keys
├── data.py                  # Data classes and type definitions
├── diagnostics.py           # Diagnostic data for troubleshooting
├── manifest.json            # Integration metadata
├── repairs.py               # Repair flows for fixing issues
├── api/                     # UDP packet parser
│   ├── __init__.py
│   └── client.py            # parse_packet() function
├── coordinator/             # Data update coordinator
│   ├── __init__.py          # Exports coordinator class
│   ├── base.py              # Main coordinator class
│   └── listeners.py         # UDP listener implementations
├── entity/                  # Base entity class
│   ├── __init__.py
│   └── base.py              # DEFABalancerEntity
├── entity_utils/            # Entity helpers
│   ├── __init__.py
│   ├── device_info.py       # Device info mapping
│   └── state_helpers.py     # State formatting
├── config_flow_handler/     # Config flow
│   ├── __init__.py
│   ├── config_flow.py       # Discovery and setup + inline config form schemas
│   └── schemas/             # Reserved for future form schemas (currently unused)
│       ├── __init__.py
│       └── config.py        # Placeholder for extracted config form schema
├── sensor/                  # Sensor entities
│   ├── __init__.py          # Platform setup
│   └── measurement.py       # Individual sensors (L1/L2/L3 current/power, total)
├── translations/            # Localization files (da, de, en, fi, nb, sv)
├── utils/                   # Integration-wide utilities
└── brand/                   # Brand assets (logos, etc.)
```

## Core Components

### Data Update Coordinator

**Directory:** `coordinator/`

The coordinator package manages data aggregation from UDP multicast packets and distributes
updates to all entities:

**Package structure:**

- `base.py` - Main coordinator class (`DEFABalancerDataUpdateCoordinator`)
- `listeners.py` - UDP listener implementations (`UDPBalancerListener`, `MockBalancerListener`, `_DatagramProtocol`)

**Core functionality:**

- Updates every 10 seconds from device broadcasts
- Aggregates an average over the most recent buffered packets (up to 25) for current values (L1, L2, L3)
- Calculates phase power using 230V fixed voltage
- Error handling (stale timeout after 15 seconds)
- Shared data access for all entities
- Automatic retry on failures

**Key classes:**

- `DEFABalancerDataUpdateCoordinator` (exported from `coordinator/__init__.py`)
- `UDPBalancerListener` (real UDP multicast implementation)
- `MockBalancerListener` (for testing)

**Design rationale:**

The coordinator aggregates packet data to smooth out individual transmission noise:

- **Ring buffer averaging**: Averages all buffered packets (up to 25) to reduce jitter in reported currents
- **Power calculation**: Uses fixed 230V per-phase voltage (DEFA standard)
- **Stale timeout**: Marks unavailable after 15 seconds without data
- **Packet buffering**: Maintains ring buffer of 25 latest packets

### API Client (Packet Parser)

**Directory:** `api/`

Handles parsing of incoming UDP multicast packets:

- `parse_packet()`: Validates and parses 54-byte DEFA protocol packets
- Extracts: serial number (L4-prefixed), L1/L2/L3 currents (mA), firmware version
- Returns `BalancerPacket` dataclass or `None` on parse error
- Rejects packets not exactly 54 bytes

**Key functions:** `parse_packet()`

**Protocol format:** 54-byte little-endian binary with fixed field layout

### Config Flow

**Directory:** `config_flow_handler/`

Implements the discovery and configuration UI for the integration:

**Structure:**

- `config_flow.py`: Main flow (discovery, selection, connection error handling)
- `schemas/`: Voluptuous schemas for forms

**Supported flows:**

- **User (discovery):** Network scan → device selection → entry creation
- **Connection error:** Handles multicast socket failures during discovery
- **Retry:** Menu-based retry after empty scan

**Key class:** `DEFABalancerConfigFlowHandler`

**Flow design:**

- Scans network for up to 15 seconds (5s initial + 10s retry if nothing found)
- No credentials or IP entry needed (all via multicast discovery)
- Handles multiple devices on same network

### Base Entity

**Package:** `entity/`

Provides common functionality for all entities in the integration:

- Device information
- Unique ID generation
- Coordinator integration
- Availability tracking

**Key class:** `DEFABalancerEntity` (in `entity/base.py`)

## Platform Organization

Each platform (sensor, binary_sensor, switch, etc.) follows this pattern:

```text
<platform>/
├── __init__.py              # Platform setup: async_setup_entry()
└── <entity_name>.py         # Individual entity implementation
```

Platform entities inherit from both:

1. Home Assistant platform base (e.g., `SensorEntity`)
2. `DEFABalancerEntity` for common functionality

## Data Flow

```text
┌─────────────────┐
│  Config Entry   │ ← Created by config flow
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ UDP Listener    │ ← Receives multicast packets from DEFA Balancer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Coordinator    │ ← Aggregates packets every 10 seconds
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │  Data   │ ← Stored in coordinator.data
    └────┬────┘
         │
    ┌────┴────────────────┐
    │         ...         │
    ▼                     ▼
┌─────────┐         ┌─────────┐
│ Sensor  │         │ Sensor  │ ← 7 sensor entities
└─────────┘         └─────────┘
```

## AI Agent Instructions

This project includes comprehensive instruction files for AI coding assistants (GitHub Copilot, Claude, etc.) to ensure consistent code generation that follows Home Assistant patterns and project conventions.

### Instruction File Architecture

**Layered approach:**

1. **`AGENTS.md`** - High-level "survival guide" for all AI agents (project overview, workflow, validation)
2. **`.github/instructions/*.instructions.md`** - Detailed path-specific patterns (applied based on file being edited)
3. **`.github/copilot-instructions.md`** - GitHub Copilot-specific workflow guidance

### Available Instruction Files

| File | Applies To | Purpose |
|------|------------|---------|
| `python.instructions.md` | `**/*.py` | Python code style, imports, type hints, async patterns, linting |
| `yaml.instructions.md` | `**/*.yaml`, `**/*.yml` | YAML formatting, Home Assistant YAML conventions |
| `json.instructions.md` | `**/*.json` | JSON formatting, schema validation, no trailing commas |
| `markdown.instructions.md` | `**/*.md` | Markdown formatting, documentation structure, linting |
| `manifest.instructions.md` | `**/manifest.json` | Integration manifest requirements, quality scale, IoT class |
| `configuration_yaml.instructions.md` | `**/configuration.yaml` | Home Assistant configuration patterns (deprecated for device integrations) |
| `config_flow.instructions.md` | `**/config_flow_handler/**/*.py`, `**/config_flow.py` | Config flow patterns, discovery, reauth, reconfigure, unique IDs |
| `service_actions.instructions.md` | `**/service_actions/**/*.py` | Service action implementation, registration in `async_setup()`, error handling |
| `services_yaml.instructions.md` | `**/services.yaml` | Service action definitions, schema, descriptions, examples (legacy filename) |
| `entities.instructions.md` | Entity platform files | Entity implementation, EntityDescription, device info, state management |
| `coordinator.instructions.md` | `**/coordinator/**/*.py`, `**/api/**/*.py` | DataUpdateCoordinator patterns, error handling, caching, pull vs push |
| `api.instructions.md` | `**/api/**/*.py`, `**/coordinator/**/*.py` | API client implementation, exceptions, rate limiting, pagination |
| `diagnostics.instructions.md` | `**/diagnostics.py` | Diagnostics data collection, `async_redact_data()` for sensitive data |
| `repairs.instructions.md` | `**/repairs.py` | Repair flows, issue creation, severity levels, fix flows |
| `translations.instructions.md` | `**/translations/*.json` | Translation file structure, placeholders, nested keys |
| `tests.instructions.md` | `tests/**/*.py` | Test patterns, fixtures, mocking, pytest conventions |

**Note:** Entity platform files include: `alarm_control_panel/**/*.py`, `binary_sensor/**/*.py`, `button/**/*.py`, `camera/**/*.py`, `climate/**/*.py`, `cover/**/*.py`, `fan/**/*.py`, `humidifier/**/*.py`, `light/**/*.py`, `lock/**/*.py`, `number/**/*.py`, `select/**/*.py`, `sensor/**/*.py`, `siren/**/*.py`, `switch/**/*.py`, `vacuum/**/*.py`, `water_heater/**/*.py`, `entity/**/*.py`, `entity_utils/**/*.py`

### Instruction File Application

**GitHub Copilot:**

Uses frontmatter `applyTo` patterns to automatically apply instructions based on file being edited:

```yaml
---
applyTo:
  - "**/*.py"
---
```

**Other AI Agents:**

Typically read `AGENTS.md` for project overview and may use path-specific instructions when available.

### Benefits

- ✅ **Consistent code quality** - AI generates code that passes validation on first run
- ✅ **Home Assistant patterns** - Follows Core development standards and best practices
- ✅ **Context-aware** - File-specific instructions ensure appropriate patterns
- ✅ **Reduced iteration** - Fewer validation errors and corrections needed
- ✅ **Knowledge transfer** - Instructions document project conventions and decisions

### Maintaining Instructions

- Keep `AGENTS.md` concise (high-level guidance only, ~30,000 ft view)
- Put detailed patterns in path-specific `.instructions.md` files
- Update instructions when patterns change or new conventions emerge
- Remove outdated rules to prevent bloat
- Document major architectural decisions in `DECISIONS.md`

### Using GitHub Copilot Coding Agent

**GitHub Copilot Coding Agent** ([github.com/copilot/agents](https://github.com/copilot/agents)) can autonomously initialize new projects from this template and implement features.

**Template Initialization:**

When creating a repository from this template, you can provide a prompt to Copilot Coding Agent that includes:

- Integration domain, title, and repository details
- Instructions to run `initialize.sh` in unattended mode with `--force` flag
- The agent will set up the project and create an initialization pull request

**Working with initialized projects:**

Once a project is initialized, Copilot Coding Agent:

- Automatically reads all instruction files (`AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`)
- Runs validation scripts (`script/check`) to verify changes
- Creates pull requests with comprehensive implementations
- Can iterate based on test failures and linter errors

**Agent-specific instructions (since November 2025):**

Use `excludeAgent` frontmatter to control which agents use specific instructions:

```yaml
---
applyTo: "**/*.py"
excludeAgent: "code-review"  # Only coding-agent uses this
---
```

See [`.github/COPILOT_CODING_AGENT.md`](../../.github/COPILOT_CODING_AGENT.md) for detailed usage instructions, example prompts, and troubleshooting.

## Key Design Decisions

See [DECISIONS.md](./DECISIONS.md) for architectural and design decisions made during development.

## Extension Points

To add new functionality:

### Adding a New Platform

1. Create directory: `custom_components/defa_balancer/<platform>/`
2. Implement `__init__.py` with `async_setup_entry()`
3. Create entity classes inheriting from platform base + `DEFABalancerEntity`
4. Add platform to `PLATFORMS` in `const.py`

### Adding a New Service Action

1. Create service action handler in `service_actions/<service_name>.py`
2. Define service action in `services.yaml` (legacy filename) with schema
3. Register service action in `__init__.py:async_setup()` (NOT `async_setup_entry`)

### Modifying Data Structure

1. Update coordinator data type in `coordinator.py`
2. Adjust API client response parsing in `api/client.py`
3. Update entity property implementations to match new structure

## Testing Strategy

- **Unit tests:** Test individual functions and classes in isolation
- **Integration tests:** Test coordinator with mocked API
- **Fixtures:** Shared test fixtures in `tests/conftest.py`

Tests mirror the source structure under `tests/`.

## Dependencies

Core dependencies (see `manifest.json`):

- `aiohttp` - Async HTTP client
- Home Assistant 2025.7.0+ - Platform requirements

Development dependencies (see `requirements_dev.txt`, `requirements_test.txt`).
