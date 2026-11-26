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
- Extracts: serial number (L4-prefixed), L1/L2/L3 currents (A), firmware version
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

The agent instructions come from the integration blueprint and are kept current by the weekly template sync:
[`AGENTS.md`](../../AGENTS.md) is the always-loaded entry point, `.agents/instructions/` holds the per-file rules and
`.agents/skills/` the task procedures. [`AI_AGENTS.md`](AI_AGENTS.md) describes the setup.

## Key Design Decisions

Architectural decisions are recorded one per file in [`decisions/`](decisions/README.md).

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
