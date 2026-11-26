---
id: 20261126-power-sensors-stay-estimates
status: accepted
rule: .agents/instructions/defa_balancer.sensor.instructions.md
---

# Keep the power sensors as watt estimates calculated from current

## Context

The DEFA Balancer is a current meter: its packets carry the current of each phase, and nothing about voltage or power
factor. The L1–L3 and Total Power sensors multiply that current by the configured phase voltage, so what they show is
apparent power at an assumed voltage, while they are labelled as active power (`SensorDeviceClass.POWER`, W). With
reactive loads on the main fuses the reading runs above the active power a meter would show.

## Decision

Keep the power sensors as they are — device class `power`, unit W, current × phase voltage — and accept the error. The
documentation says plainly that the values are apparent power estimates and explains the difference.

The integration gets a little more out of a unit that exists for EV charger load management; it does not try to be an
energy meter. Users who need active power have devices built to measure it.

## Considered options

- **Relabel as apparent power (`APPARENT_POWER`, VA) in 2.0.0.** Correct on paper, but every user pays for it: the
  long-term statistics break, the Integral helper no longer feeds the Energy dashboard, and anything filtering on
  `device_class: power` loses the sensors. The number itself would be no more accurate.
- **Add VA sensors beside the W ones.** Four more entities carrying the same number.
- **Estimate active power with an assumed power factor.** The power factor changes with the load, so a fixed one only
  moves the error around.

## Consequences

- The documentation, not the sensors, carries the accuracy statement: `README.md` and `docs/user/CONFIGURATION.md`.
- Revisit only if the packet turns out to carry voltage or power factor; a new record then supersedes this one.
