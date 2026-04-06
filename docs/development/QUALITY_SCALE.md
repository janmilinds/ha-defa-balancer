# Integration Quality Scale — DEFA Balancer

> Assessed against [Home Assistant Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale).
> Version: 1.0.0-beta.4 | Date: 2026-04-05

## Bronze

- [x] `action-setup` — No service actions defined; N/A (nothing to register)
- [x] `appropriate-polling` — Not a polling integration (`local_push`); DataUpdateCoordinator reads from a ring buffer on a 10 s interval
- [x] `brands` — Brand assets in `custom_components/defa_balancer/brand/` (icon, logo, @2x variants)
- [x] `common-modules` — Base entity in `entity/base.py`, coordinator in `coordinator/`, data class in `data.py`
- [x] `config-flow-test-coverage` — Config flow tests cover user, scanning, select, retry, already_configured, connection_error, reconfigure, and options flows (full coverage)
- [x] `config-flow` — UI-based config flow with device scanning
  - [x] Uses `data_description` for options flow fields
  - [x] `ConfigEntry.data` for immutable setup data; `ConfigEntry.options` for user-changeable phase voltage
- [x] `dependency-transparency` — No third-party PyPI dependencies;
- [x] `docs-actions` — No service actions; N/A
- [x] `docs-high-level-description` — README.md describes DEFA Balancer product and integration purpose
- [x] `docs-installation-instructions` — `docs/user/GETTING_STARTED.md` provides HACS and manual installation steps
- [x] `docs-removal-instructions` — `docs/user/CONFIGURATION.md` includes removal and uninstall instructions
- [x] `entity-event-setup` — Listener started in `async_setup_entry`, stopped in `async_unload_entry`; entities use coordinator subscription via `CoordinatorEntity`
- [x] `entity-unique-id` — Unique ID = `{entry_id}_{description.key}`, set in base entity
- [x] `has-entity-name` — `_attr_has_entity_name = True` in `DEFABalancerEntity`
- [x] `runtime-data` — `DEFABalancerData` dataclass stored on `entry.runtime_data`
- [x] `test-before-configure` — Config flow scans for UDP multicast packets before allowing device selection
- [x] `test-before-setup` — `async_config_entry_first_refresh()` called; raises `ConfigEntryNotReady` if device unreachable
- [x] `unique-config-entry` — `async_set_unique_id(serial)` + `_abort_if_unique_id_configured()` per device serial

## Silver

- [x] `action-exceptions` — No service actions; N/A
- [x] `config-entry-unloading` — `async_unload_entry` unloads platforms and stops listener
- [x] `docs-configuration-parameters` — `docs/user/CONFIGURATION.md` documents options (phase voltage) and multicast requirements
- [x] `docs-installation-parameters` — Prerequisites (HA version, HACS, network requirements) documented in `docs/user/GETTING_STARTED.md`
- [x] `entity-unavailable` — `CoordinatorEntity` marks entities unavailable when `UpdateFailed` is raised (no data within 15 s)
- [x] `integration-owner` — `"codeowners": ["@janmilinds"]` in `manifest.json`
- [x] `log-when-unavailable` — Coordinator logs `UpdateFailed` on unavailability; clears on recovery
- [x] `parallel-updates` — `PARALLEL_UPDATES = 0` defined in `const.py`, used by sensor platform (read-only coordinator-backed sensors)
- [ ] `reauthentication-flow` — N/A: device uses UDP multicast, no credentials involved
- [x] `test-coverage` — 97 % overall (90 tests across 8 test modules)

## Gold

- [x] `devices` — `DeviceInfo` with manufacturer, model, serial, firmware version
- [x] `diagnostics` — `async_get_config_entry_diagnostics` with `async_redact_data` for serial redaction
- [ ] `discovery-update-info` — N/A: device uses fixed multicast address; no network info to update
- [ ] `discovery` — Scanning-based (not standard HA discovery methods like DHCP/SSDP/Zeroconf); device doesn't support standard discovery protocols
- [x] `docs-data-update` — `docs/user/CONFIGURATION.md` describes push architecture, buffer, unavailability detection, and power calculation
- [x] `docs-examples` — Automation examples in `docs/user/GETTING_STARTED.md` (high power alert, phase imbalance, energy tracking, availability)
- [x] `docs-known-limitations` — `docs/user/CONFIGURATION.md` lists multicast-only, IPv4-only, read-only, single NIC, no energy dashboard, fixed multicast limitations
- [x] `docs-supported-devices` — `docs/user/GETTING_STARTED.md` lists P/N: 715004 as tested, P/N: 715008 as compatible but untested
- [x] `docs-supported-functions` — `docs/user/CONFIGURATION.md` documents all sensors (per-phase current/power, total power) and diagnostic entities
- [x] `docs-troubleshooting` — Both user docs include troubleshooting sections (no device found, unavailable, stale data, debug logging)
- [x] `docs-use-cases` — Phase imbalance, energy tracking, and availability monitoring use cases documented
- [ ] `dynamic-devices` — N/A: single device per config entry; additional devices added via new config entries
- [x] `entity-category` — Diagnostic sensors use `EntityCategory.DIAGNOSTIC`; measurement sensors have no category (correct)
- [x] `entity-device-class` — `SensorDeviceClass.CURRENT` and `SensorDeviceClass.POWER` used appropriately
- [x] `entity-disabled-by-default` — Firmware and packet count diagnostic sensors disabled by default
- [x] `entity-translations` — All entities have translation keys in `translations/en.json`
- [x] `exception-translations` — `ConfigEntryNotReady(translation_key="device_unreachable")` uses translated exception
- [x] `icon-translations` — `icons.json` maps translation keys to MDI icons for all entities
- [ ] `reconfiguration-flow` — `async_step_reconfigure` - integration does not have settings in configuration flow
- [x] `repair-issues` — Persistent repair issue created when device is unreachable for >60 s; cleared on recovery
- [ ] `stale-devices` — N/A: single device per config entry; removing config entry removes the device

## Platinum

- [x] `async-dependency` — No external dependencies; all I/O is async (`asyncio`, `aiohttp`)
- [ ] `inject-websession` — N/A: no HTTP API client; uses raw UDP multicast socket
- [ ] `strict-typing` — Pyright configured for basic mode; not full strict typing
