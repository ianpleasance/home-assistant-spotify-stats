# Entity Naming Reference

## Domain vs Entity Naming

- **Integration Domain**: `spotify_stats`
- **Entity ID Prefix**: `sensor.{username}_spotify_stats_*`
- **Device Name**: `Spotify Stats ({username})`

This prevents any clash with the official Home Assistant Spotify integration (domain: `spotify`).

## Entity IDs Created Per User

For a user with username "ian", the following entities are created:

### Sensors (9 total)

1. `sensor.ian_spotify_stats_now_playing`
   - Currently playing track
   - State: "playing", "paused", or "idle"

2. `sensor.ian_spotify_stats_recently_played`
   - Last 50 played tracks
   - State: timestamp of most recent track

3. `sensor.ian_spotify_stats_followed_artists`
   - Followed artists count
   - State: number of followed artists

4. `sensor.ian_spotify_stats_top_artists_4weeks`
   - Top 50 artists (last 4 weeks)
   - State: count

5. `sensor.ian_spotify_stats_top_artists_6months`
   - Top 50 artists (last 6 months)
   - State: count

6. `sensor.ian_spotify_stats_top_artists_alltime`
   - Top 50 artists (all time)
   - State: count

7. `sensor.ian_spotify_stats_top_tracks_4weeks`
   - Top 50 tracks (last 4 weeks)
   - State: count

8. `sensor.ian_spotify_stats_top_tracks_6months`
   - Top 50 tracks (last 6 months)
   - State: count

9. `sensor.ian_spotify_stats_top_tracks_alltime`
   - Top 50 tracks (all time)
   - State: count

## Services

All services are under the `spotify_stats` domain:

1. `spotify_stats.export_followed_artists`
2. `spotify_stats.export_saved_library`
3. `spotify_stats.export_playlists`
4. `spotify_stats.export_recently_played_csv`
5. `spotify_stats.export_top_stats_csv`
6. `spotify_stats.set_update_interval`
7. `spotify_stats.refresh_now_playing`

## Device Grouping

All sensors for a user are grouped under a device:
- **Device Name**: `Spotify Stats (ian)`
- **Manufacturer**: Spotify
- **Model**: Account

## Example Multi-User Setup

### User: ian
- Device: `Spotify Stats (ian)`
- Sensors: `sensor.ian_spotify_stats_*`

### User: sal
- Device: `Spotify Stats (sal)`
- Sensors: `sensor.sal_spotify_stats_*`

## No Conflicts

This naming scheme ensures:
- ✅ No conflict with official Spotify integration (`media_player.spotify_*`)
- ✅ Clear identification of statistics-specific sensors
- ✅ Easy multi-user support
- ✅ Readable entity IDs
- ✅ Proper device grouping
