# Configuration Reference

This document describes all configuration options for the DEFA Balancer custom integration.

## Discovery and Setup

The DEFA Balancer uses automatic network discovery. When you add the integration:

1. The integration scans your network for DEFA Balancer devices (multicast group `234.222.250.1` on UDP port `57082`)
2. Devices are detected and listed automatically
3. Select a device to begin monitoring

**No manual IP or authentication configuration is needed.**

## Multicast Network Requirements

For discovery and operation:

- Home Assistant must be on the same subnet or VLAN as the DEFA Balancer
- Multicast traffic to `234.222.250.1:57082` must be allowed (check router/firewall)
- Both devices should be on IPv4 networks (IPv6 multicast not currently supported)

## Update Interval

Data updates are processed by Home Assistant every 10 seconds by default from the Balancer's multicast broadcasts. The Balancer's multicast behavior is determined by the device firmware, while the integration's default 10-second update interval is set in its configuration (not currently adjustable via the Home Assistant UI).

## Entity Customization

You can customize individual entity properties via the Home Assistant UI:

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find and click the entity (e.g., "Balancer L1 Current")
3. Click the settings icon
4. Modify:
   - **Entity ID** - Unique identifier (used in automations)
   - **Name** - Display name
   - **Icon** - Visual icon (e.g., `mdi:lightning-bolt`)
   - **Area assignment** - Organize into rooms/areas

### Disabling Entities

If you don't need certain entities:

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find the entity
3. Click it, then click **Settings** icon
4. Toggle **Enable entity** off

Disabled entities won't update or consume resources.

## Sensors Provided

The integration creates the following sensors for each DEFA Balancer:

### Per-Phase Sensors

- **L1 Current** (A) - Amperage on phase 1
- **L2 Current** (A) - Amperage on phase 2
- **L3 Current** (A) - Amperage on phase 3
- **L1 Power** (W) - Calculated power on phase 1 (current × 230V)
- **L2 Power** (W) - Calculated power on phase 2 (current × 230V)
- **L3 Power** (W) - Calculated power on phase 3 (current × 230V)

### Total Sensor

- **Total Power** (W) - Sum of L1, L2, and L3 power

All values update every 10 seconds.

## Troubleshooting

### "No devices found" during setup

1. Verify DEFA Balancer is powered on and connected to network
2. Confirm Home Assistant is on the same subnet/VLAN
3. Check if multicast traffic is allowed:
   - Log in to your router
   - Disable IGMP snooping (if available)
   - Ensure multicast is not blocked
4. Power-cycle the DEFA Balancer by turning it off and on again
5. Try adding the integration again (scans for up to 10 seconds)

### Sensors show "unavailable"

1. Check power to DEFA Balancer
2. Verify network cable is connected
3. Check if Balancer is on same subnet as Home Assistant
4. Power-cycle the DEFA Balancer by turning it off and on again
5. Restart the integration:
   - Go to **Settings** → **Devices & Services**
   - Find "DEFA Balancer"
   - Click the three dots
   - Select "Reload"

### Stale data warning

If sensors show "unavailable" after 15 seconds without updates (or stay "unknown" and never receive a first value):

1. Check network connectivity
2. Look for firewall or multicast blocking
3. Power-cycle the DEFA Balancer by turning it off and on again
4. Restart Home Assistant to force reconnection

## Diagnostic Data

The integration provides diagnostic data for troubleshooting:

1. Go to **Settings** → **Devices & Services**
2. Find "DEFA Balancer"
3. Click on the device
4. Click **Download Diagnostics**

Diagnostic data includes current sensor states and connection information. Review before sharing publicly.
