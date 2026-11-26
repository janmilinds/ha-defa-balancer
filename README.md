# DEFA Balancer

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

Monitor real-time phase currents and estimated power from your [DEFA Balancer](https://www.defa.com/) load management unit directly in Home Assistant.

The DEFA Balancer is a load management module designed for EV charging installations. It continuously broadcasts electrical measurements over the local network, and this integration picks them up automatically — no cloud, no account, no polling.

## Features

- **Automatic discovery** — finds the Balancer on your network, no IP or credentials needed
- **Real-time data** — values updated every 10 seconds from live device broadcasts
- **Per-phase monitoring** — current readings and estimated power for L1, L2, and L3
- **Local only** — all communication stays on your local network

## Sensors

| Sensor      | Unit | Description                                |
| ----------- | ---- | ------------------------------------------ |
| L1 Current  | A    | Phase 1 current                            |
| L2 Current  | A    | Phase 2 current                            |
| L3 Current  | A    | Phase 3 current                            |
| L1 Power    | W    | Phase 1 power, estimated                   |
| L2 Power    | W    | Phase 2 power, estimated                   |
| L3 Power    | W    | Phase 3 power, estimated                   |
| Total Power | W    | Combined estimated power across all phases |

The Balancer measures current only. The power sensors are calculated as current × phase voltage, which gives apparent power rather than the active power your electricity meter measures — close for heaters and EV charging, up to about 40 % too high for heat pumps and electronics. They are good for following load and fuse headroom, not as an energy meter. Details: [power calculation](docs/user/CONFIGURATION.md#power-calculation).

## Requirements

- Home Assistant 2026.11.0 or newer
- DEFA Balancer connected to the same network/subnet/VLAN as Home Assistant, or its multicast traffic forwarded to Home Assistant's VLAN ([details](docs/user/CONFIGURATION.md#home-assistant-on-a-different-vlan))
- Multicast UDP traffic to `234.222.250.1:57082` allowed on your network

## Installation

### Marketplace (recommended)

In the Marketplace, search for "DEFA Balancer" and select **Download**.

<!-- ha-marketplace:exclude-start -->

[![Open your Home Assistant instance and open this repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=janmilinds&repository=ha-defa-balancer&category=integration)

### Manual

1. Download `defa_balancer.zip` from the latest [release](https://github.com/janmilinds/ha-defa-balancer/releases)
2. Extract it into a `custom_components/defa_balancer` folder in your Home Assistant configuration directory
3. Restart Home Assistant

<!-- ha-marketplace:exclude-end -->

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=defa_balancer)

Or go to **Settings** → **Devices & Services** → **Add Integration** → search for **DEFA Balancer**.

The integration scans the network for up to 10 seconds. If your Balancer is on and reachable, it will appear automatically — just confirm the device and you're done.

For more details on setup, configuration, and troubleshooting, see the [getting started guide](docs/user/GETTING_STARTED.md) and [configuration documentation](docs/user/CONFIGURATION.md).

## Troubleshooting

If no device is found during setup, check the following:

- Balancer is powered on and connected to the network
- Home Assistant is on the same subnet/VLAN as the Balancer, or the Balancer's multicast traffic is forwarded to it
- Your router or switch allows multicast traffic (check your router configuration)

For more detailed troubleshooting steps, see the [configuration documentation](docs/user/CONFIGURATION.md).

<!-- ha-marketplace:exclude-start -->

## Contributing

Contributions welcome — open an issue or pull request.

### Development Setup

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/janmilinds/ha-defa-balancer?quickstart=1)

Or locally with Docker and VS Code Dev Containers. See [`docs/development/`](docs/development/) for details.

<!-- ha-marketplace:exclude-end -->

## License

MIT — see [LICENSE](LICENSE).

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/janmilinds/ha-defa-balancer.svg?style=for-the-badge
[commits]: https://github.com/janmilinds/ha-defa-balancer/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/janmilinds/ha-defa-balancer.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40janmilinds-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/janmilinds/ha-defa-balancer.svg?style=for-the-badge
[releases]: https://github.com/janmilinds/ha-defa-balancer/releases
