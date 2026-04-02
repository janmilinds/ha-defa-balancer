# Getting Started with DEFA Balancer

This guide will help you install and set up the DEFA Balancer custom integration for Home Assistant.

## Prerequisites

- Home Assistant 2024.1 or newer
- HACS (Home Assistant Community Store) installed
- DEFA Balancer device on the same network as Home Assistant
- Multicast traffic (group `234.222.250.1`) allowed on your network

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
4. The integration will scan your network for up to 15 seconds

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
|---|---|---|
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
      - trigger: numeric_state
        entity_id: sensor.defa_balancer_xxxx_total_power
        above: 10000
    action:
      - action: notify.notify
        data:
          message: "Total power exceeded 10 kW: {{ trigger.to_state.state }} W"
```

## Troubleshooting

### No Device Found During Setup

If the integration doesn't find your Balancer during the 15-second scan:

1. Verify the DEFA Balancer is powered on and connected to the network
2. Confirm Home Assistant is on the same subnet/VLAN
3. Check if multicast traffic is allowed on your router
4. Try again — the integration will re-scan

### Sensors Show "Unavailable"

This means the Balancer stopped sending data for more than 15 seconds:

1. Check power to the DEFA Balancer
2. Verify the network cable is connected
3. Ensure the Balancer is still on the same subnet
4. Try reloading the integration from **Settings** → **Devices & Services**

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
