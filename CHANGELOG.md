## 1.0.0 (2025-11-14)


### Features

* initial release of Elli Charger Home Assistant integration ([f86837a](https://github.com/marcszy91/hacs-elli-charger/commit/f86837aa4c1a9708f9a1a6a72cdda632c855c8ee))

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-13

### Added
- Initial release of Elli Charger HACS integration
- authentication with Elli Account
- Station-based sensor architecture supporting multiple wallboxes
- Wallbox status sensor (Idle/Connected/Charging)
- Last session sensor with comprehensive attributes
- Session energy sensor optimized for Home Assistant Energy Dashboard
- Firmware version display in wallbox attributes
- Automatic session tracking with energy consumption
- RFID card tracking for billing
- Support for momentary power monitoring
- Lifecycle and charging state tracking

### Features
- Three sensors per charging station
- Energy consumption tracking in kWh
- Real-time power monitoring in Watts
- Session state and lifecycle tracking
- RFID card identification
- Authentication method tracking
- Firmware version monitoring
- Automatic token refresh
