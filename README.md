# DEFA Balancer

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

Monitor real-time phase currents and power consumption from your [DEFA Balancer](https://www.defa.com/) load management unit directly in Home Assistant.

The DEFA Balancer is a load management module designed for EV charging installations. It continuously broadcasts electrical measurements over the local network, and this integration picks them up automatically — no cloud, no account, no polling.

## Features

- **Automatic discovery** — finds the Balancer on your network, no IP or credentials needed
- **Real-time data** — values updated every 10 seconds from live device broadcasts
- **Per-phase monitoring** — individual current and power readings for L1, L2, and L3
- **Local only** — all communication stays on your local network

## Sensors

| Sensor | Unit | Description |
|---|---|---|
| L1 Current | A | Phase 1 current |
| L2 Current | A | Phase 2 current |
| L3 Current | A | Phase 3 current |
| L1 Power | W | Phase 1 power |
| L2 Power | W | Phase 2 power |
| L3 Power | W | Phase 3 power |
| Total Power | W | Combined power across all phases |

## Requirements

- Home Assistant 2025.12.3 or newer
- DEFA Balancer connected to the same network/subnet/VLAN as Home Assistant
- Multicast traffic (group `234.222.250.1`) allowed on your network

## Installation

### HACS (Recommended)

Prerequisite: [HACS](https://hacs.xyz/) is installed.

This repository is not in the official HACS default list, so add it as a custom repository first:

1. Open HACS in Home Assistant.
2. Open **Integrations**.
3. Click the three-dot menu in the top-right corner.
4. Select **Custom repositories**.
5. Add repository URL: `https://github.com/janmilinds/ha-defa-balancer`.
6. Select category: **Integration**.
7. Click **Add**.

Then install it:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=janmilinds&repository=ha-defa-balancer&category=integration)

8. Click the button above, or find **DEFA Balancer** in HACS and click **Download**.
9. Restart Home Assistant.

### Manual

1. Download the `custom_components/defa_balancer/` folder from this repository.
2. Copy it to your Home Assistant's `custom_components/` directory.
3. Restart Home Assistant.

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=defa_balancer)

Or go to **Settings** → **Devices & Services** → **Add Integration** → search for **DEFA Balancer**.

The integration scans the network for up to 15 seconds. If your Balancer is on and reachable, it will appear automatically — just confirm the device and you're done.

## Troubleshooting

If no device is found during setup, check the following:

- Balancer is powered on and connected to the network
- Home Assistant is on the same subnet/VLAN as the Balancer
- Your router or switch allows multicast traffic (check your router configuration)

## Contributing

Contributions welcome — open an issue or pull request.

### Development Setup

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/janmilinds/ha-defa-balancer?quickstart=1)

Or locally with Docker and VS Code Dev Containers. See [`docs/development/`](docs/development/) for details.

## License

MIT — see [LICENSE](LICENSE).

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/janmilinds/ha-defa-balancer.svg?style=for-the-badge
[commits]: https://github.com/janmilinds/ha-defa-balancer/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/janmilinds/ha-defa-balancer.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40janmilinds-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/janmilinds/ha-defa-balancer.svg?style=for-the-badge
[releases]: https://github.com/janmilinds/ha-defa-balancer/releases
[user_profile]: https://github.com/janmilinds
