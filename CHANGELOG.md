# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-02-03

### Added
- Initial release of Spotify Statistics integration
- Multi-user account support
- Real-time tracking sensors:
  - Currently playing track with full metadata
  - Recently played tracks (last 50)
  - Followed artists
  - Top artists and tracks (4 weeks, 6 months, all-time)
- Data export services:
  - Export followed artists to JSON
  - Export saved library to JSON
  - Export playlists to JSON
  - Export listening history to CSV
  - Export top stats snapshots to CSV
- Configurable update intervals (minimum 30s for now playing, 5min for recently played)
- Dynamic interval adjustment service
- Manual refresh service for now playing
- OAuth2 authentication with Spotify API
- HACS compatibility
- Comprehensive documentation and automation examples

### Features
- Sensor attributes include Spotify URLs for easy access
- CSV export with deduplication for append mode
- Optional audio features analysis in CSV exports
- Per-user device grouping in Home Assistant
- Automatic daily updates for top stats
- Hourly updates for followed artists

[0.1.0]: https://github.com/ianpleasance/home-assistant-spotify-stats/releases/tag/v0.1.0
