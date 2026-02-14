# Spotify Statistics

Track comprehensive Spotify listening statistics in Home Assistant.

## What This Integration Does

Spotify Statistics provides detailed insights into your Spotify listening habits with 12 sensors per user:

- **Now Playing** - Real-time track information
- **Recently Played** - Last 50 tracks with timestamps
- **Top Artists** - Across 3 time periods (4 weeks, 6 months, all-time)
- **Top Tracks** - Across 3 time periods (4 weeks, 6 months, all-time)
- **Followed Artists** - Complete list of artists you follow
- **Playlists** - All your playlists with metadata
- **Saved Tracks** - Your liked songs library
- **Saved Albums** - Your saved albums collection

## Key Features

✅ **Multi-User Support** - Track stats for multiple Spotify accounts  
✅ **Configurable Polling** - Adjust update intervals (30s-1hr)  
✅ **Rich Attributes** - Each sensor includes detailed metadata  
✅ **7 Export Services** - Backup data to CSV/JSON files  
✅ **Shared OAuth** - Uses official Spotify integration credentials  
✅ **Dashboard Ready** - Example 8-view dashboard included

## Export Services

- `export_recently_played_csv` - Export listening history with audio features
- `export_top_stats_csv` - Export top artists/tracks rankings
- `export_followed_artists` - Backup followed artists list
- `export_playlists` - Export all playlists with tracks
- `export_saved_library` - Backup liked songs and albums
- `set_update_intervals` - Change polling rates dynamically
- `refresh_now_playing` - Force immediate update

## Requirements

- **Spotify Premium** (required for now playing sensor)
- **Official Spotify Integration** (must be configured first)
- **Spotify Developer App** (create at developer.spotify.com)

## Quick Start

1. Configure the official **Spotify** integration first
2. Add **Spotify Statistics** integration
3. Enter your Spotify username
4. Authorize through Spotify OAuth
5. Sensors appear immediately!

## Example Uses

- Daily listening history backups
- Year-end listening reports (like Spotify Wrapped)
- Track music taste evolution over time
- Share top artists/tracks on social media
- Automate playlist creation based on top tracks
- Monitor when specific artists are played

## Documentation

Full documentation including:
- Detailed sensor descriptions
- Service call examples
- Dashboard configuration
- Automation examples
- Troubleshooting guide

Available at: [GitHub Repository](https://github.com/ianpleasance/home-assistant-spotify-stats)

## Support

- [Report Issues](https://github.com/ianpleasance/home-assistant-spotify-stats/issues)
- [Discussions](https://github.com/ianpleasance/home-assistant-spotify-stats/discussions)
