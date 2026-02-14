# Spotify Statistics for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub release](https://img.shields.io/github/release/ianpleasance/home-assistant-spotify-stats.svg)](https://github.com/ianpleasance/home-assistant-spotify-stats/releases)

A comprehensive Home Assistant custom integration that tracks detailed Spotify listening statistics, including now playing, recently played tracks, top artists and tracks across multiple time ranges, followed artists, playlists, and saved library.

## Features

### 📊 Rich Statistics Tracking

- **Now Playing**: Real-time tracking of currently playing tracks
- **Recently Played**: Last 50 tracks with timestamps
- **Top Artists & Tracks**: Rankings across 3 time periods (4 weeks, 6 months, all-time)
- **Followed Artists**: Complete list of artists you follow
- **Playlists**: All your playlists with track counts and metadata
- **Saved Library**: Your liked songs and saved albums

### 🔄 Flexible Update Intervals

- Configurable polling for now playing (30-300 seconds)
- Configurable polling for recently played (300-3600 seconds)
- Automatic daily updates for top stats and followed artists
- Live updates for playlists and saved library

### 📁 Data Export Services

Seven export services to backup and analyze your data:

- **Export Recently Played**: CSV export with optional audio features
- **Export Top Stats**: Export top artists or tracks to CSV
- **Export Followed Artists**: Complete list with genres and popularity
- **Export Playlists**: Full playlist metadata including tracks
- **Export Saved Library**: All saved tracks and albums
- **Refresh Now Playing**: Force immediate update
- **Set Update Intervals**: Dynamically adjust polling rates

### 🎵 Multi-User Support

Track statistics for multiple Spotify accounts independently with separate configurations per user.

## Sensors

The integration creates 12 sensors per configured user:

| Sensor | Description | State | Attributes |
|--------|-------------|-------|------------|
| `now_playing` | Currently playing track | playing/paused/idle | Track details, artist, album, progress, etc. |
| `recently_played` | Recent listening history | Last played timestamp | 50 most recent tracks with timestamps |
| `followed_artists` | Artists you follow | Total count | First 20 artists with genres, popularity |
| `top_artists_4weeks` | Top artists (4 weeks) | Count | Top 50 artists ranked by listening |
| `top_artists_6months` | Top artists (6 months) | Count | Top 50 artists ranked by listening |
| `top_artists_alltime` | Top artists (all time) | Count | Top 50 artists ranked by listening |
| `top_tracks_4weeks` | Top tracks (4 weeks) | Count | Top 50 tracks ranked by listening |
| `top_tracks_6months` | Top tracks (6 months) | Count | Top 50 tracks ranked by listening |
| `top_tracks_alltime` | Top tracks (all time) | Count | Top 50 tracks ranked by listening |
| `playlists` | Your playlists | Total count | First 20 playlists with metadata |
| `saved_tracks` | Liked songs | Total count | First 20 recently added tracks |
| `saved_albums` | Saved albums | Total count | First 20 recently added albums |

**Note**: Due to Home Assistant's 16KB attribute size limit, playlist and library sensors show only the first 20 items in attributes, but export services provide complete data.

## Installation

### Prerequisites

1. **Spotify Developer Account**: Create an app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. **Spotify Premium**: Required for now playing functionality
3. **Home Assistant Spotify Integration**: Must be installed and configured first

### HACS Installation (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL: `https://github.com/ianpleasance/home-assistant-spotify-stats`
5. Select category: "Integration"
6. Click "Add"
7. Click "Install" on the Spotify Statistics card
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/spotify_stats` directory to your Home Assistant `config/custom_components` directory
2. Restart Home Assistant

## Configuration

### Step 1: Configure Spotify Integration

First, ensure the official Spotify integration is set up:

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for and add **Spotify**
3. Follow the OAuth flow to authorize

### Step 2: Add Spotify Statistics

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Spotify Statistics**
3. Enter your **Spotify username** (e.g., `planetbuilders`)
4. Set update intervals:
   - **Now Playing Interval**: 30-300 seconds (default: 30)
   - **Recently Played Interval**: 300-3600 seconds (default: 300)
5. Click **Submit**
6. You'll be redirected to Spotify to authorize (reuses credentials from official integration)
7. Click **Agree** on Spotify
8. Done! Sensors will appear within seconds

### Spotify Developer App Setup

Your Spotify app needs this redirect URI configured:

```
https://your-home-assistant-url/auth/external/callback
```

Or if using Nabu Casa:

```
https://my.home-assistant.io/redirect/oauth
```

## Services

### `spotify_stats.export_recently_played_csv`

Export recently played tracks to CSV with optional audio features.

```yaml
service: spotify_stats.export_recently_played_csv
data:
  username: planetbuilders
  filepath: /config/www/recently_played.csv
  append: false
  include_audio_features: true
