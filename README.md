# Spotify Statistics Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/ianpleasance/home-assistant-spotify-stats.svg)](https://github.com/ianpleasance/home-assistant-spotify-stats/releases)
[![License](https://img.shields.io/github/license/ianpleasance/home-assistant-spotify-stats.svg)](LICENSE)

A comprehensive Home Assistant integration for tracking Spotify listening statistics, followed artists, playlists, and listening history across multiple user accounts.

## Features

- **Multi-User Support** - Track statistics for multiple Spotify accounts
- **Real-Time Tracking**
  - Currently playing track with full metadata
  - Recently played tracks (last 50)
  - Followed artists
  - Top artists and tracks (4 weeks, 6 months, all-time)
- **Data Export Services**
  - Export followed artists to JSON
  - Export saved library (albums & tracks) to JSON
  - Export playlists with full track listings to JSON
  - Export listening history to CSV with optional audio features
  - Export top stats snapshots to CSV
- **Configurable Update Intervals**
  - Customize polling frequency per user
  - Minimum 30 seconds for now playing
  - Minimum 5 minutes for recently played
- **Long-Term Analysis**
  - CSV exports for historical tracking
  - Automated backup capabilities
  - Audio feature analysis (danceability, energy, etc.)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/ianpleasance/home-assistant-spotify-stats`
6. Select category: "Integration"
7. Click "Add"
8. Find "Spotify Statistics" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub releases](https://github.com/ianpleasance/home-assistant-spotify-stats/releases)
2. Extract the `spotify_stats` folder to your `custom_components` directory
3. Restart Home Assistant

## Getting Spotify API Credentials

Before you can configure the integration, you need to create a Spotify Developer application:

1. **Go to Spotify Developer Dashboard**
   - Visit [https://developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Log in with your Spotify account

2. **Create a New App**
   - Click "Create app"
   - Fill in the form:
     - **App name**: `Home Assistant Spotify Stats` (or any name you prefer)
     - **App description**: `Integration for tracking Spotify statistics in Home Assistant`
     - **Redirect URI**: `https://your-home-assistant-url/auth/external/callback`
       - Replace `your-home-assistant-url` with your actual Home Assistant URL
       - If using Nabu Casa: `https://abcdef1234567890.ui.nabu.casa/auth/external/callback`
       - If using local URL: `http://homeassistant.local:8123/auth/external/callback`
     - Check the "Web API" checkbox
   - Accept the Terms of Service
   - Click "Save"

3. **Get Your Credentials**
   - Click on your newly created app
   - Click "Settings" in the top right
   - You'll see:
     - **Client ID** - Copy this
     - **Client Secret** - Click "View client secret" and copy this
   - Keep these credentials safe - you'll need them for configuration

4. **Note Your Spotify Username**
   - Go to your [Spotify account page](https://www.spotify.com/account/profile/)
   - Your username is shown at the top (or use your display name)

## Configuration

### Adding an Account

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Spotify Statistics**
4. Enter the required information:
   - **Username**: Your Spotify username or display name (e.g., "ian")
   - **Client ID**: From your Spotify Developer app
   - **Client Secret**: From your Spotify Developer app
   - **Now Playing Update Interval**: Seconds between updates (default: 30, min: 30)
   - **Recently Played Update Interval**: Seconds between updates (default: 300, min: 300)
5. Click **Submit**
6. You'll be redirected to Spotify to authorize the integration
7. Grant the requested permissions
8. You'll be redirected back to Home Assistant

### Adding Multiple Accounts

Repeat the configuration process for each Spotify account you want to track. Each account will have its own set of sensors and can have independent update intervals.

### Adjusting Settings

After initial configuration, you can modify update intervals:

1. Go to **Settings** → **Devices & Services**
2. Find **Spotify Statistics** for the user you want to adjust
3. Click **Configure**
4. Adjust the intervals as needed
5. Click **Submit**

## Entities Created

For each configured user (e.g., "ian"), the following sensors are created:

### Sensors

- `sensor.{username}_spotify_stats_followed_artists` - Count and list of followed artists
- `sensor.{username}_spotify_stats_recently_played` - Last 50 played tracks
- `sensor.{username}_spotify_stats_now_playing` - Currently playing track (state: playing/paused/idle)
- `sensor.{username}_spotify_stats_top_artists_4weeks` - Top 50 artists, last 4 weeks
- `sensor.{username}_spotify_stats_top_artists_6months` - Top 50 artists, last 6 months
- `sensor.{username}_spotify_stats_top_artists_alltime` - Top 50 artists, all time
- `sensor.{username}_spotify_stats_top_tracks_4weeks` - Top 50 tracks, last 4 weeks
- `sensor.{username}_spotify_stats_top_tracks_6months` - Top 50 tracks, last 6 months
- `sensor.{username}_spotify_stats_top_tracks_alltime` - Top 50 tracks, all time

All sensors include detailed metadata in their attributes.

## Services

### Export Services

#### `spotify_stats.export_followed_artists`

Export all followed artists with complete metadata to JSON.

```yaml
service: spotify_stats.export_followed_artists
data:
  username: "ian"
  filepath: "/config/www/spotify/ian_followed_artists.json"
```

#### `spotify_stats.export_saved_library`

Export saved albums and tracks with complete metadata to JSON.

```yaml
service: spotify_stats.export_saved_library
data:
  username: "ian"
  filepath: "/config/www/spotify/ian_saved_library.json"
```

#### `spotify_stats.export_playlists`

Export all playlists with full track listings to JSON.

```yaml
service: spotify_stats.export_playlists
data:
  username: "ian"
  filepath: "/config/www/spotify/ian_playlists.json"
```

#### `spotify_stats.export_recently_played_csv`

Export recently played tracks to CSV for long-term tracking.

```yaml
service: spotify_stats.export_recently_played_csv
data:
  username: "ian"
  filepath: "/config/www/spotify/ian_listening_history.csv"
  append: true  # Append to existing file (prevents duplicates)
  include_audio_features: false  # Fetch audio analysis data (slower)
```

#### `spotify_stats.export_top_stats_csv`

Export top artists or tracks snapshot to CSV.

```yaml
service: spotify_stats.export_top_stats_csv
data:
  username: "ian"
  filepath: "/config/www/spotify/stats/ian_top_artists_202502.csv"
  entity_type: "artists"  # or "tracks"
  time_range: "short_term"  # "short_term", "medium_term", or "long_term"
```

### Control Services

#### `spotify_stats.set_update_interval`

Dynamically adjust update intervals for a user.

```yaml
service: spotify_stats.set_update_interval
data:
  username: "ian"
  now_playing_interval: 60  # Optional
  recently_played_interval: 600  # Optional
```

#### `spotify_stats.refresh_now_playing`

Immediately refresh the now playing sensor.

```yaml
service: spotify_stats.refresh_now_playing
data:
  username: "ian"
```

## Automation Examples

### Daily Listening History Export

```yaml
automation:
  - alias: "Spotify: Export Daily Listening History"
    trigger:
      - platform: time
        at: "23:55:00"
    action:
      - service: spotify_stats.export_recently_played_csv
        data:
          username: "ian"
          filepath: "/config/www/spotify/ian_listening_history.csv"
          append: true
```

### Weekly Library Backup

```yaml
automation:
  - alias: "Spotify: Weekly Library Backup"
    trigger:
      - platform: time
        at: "02:00:00"
    condition:
      - condition: time
        weekday:
          - sun
    action:
      - service: spotify_stats.export_followed_artists
        data:
          username: "ian"
          filepath: "/config/www/spotify/backups/ian_followed_artists_{{ now().strftime('%Y%m%d') }}.json"
      - service: spotify_stats.export_saved_library
        data:
          username: "ian"
          filepath: "/config/www/spotify/backups/ian_library_{{ now().strftime('%Y%m%d') }}.json"
      - service: spotify_stats.export_playlists
        data:
          username: "ian"
          filepath: "/config/www/spotify/backups/ian_playlists_{{ now().strftime('%Y%m%d') }}.json"
```

### Monthly Top Stats Snapshot

```yaml
automation:
  - alias: "Spotify: Monthly Top Stats"
    trigger:
      - platform: time
        at: "03:00:00"
    condition:
      - condition: template
        value_template: "{{ now().day == 1 }}"
    action:
      - service: spotify_stats.export_top_stats_csv
        data:
          username: "ian"
          filepath: "/config/www/spotify/stats/ian_top_artists_{{ now().strftime('%Y%m') }}.csv"
          entity_type: "artists"
          time_range: "short_term"
```

### Speed Up Updates When Playing

```yaml
automation:
  - alias: "Spotify: Ian Speed Up When Playing"
    trigger:
      - platform: state
        entity_id: sensor.ian_spotify_stats_now_playing
        to: "playing"
    action:
      - service: spotify_stats.set_update_interval
        data:
          username: "ian"
          now_playing_interval: 30
  
  - alias: "Spotify: Ian Slow Down When Idle"
    trigger:
      - platform: state
        entity_id: sensor.ian_spotify_stats_now_playing
        to: "idle"
        for: "00:05:00"
    action:
      - service: spotify_stats.set_update_interval
        data:
          username: "ian"
          now_playing_interval: 120
```

## Dashboard Examples

### Simple Now Playing Card

```yaml
type: entity
entity: sensor.ian_spotify_stats_now_playing
```

### Multi-User Household View

```yaml
type: entities
title: Household Spotify Activity
entities:
  - entity: sensor.ian_spotify_stats_now_playing
    name: "Ian's Now Playing"
  - entity: sensor.sal_spotify_stats_now_playing
    name: "Sal's Now Playing"
  - entity: sensor.ian_spotify_stats_followed_artists
    name: "Ian Followed Artists"
  - entity: sensor.sal_spotify_stats_followed_artists
    name: "Sal Followed Artists"
```

### Top Artists Chart

```yaml
type: markdown
content: |
  ## Ian's Top Artists (4 Weeks)
  {% for artist in state_attr('sensor.ian_spotify_stats_top_artists_4weeks', 'artists')[:10] %}
  {{ loop.index }}. [{{ artist.name }}]({{ artist.url }})
  {% endfor %}
```

## File Structure

Exported files are stored in `/config/www/spotify/`:

```
/config/www/spotify/
├── ian_followed_artists.json
├── ian_saved_library.json
├── ian_playlists.json
├── ian_listening_history.csv
├── sal_followed_artists.json
├── sal_saved_library.json
└── backups/
    ├── ian_followed_artists_20250203.json
    └── ian_library_20250203.json
```

These files are accessible via:
- `http://your-home-assistant:8123/local/spotify/ian_listening_history.csv`

## Troubleshooting

### "Invalid Redirect URI" Error

Make sure your redirect URI in the Spotify Developer Dashboard exactly matches your Home Assistant URL. Common formats:
- Nabu Casa: `https://abcdef1234567890.ui.nabu.casa/auth/external/callback`
- Local: `http://homeassistant.local:8123/auth/external/callback`
- Custom domain: `https://yourdomain.com/auth/external/callback`

### Sensors Not Updating

1. Check your update intervals in integration configuration
2. Verify you've authorized the integration in Spotify
3. Check Home Assistant logs for API rate limit messages
4. Try manually refreshing with `spotify_stats.refresh_now_playing`

### Export Files Not Appearing

1. Ensure the `/config/www/spotify/` directory exists
2. Check file permissions
3. Review Home Assistant logs for write errors
4. Verify the filepath in your automation/service call

## Permissions Required

The integration requires the following Spotify API scopes:
- `user-read-currently-playing` - Read currently playing track
- `user-read-recently-played` - Read recently played tracks
- `user-top-read` - Read top artists and tracks
- `user-follow-read` - Read followed artists
- `user-library-read` - Read saved albums and tracks
- `playlist-read-private` - Read private playlists
- `playlist-read-collaborative` - Read collaborative playlists

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/ianpleasance/home-assistant-spotify-stats/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ianpleasance/home-assistant-spotify-stats/discussions)

## Credits

Created by Ian Pleasance ([@ianpleasance](https://github.com/ianpleasance))

Built for the Home Assistant community.
