# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0-beta.4] - 2026-04-06

### Added

- Options flow and a reconfiguration flow to change integration settings after setup.
- Diagnostic sensors exposing internal health and diagnostics data.
- Icons configuration for entities to improve UI presentation.

### Changed

- Reduced device scan timeout and improved scanning behavior for faster discovery.
- Localized and clearer `ConfigEntryNotReady` messages and better edge-case handling.
- Expanded documentation and quality-scale checklist: usage examples, automation examples, known limitations, data update mechanism, and uninstall instructions.
- Refactored and consolidated imports and code layout; quality and test coverage improvements.

### Removed

- Unused `entity_utils` helpers package.

---
**Full Changelog**: https://github.com/janmilinds/ha-defa-balancer/compare/v1.0.0-beta.3...v1.0.0-beta.4


The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta.3] - 2026-04-04

### Added

- Comprehensive test coverage for coordinator, config flow, and entity behavior.
- Raise an issue when the device is unreachable, with a checklist of troubleshooting steps in the issue description.

### Changed

- Diagnostics now redact serial numbers from the config entry title and redact `serial` fields in returned diagnostics data by default.
- Documentation and README updated to reflect troubleshooting guidance and the new behavior.
- Better serial parsing for UDP packets: extract the fixed serial length from the right-hand side.

### Removed

- Interactive repairs/fix flow stub; the "device unreachable" issue is non-fixable.
- Unused utility modules and `entity_utils` helpers.

---
**Full Changelog**: https://github.com/janmilinds/ha-defa-balancer/compare/v1.0.0-beta.2...v1.0.0-beta.3

## [1.0.0-beta.2] - 2026-04-01

### Added

- Translations for Finnish, Swedish, Danish, Norwegian, and German.
- Sensors show as unavailable when the device stops sending data and recover automatically when data resumes.

### Changed

- Setup error message is now clearer when the device is not reachable at startup.

### Fixed

- L1 phase current was read from wrong position in the data stream and showed values roughly 40 times too high.

---
**Full Changelog**: https://github.com/janmilinds/ha-defa-balancer/compare/v1.0.0-beta.1...v1.0.0-beta.2

## [1.0.0-beta.1] - 2026-03-31

### Added

- First beta release of the DEFA Balancer Home Assistant integration.
- Automatic device discovery from the local network during setup.
- Energy monitoring sensors for phase currents, phase power, and total power.
- Clearer setup flow with scanning progress and retry guidance when no device is found.
- Device details shown in Home Assistant (manufacturer, model, firmware, and serial number).
- Local mock balancer script for easy development and testing.

---
**Full Changelog**: https://github.com/janmilinds/ha-defa-balancer/commits/v1.0.0-beta.1