```

**Parameters**:
- `username` (required): Spotify username
- `filepath` (required): Path to save CSV file
- `append` (optional): Append to existing file (default: false)
- `include_audio_features` (optional): Include danceability, energy, tempo, etc. (default: false)

### `spotify_stats.export_top_stats_csv`

Export top artists or tracks to CSV.

```yaml
service: spotify_stats.export_top_stats_csv
data:
  username: planetbuilders
  filepath: /config/www/top_artists.csv
  entity_type: artists
  time_range: medium_term
```

**Parameters**:
- `username` (required): Spotify username
- `filepath` (required): Path to save CSV file
- `entity_type` (required): `artists` or `tracks`
- `time_range` (required): `short_term` (4 weeks), `medium_term` (6 months), or `long_term` (all time)

### `spotify_stats.export_followed_artists`

Export complete list of followed artists to JSON.

```yaml
service: spotify_stats.export_followed_artists
data:
  username: planetbuilders
  filepath: /config/www/followed_artists.json
```

### `spotify_stats.export_playlists`

Export all playlists with full metadata to JSON.

```yaml
service: spotify_stats.export_playlists
data:
  username: planetbuilders
  filepath: /config/www/playlists.json
```

**Note**: Skips deleted/inaccessible playlists with a warning in logs.

### `spotify_stats.export_saved_library`

Export saved tracks and albums to JSON.

```yaml
service: spotify_stats.export_saved_library
data:
  username: planetbuilders
  filepath: /config/www/saved_library.json
```

### `spotify_stats.set_update_intervals`

Dynamically change polling intervals without restarting.

```yaml
service: spotify_stats.set_update_intervals
data:
  username: planetbuilders
  now_playing_interval: 60
  recently_played_interval: 600
```

### `spotify_stats.refresh_now_playing`

Force immediate refresh of now playing sensor.

```yaml
service: spotify_stats.refresh_now_playing
data:
  username: planetbuilders
```

## Dashboard Example

A complete 8-view dashboard is available in the repository showcasing:

- Now Playing & Recently Played
- Top Artists & Tracks (4 weeks, 6 months, all time)
- Followed Artists  
- Playlists
- Saved Tracks & Albums

## Automation Examples

### Daily Listening History Backup

```yaml
automation:
  - alias: "Backup Spotify History Daily"
    trigger:
      - platform: time
        at: "23:59:00"
    action:
      - service: spotify_stats.export_recently_played_csv
        data:
          username: planetbuilders
          filepath: "/config/backups/spotify_{{ now().strftime('%Y%m%d') }}.csv"
          append: false
          include_audio_features: true
```

### Weekly Top Artists Report

```yaml
automation:
  - alias: "Weekly Top Artists Export"
    trigger:
      - platform: time
        at: "09:00:00"
      - platform: time_pattern
        days: "/7"
    action:
      - service: spotify_stats.export_top_stats_csv
        data:
          username: planetbuilders
          filepath: "/config/reports/artists_{{ now().strftime('%Y%m%d') }}.csv"
          entity_type: artists
          time_range: short_term
```

## Troubleshooting

### "Implementation not available" error

**Solution**: The official Spotify integration must be configured first. The Spotify Statistics integration shares OAuth credentials with it.

### 401 Unauthorized errors

**Causes**:
- Spotify Premium required for now playing functionality
- Token expired (automatic refresh should handle this)
- Redirect URI mismatch in Spotify Developer Dashboard

**Solution**: Verify redirect URI matches your Home Assistant URL exactly.

### Database size warnings

The integration limits sensor attributes to 20 items each to stay under Home Assistant's 16KB attribute limit. Use export services to access complete data.

### Export playlists fails with 404

Some playlists may be deleted or made private. The service skips these with a warning and exports remaining playlists successfully.

## Data Privacy

- All data stays local in Home Assistant
- OAuth tokens stored securely in Home Assistant's credential storage
- Export files saved to paths you specify
- No data sent to third parties (except Spotify API calls)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/ianpleasance/home-assistant-spotify-stats/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ianpleasance/home-assistant-spotify-stats/discussions)

## Credits

Created by [Ian Pleasance](https://github.com/ianpleasance)

Uses the [spotipy](https://github.com/spotipy-dev/spotipy) library for Spotify API access.

## License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.

## Changelog

### v0.1.0 (2026-02-13)

Initial release with:
- 12 sensors per user (now playing, recently played, top stats, followed artists, playlists, saved library)
- 7 export services
- Multi-user support
- Shared OAuth with official Spotify integration
- Configurable polling intervals
- Example dashboard and automations
