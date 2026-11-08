# Islamic Prayers - Home Assistant Integration

A HACS-compatible Home Assistant custom integration that provides Islamic prayer time sensors with support for multiple global calculation methods.

## Features

- **6 Prayer Sensors**: Tark-e-Seher, Fajr, Zuhr, Asr, Maghrib, Isha
- **Next Prayer Sensor**: Shows the upcoming prayer with countdown timer
- **Multiple Calculation Methods**: MWL, ISNA, Egyptian, Karachi, Umm Al-Qura, Dubai, Qatar, Kuwait, Moon Sighting Committee, Singapore, UOIF
- **Live Per-Prayer Adjustments**: Offset each prayer time by +/- minutes with sliders that apply instantly
- **Interactive Map**: Set your location via map picker during setup and reconfiguration
- **Next Prayer Toggles**: Enable/disable individual prayers from the Next Prayer sensor

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → Custom repositories
3. Add `https://github.com/deCodeIt/islamic-prayer-ha` as an Integration
4. Search for "Islamic Prayers" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/islamic_prayer/` to your HA `custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Islamic Prayers"
3. **Step 1**: Select your location on the map
4. **Step 2**: Choose your calculation method
5. **Step 3**: Set per-prayer time offsets and Next Prayer toggles

After setup, the offsets remain available as live sliders (see below) and in
the integration's **Configure** dialog.

## Sensors

| Sensor | State | Attributes |
|--------|-------|------------|
| Tark-e-Seher | HH:MM | adjustment_minutes, calculation_method, lat/lon |
| Fajr | HH:MM | adjustment_minutes, calculation_method, lat/lon |
| Zuhr | HH:MM | adjustment_minutes, calculation_method, lat/lon |
| Asr | HH:MM | adjustment_minutes, calculation_method, lat/lon |
| Maghrib | HH:MM | adjustment_minutes, calculation_method, lat/lon |
| Isha | HH:MM | adjustment_minutes, calculation_method, lat/lon |
| Next Prayer | Prayer name | time, countdown, remaining_seconds, enabled_prayers |

## Adjusting Prayer Times

Every prayer exposes a **live offset slider** on the integration's device
page, for example `number.islamic_prayers_fajr_offset`:

| Entity | Range | Step |
|--------|-------|------|
| `number.<prayer>_offset` | -30 to +30 minutes | 1 minute |

Dragging the slider — or calling `number.set_value` — recalculates all prayer
times immediately. No reload, restart or options flow is needed, and the value
is stored in the config entry so it survives restarts.

Slider visibility follows the same per-prayer setting as the Next Prayer sensor:
when a prayer is excluded from Next Prayer (the existing `next_prayer_*`
toggles), its offset slider is **hidden** in the UI, and it reappears as soon
as the prayer is enabled again. Tark-e-Seher has no Next Prayer toggle, so its
slider is always visible.

Arrival events are only raised for prayers that are actually reached:

- Times that are already in the past are never announced. If an offset moves a
  prayer behind the current time, it is silently treated as passed.
- A prayer that was already announced never fires again, even if an offset
  moves its time back into the future.
- Arrivals detected more than 5 minutes late (for example after Home Assistant
  was suspended) are treated as passed instead of raising an event.

## Calculation Methods

### Sunni Methods
- **Muslim World League (MWL)** - Default for most regions
- **ISNA (North America)** - Islamic Society of North America
- **Egyptian** - Egyptian General Authority of Survey
- **Karachi** - University of Islamic Sciences, Karachi
- **Umm Al-Qura** - Umm Al-Qura University, Makkah
- **Dubai** - Dubai method
- **Qatar** - Qatar method
- **Kuwait** - Kuwait method
- **Moon Sighting Committee** - Moonsighting.com
- **Singapore** - Singapore method
- **UOIF (France)** - Union des Organisations Islamiques de France
- **KEMENAG** - Indonesia

### Shia Methods
- **Tehran** - Institute of Geophysics, University of Tehran
- **Jafari** - Shia Ithna-Ashari, Leva Institute, Qum

## License

MIT
