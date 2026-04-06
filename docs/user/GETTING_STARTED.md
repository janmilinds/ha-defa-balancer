# Getting Started with DEFA Balancer

This guide will help you install and set up the DEFA Balancer custom integration for Home Assistant.

## Prerequisites

- Home Assistant 2025.12.3 or newer
- HACS (Home Assistant Community Store) installed
- DEFA Balancer device on the same network as Home Assistant
- Multicast UDP traffic to group `234.222.250.1` on port `57082` allowed on your network

## Supported Devices

The integration is designed to work with DEFA Balancer devices that broadcast their data via multicast. It has been tested with P/N: 715004. It should also be compatible with DEFA Balancer S (P/N: 715008), but this has not been explicitly tested.

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/janmilinds/ha-defa-balancer`
6. Set category to "Integration"
7. Click "Add"
8. Find "DEFA Balancer" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/janmilinds/ha-defa-balancer/releases)
2. Extract the `defa_balancer` folder from the archive
3. Copy it to `custom_components/defa_balancer/` in your Home Assistant configuration directory
4. Restart Home Assistant

## Initial Setup

After installation, the integration automatically discovers your DEFA Balancer:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "DEFA Balancer"
4. The integration will scan your network for up to 10 seconds

### Step 1: Device Selection

If your Balancer is found, you'll see it listed:

- Select the device you want to add
- Click **Submit**

If no device is found, check:

- DEFA Balancer is powered on and connected to the network
- Home Assistant is on the same subnet/VLAN
- Your router/switch allows multicast traffic

### Step 2: Configuration

After selection, the integration creates:

- **Device:** Representing your DEFA Balancer
- **Sensors:** L1/L2/L3 current (A) and power (W), plus total power

No additional configuration needed — data updates automatically every 10 seconds.

## What Gets Created

After successful setup, the integration creates:

### Device

- **DEFA Balancer {serial}** — with manufacturer, model, serial number, and firmware version

### Sensors

| Entity | Unit | Description |
| --- | --- | --- |
| L1 Current | A | Phase 1 current |
| L2 Current | A | Phase 2 current |
| L3 Current | A | Phase 3 current |
| L1 Power | W | Phase 1 power (current × 230V) |
| L2 Power | W | Phase 2 power (current × 230V) |
| L3 Power | W | Phase 3 power (current × 230V) |
| Total Power | W | Combined power across all phases |

## First Steps

### Dashboard Cards

Add entities to your dashboard:

1. Go to your dashboard
2. Click **Edit Dashboard** → **Add Card**
3. Choose card type (e.g., "Entities", "Gauge")
4. Select entities from "DEFA Balancer"

Example entities card:

```yaml
type: entities
title: DEFA Balancer
entities:
  - sensor.defa_balancer_xxxx_l1_current
  - sensor.defa_balancer_xxxx_l2_current
  - sensor.defa_balancer_xxxx_l3_current
  - sensor.defa_balancer_xxxx_total_power
```

### Automations

Use the sensors in automations:

**Example — Notify when total power exceeds threshold:**

```yaml
automation:
  - alias: "High power alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.defa_balancer_xxxx_total_power
        above: 10000
    action:
      - service: notify.notify
        data:
          message: "Total power exceeded 10 kW: {{ trigger.to_state.state }} W"
```

### More Use Cases

**Monitor phase imbalance** — alert when one phase draws significantly more than others:

```yaml
automation:
  - alias: "Phase imbalance warning"
    trigger:
      - platform: template
        value_template: >
          {{ (states('sensor.defa_balancer_xxxx_l1_current') | float -
              states('sensor.defa_balancer_xxxx_l2_current') | float) | abs > 10 }}
    action:
      - service: notify.notify
        data:
          message: "Phase imbalance detected between L1 and L2"
```

**Track energy consumption** — create a Riemann sum helper to convert power (W) to energy (kWh) for the Energy dashboard:

1. Go to **Settings** → **Devices & Services** → **Helpers**
2. Click **+ Create Helper** → **Integration — Riemann sum integral**
3. Select `sensor.defa_balancer_xxxx_total_power` as the input sensor
4. Set method to **Left** and precision to 2
5. The resulting kWh sensor can be added to the Energy dashboard

**Track device availability** — log when the Balancer goes offline/online:

```yaml
automation:
  - alias: "Balancer offline"
    trigger:
      - platform: state
        entity_id: sensor.defa_balancer_xxxx_total_power
        to: "unavailable"
    action:
      - service: notify.notify
        data:
          message: "DEFA Balancer went offline"
```

## Troubleshooting

### No Device Found During Setup

If the integration doesn't find your Balancer during the 10-second scan:

1. Verify the DEFA Balancer is powered on and connected to the network
2. Confirm Home Assistant is on the same subnet/VLAN
3. Check if multicast traffic is allowed on your router
4. Power-cycle the DEFA Balancer by turning it off and on again
5. Try again — the integration will re-scan

### Sensors Show "Unavailable"

This means the Balancer stopped sending data for more than 15 seconds:

1. Check power to the DEFA Balancer
2. Verify the network cable is connected
3. Ensure the Balancer is still on the same subnet
4. Power-cycle the DEFA Balancer by turning it off and on again
5. Try reloading the integration from **Settings** → **Devices & Services**

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: warning
  logs:
    custom_components.defa_balancer: debug
```

Add this to `configuration.yaml`, restart, and reproduce the issue. Check logs for detailed information.

## Next Steps

- See [CONFIGURATION.md](./CONFIGURATION.md) for detailed configuration options
- Report issues at [GitHub Issues](https://github.com/janmilinds/ha-defa-balancer/issues)
