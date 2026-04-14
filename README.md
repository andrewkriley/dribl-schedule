# Dribl Fixtures — Home Assistant Integration

> **⚠️ Disclaimer:** This is an **unofficial, experimental** Home Assistant integration and is not affiliated with, endorsed by, or supported by Dribl in any way. It is provided as a best-effort community tool.
>
> **Please ensure you cross-check your game times and locations directly with your club or association before travelling to any fixture.**

---

A custom Home Assistant integration that surfaces football fixture data from the [Dribl Match Centre](https://dribl.com) platform as HA sensors — with a fully guided setup so you never need to find or construct an API URL yourself.

## Features

- 4-step UI setup wizard: association → club → competition → team
- Sensor state = next fixture date/time
- Attributes include: round, home/away team, ground, field, score, full fixture list
- Auto-refreshes every 60 minutes
- Add as many teams as you like (one sensor per team)

## Installation

1. Copy the `custom_components/dribl/` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration** and search for **Dribl Fixtures**
4. Follow the 4-step wizard:

| Step | What to enter | Where to find it |
|---|---|---|
| Association | e.g. `nwsf` | The subdomain from your fixtures URL: **nwsf**.dribl.com |
| Club | Pick from dropdown | Your club name |
| Competition | Pick from dropdown | e.g. Premiership |
| Team | Pick from dropdown | Your age group / division |

Repeat for each team you want to track.

## Sensor Output

Each team creates a sensor (e.g. `sensor.north_ryde_sc_over_35s`) with:

- **State:** Next fixture datetime (ISO 8601, UTC)
- **Attributes:** `round`, `home_team`, `away_team`, `ground`, `field`, `competition`, `league`, `status`, `home_score`, `away_score`, `all_fixtures`

## Automations (example)

Notify 2 hours before kickoff:

```yaml
automation:
  - alias: "Kickoff reminder"
    trigger:
      - platform: template
        value_template: >
          {% set kickoff = state_attr('sensor.my_team', 'date') | as_datetime %}
          {{ (kickoff - now()).total_seconds() < 7200 and
             (kickoff - now()).total_seconds() > 7140 }}
    action:
      - service: notify.mobile_app
        data:
          message: "Kickoff in 2 hours — {{ state_attr('sensor.my_team', 'home_team') }} vs {{ state_attr('sensor.my_team', 'away_team') }} at {{ state_attr('sensor.my_team', 'ground') }}"
```

## Disclaimer

This integration uses the public Dribl Match Centre API on a best-effort basis. Fixture data may be delayed or incorrect. Always verify game times and locations with your club or association.

This project is not affiliated with, endorsed by, or supported by Dribl.
