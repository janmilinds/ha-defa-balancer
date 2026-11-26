---
name: "DEFA Balancer Sensors"
description: "What the current and power sensors measure, and what stays unchanged about them"
applyTo: "custom_components/defa_balancer/sensor/**/*.py, custom_components/defa_balancer/coordinator/**/*.py"
paths:
  - "custom_components/defa_balancer/sensor/**/*.py"
  - "custom_components/defa_balancer/coordinator/**/*.py"
---

# DEFA Balancer Sensor Instructions

**Procedure:** `haci-entity-platform` (plugin `haci-build`) — load it before adding or changing a sensor. This file adds
only what is specific to this integration.

## Traps

- **Keep the power sensors as `SensorDeviceClass.POWER` in W, calculated as current × phase voltage.** The value is
  apparent power, and that is a deliberate, documented trade-off — do not relabel it as VA, add VA sensors or apply an
  assumed power factor.

Source: docs/development/decisions/20261126-power-sensors-stay-estimates.md
