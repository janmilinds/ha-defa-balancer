# Configuration Reference

This document describes all configuration options for the DEFA Balancer custom integration.

## Discovery and Setup

The DEFA Balancer uses automatic network discovery. When you add the integration:

1. The integration scans your network for DEFA Balancer devices (multicast group `234.222.250.1` on UDP port `57082`)
2. Devices are detected and listed automatically
3. Select a device to begin monitoring

**No manual IP or authentication configuration is needed.**

## Supported Devices

All DEFA Balancer devices that broadcast via multicast UDP should be compatible. The integration communicates using the standard Balancer multicast protocol.

| Part Number | Device | Status |
| --- | --- | --- |
| P/N: 715004 | DEFA Balancer | Verified |
| P/N: 715008 | DEFA Balancer S | Compatible (untested) |

If you have a DEFA Balancer model not listed here, please report your experience via [GitHub Issues](https://github.com/janmilinds/ha-defa-balancer/issues).

## Multicast Network Requirements

For discovery and operation:

- Home Assistant must be on the same subnet or VLAN as the DEFA Balancer
- Multicast traffic to `234.222.250.1:57082` must be allowed (check router/firewall)
- Both devices should be on IPv4 networks (IPv6 multicast not currently supported)

## How Data Is Updated

The DEFA Balancer uses a **push architecture** — data flows from device to Home Assistant without polling:

1. **Device broadcasts:** The Balancer continuously sends UDP multicast packets containing current measurements and firmware version
2. **Listener captures:** The integration's UDP listener receives packets and stores them in a ring buffer (last 25 packets)
3. **Coordinator reads:** Every 10 seconds, the DataUpdateCoordinator reads the latest packets from the buffer and updates entity states
4. **Unavailability detection:** If no fresh packet arrives within 15 seconds, sensors are marked "unavailable"
5. **Offline repair issue:** If the device remains unreachable for 60 seconds, a persistent repair issue is created to notify the user

### Power Calculation

Power values (W) are calculated from current (A) × phase voltage. The default phase voltage is 230V and can be adjusted per device in **Settings** → **Devices & Services** → DEFA Balancer → **Configure** (options flow).

### Options

| Option | Default | Range | Description |
| --- | --- | --- | --- |
| Phase voltage | 230 V | 100–250 V | Voltage used for power calculation |

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

## Known Limitations

- **Power measurement accuracy:** Power is calculated as `current × phase voltage`. The integration does not measure voltage or power factor. Actual power may differ slightly due to voltage variations (typically ±6% in Nordic grids) and reactive loads such as heat pumps or EV chargers. For typical household monitoring purposes the accuracy is sufficient.
- **Multicast only:** The device communicates via multicast UDP. Routed or VPN-connected Home Assistant instances that cannot receive multicast traffic will not work.
- **IPv4 only:** IPv6 multicast is not supported.
- **No device control:** The integration is read-only — it monitors current and power but cannot control the Balancer or connected chargers.
- **Single network interface:** The listener binds to `0.0.0.0`. On multi-homed hosts, multicast may arrive on an unexpected interface depending on OS routing.
- **No energy dashboard support:** Sensors report instantaneous power (W), not energy (kWh). A Riemann integration helper can be used to create energy sensors.
- **Fixed multicast address:** The multicast group and port are determined by the device firmware and cannot be changed.

## Diagnostic Data

The integration provides diagnostic data for troubleshooting:

1. Go to **Settings** → **Devices & Services**
2. Find "DEFA Balancer"
3. Click on the device
4. Click **Download Diagnostics**

Diagnostic data includes current sensor states and connection information. Review before sharing publicly.

## Removing the Integration

### Remove a Single Device

1. Go to **Settings** → **Devices & Services**
2. Find "DEFA Balancer"
3. Click the three dots next to the entry
4. Select **Delete**
5. Confirm removal

This removes the config entry and all associated entities. Automations referencing these entities will need to be updated.

### Uninstall the Integration Completely

1. Remove all DEFA Balancer config entries (see above)
2. If installed via HACS:
   - Open HACS → **Integrations**
   - Find "DEFA Balancer" → click the three dots → **Remove**
3. If installed manually:
   - Delete the `custom_components/defa_balancer/` directory
4. Restart Home Assistant
