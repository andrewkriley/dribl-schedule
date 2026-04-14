# Dribl Fixtures — Home Assistant Integration

> **⚠️ Disclaimer:** This is an **unofficial, experimental** Home Assistant integration and is not affiliated with, endorsed by, or supported by Dribl in any way. It is provided as a best-effort community tool.
>
> **Please ensure you cross-check your game times and locations directly with your club or association before travelling to any fixture.**

---

## Overview

This integration polls the public Dribl Match Centre API to surface football fixture data as Home Assistant sensors. Each configured team becomes a sensor whose state is the next upcoming fixture datetime, with full fixture details available as attributes.

---

## API URL Structure

The Dribl Match Centre API follows this pattern:

```
https://mc-api.dribl.com/api/fixtures
  ?date_range=default       # 'default' = upcoming only; 'all' = full season
  &season=<season_id>
  &competition=<competition_id>
  &club=<club_id>
  &league=<league_id>
  &tenant=<tenant_id>       # The association (resolved from the subdomain slug)
  &timezone=Australia%2FSydney
```

### Key Discovery Endpoints

| Purpose | Endpoint |
|---|---|
| Resolve tenant from subdomain | `GET /api/tenants?mc_link={slug}.dribl.com&slug={slug}` |
| List clubs for an association | `GET /api/list/clubs?disable_paging=true&tenant={tenant_id}` |
| List seasons | `GET /api/list/seasons?disable_paging=true&tenant={tenant_id}` |
| List competitions for a season | `GET /api/list/competitions?disable_paging=true&tenant={tenant_id}&season={season_id}` |
| List leagues (teams) for a competition | `GET /api/list/leagues?disable_paging=true&tenant={tenant_id}&competition={competition_id}&sort=+name` |
| Fetch fixtures | `GET /api/fixtures?...` (see above) |

The integration's config flow walks through these endpoints automatically — the user never needs to construct a URL manually.

---

## Notes

- All fixture times are returned by the API in UTC and should be interpreted in your local timezone.
- `date_range=default` returns upcoming fixtures only. The integration uses this by default.
- Each Dribl association has its own tenant ID, resolved automatically from the subdomain (e.g. `nwsf` → `nwsf.dribl.com`).
- This integration is read-only and does not write any data back to Dribl.
