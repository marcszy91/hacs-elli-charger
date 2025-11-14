# Elli Charger Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/marcszy91/hacs-elli-charger.svg)](https://github.com/marcszy91/hacs-elli-charger/releases)

Home Assistant integration for Elli charging stations (wallboxes). Monitor your charging sessions and station status directly in Home Assistant.

## Features

- Real-time charging session monitoring
- Energy consumption tracking (kWh)
- Current charging power (Watts)
- Station status and information
- Automatic token refresh
- Easy configuration through UI

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add the repository URL: `https://github.com/marcszy91/hacs-elli-charger`
6. Select category: "Integration"
7. Click "Add"
8. Find "Elli Charger" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/marcszy91/hacs-elli-charger/releases)
2. Extract the files to your `custom_components` directory:
   ```
   custom_components/elli_charger/
   ```
3. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Elli Charger"
4. Enter your Elli account credentials:
   - Email
   - Password

## Sensors

The integration provides the following sensors:

### Station Sensor
- **Name**: `Elli [Station Name]`
- **State**: Connected/Idle
- **Attributes**:
  - Station ID
  - Name
  - Serial Number
  - Model
  - Firmware Version

### Current Session Energy
- **Name**: `Elli Current Session Energy`
- **Unit**: kWh
- **Device Class**: Energy
- **Attributes**:
  - Session ID
  - Station ID
  - Start Time
  - End Time (if completed)
  - Status

### Current Session Power
- **Name**: `Elli Current Session Power`
- **Unit**: W
- **Device Class**: Power
- **Attributes**:
  - Session ID
  - Station ID
  - Status

## Usage Examples

### Automation: Notify when charging complete

```yaml
automation:
  - alias: "Notify when EV charging complete"
    trigger:
      - platform: numeric_state
        entity_id: sensor.elli_current_session_power
        below: 100
        for:
          minutes: 5
    condition:
      - condition: numeric_state
        entity_id: sensor.elli_current_session_energy
        above: 5
    action:
      - service: notify.mobile_app
        data:
          message: "EV charging complete! {{ states('sensor.elli_current_session_energy') }} kWh charged"
```

### Energy Dashboard

Add the energy sensor to your Home Assistant Energy Dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Under "Electricity grid" → "Add consumption"
3. Select `sensor.elli_current_session_energy`

## API Client

This integration uses the [elli-client](https://pypi.org/project/elli-client/) Python package for communication with the Elli API.

## Support

- [Report Issues](https://github.com/marcszy91/hacs-elli-charger/issues)
- [Feature Requests](https://github.com/marcszy91/hacs-elli-charger/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Disclaimer

This integration is not officially supported by Elli or Volkswagen Group Charging GmbH. Use at your own risk.
