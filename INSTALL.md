# Installation Guide

This guide will walk you through installing and configuring the Spotify Statistics integration for Home Assistant.

## Prerequisites

Before you begin, ensure you have:
- Home Assistant 2024.1.0 or newer
- A Spotify account
- Access to the Home Assistant configuration directory

## Step 1: Get Spotify API Credentials

1. **Visit the Spotify Developer Dashboard**
   - Go to: https://developer.spotify.com/dashboard
   - Log in with your Spotify account

2. **Create a New Application**
   - Click the "Create app" button
   - Fill in the application details:
     ```
     App name: Home Assistant Spotify Stats
     App description: Integration for tracking Spotify statistics
     Website: https://github.com/ianpleasance/home-assistant-spotify-stats
     Redirect URI: https://YOUR-HOME-ASSISTANT-URL/auth/external/callback
     ```
   - **Important**: Replace `YOUR-HOME-ASSISTANT-URL` with your actual Home Assistant URL:
     - Nabu Casa: `https://abcdefg123456.ui.nabu.casa`
     - Local: `http://homeassistant.local:8123`
     - Custom domain: `https://yourdomain.com`
   - Check "Web API" under "Which API/SDKs are you planning to use?"
   - Accept the Terms of Service
   - Click "Save"

3. **Get Your Credentials**
   - Click on your newly created app
   - Click "Settings" in the top right
   - Copy your **Client ID**
   - Click "View client secret" and copy your **Client Secret**
   - **Keep these safe** - you'll need them shortly

## Step 2: Install the Integration

### Option A: HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three-dot menu in the top right
4. Select "Custom repositories"
5. Add the repository:
   - **URL**: `https://github.com/ianpleasance/home-assistant-spotify-stats`
   - **Category**: Integration
6. Click "Add"
7. Click "Explore & Download Repositories"
8. Search for "Spotify Statistics"
9. Click "Download"
10. Restart Home Assistant

### Option B: Manual Installation

1. Download the latest release from:
   https://github.com/ianpleasance/home-assistant-spotify-stats/releases

2. Extract the ZIP file

3. Copy the `spotify_stats` folder to your Home Assistant's `custom_components` directory:
   ```
   /config/custom_components/spotify_stats/
   ```

4. Your directory structure should look like:
   ```
   config/
   ├── custom_components/
   │   └── spotify_stats/
   │       ├── __init__.py
   │       ├── manifest.json
   │       ├── sensor.py
   │       ├── services.py
   │       └── ...
   ```

5. Restart Home Assistant

## Step 3: Configure the Integration

1. **Navigate to Integrations**
   - Go to: Settings → Devices & Services
   - Click "Add Integration"

2. **Search for Spotify Statistics**
   - Type "Spotify Statistics" in the search box
   - Click on it when it appears

3. **Enter Configuration Details**
   - **Username**: Your Spotify username or display name (e.g., "ian")
     - Find this at: https://www.spotify.com/account/profile/
   - **Client ID**: Paste the Client ID from Step 1
   - **Client Secret**: Paste the Client Secret from Step 1
   - **Now Playing Interval**: Leave default (30 seconds) or customize
   - **Recently Played Interval**: Leave default (300 seconds) or customize
   - Click "Submit"

4. **Authorize with Spotify**
   - You'll be redirected to Spotify's authorization page
   - Review the permissions requested:
     - Read currently playing track
     - Read recently played tracks
     - Read top artists and tracks
     - Read followed artists
     - Read saved albums and tracks
     - Read playlists
   - Click "Agree" to authorize
   - You'll be redirected back to Home Assistant

5. **Configuration Complete!**
   - You should see a success message
   - The integration will appear in your devices list as "Spotify (username)"

## Step 4: Verify Installation

1. **Check for Sensors**
   - Go to: Developer Tools → States
   - Search for sensors starting with `sensor.{username}_spotify_stats_`
   - You should see 9 sensors:
     ```
     sensor.{username}_spotify_stats_now_playing
     sensor.{username}_spotify_stats_recently_played
     sensor.{username}_spotify_stats_followed_artists
     sensor.{username}_spotify_stats_top_artists_4weeks
     sensor.{username}_spotify_stats_top_artists_6months
     sensor.{username}_spotify_stats_top_artists_alltime
     sensor.{username}_spotify_stats_top_tracks_4weeks
     sensor.{username}_spotify_stats_top_tracks_6months
     sensor.{username}_spotify_stats_top_tracks_alltime
     ```

2. **Test a Sensor**
   - Go to: Developer Tools → States
   - Click on `sensor.{username}_spotify_stats_now_playing`
   - You should see the current state (playing/paused/idle)
   - Click "Attributes" to see detailed information

3. **Check Services**
   - Go to: Developer Tools → Services
   - Search for "spotify_stats"
   - You should see 7 services available

## Step 5: Add Multiple Users (Optional)

To track multiple Spotify accounts:

1. Repeat Step 3 with different credentials
2. Use a different username for each account
3. Each account can have independent update intervals

## Step 6: Create Export Directory

Create a directory for exported files:

1. Navigate to your Home Assistant's `www` directory
2. Create a folder: `/config/www/spotify/`
3. Optionally create subdirectories:
   ```
   /config/www/spotify/
   ├── backups/
   └── stats/
   ```

This is where your exports will be saved and accessible at:
`http://YOUR-HOME-ASSISTANT:8123/local/spotify/`

## Step 7: Set Up Automations (Optional)

Check out the example automations in `examples/automations.yaml` for:
- Daily listening history exports
- Weekly backups
- Monthly statistics snapshots
- Dynamic update intervals
- And more!

## Troubleshooting

### "Invalid Redirect URI" Error

**Problem**: Getting an error about redirect URI during authorization

**Solution**: 
1. Go back to your Spotify Developer app settings
2. Make sure your Redirect URI exactly matches your Home Assistant URL
3. Common formats:
   - `https://abc123.ui.nabu.casa/auth/external/callback` (Nabu Casa)
   - `http://homeassistant.local:8123/auth/external/callback` (Local)
   - `https://yourdomain.com/auth/external/callback` (Custom domain)
4. Save the settings
5. Try configuration again

### Sensors Not Updating

**Problem**: Sensors show "unavailable" or old data

**Solution**:
1. Check Home Assistant logs for errors
2. Try manually refreshing:
   ```yaml
   service: spotify_stats.refresh_now_playing
   data:
     username: "your_username"
   ```
3. Verify your Spotify account is actively playing music
4. Check your update intervals aren't too long

### Authentication Errors

**Problem**: "Invalid authentication" or "Token expired"

**Solution**:
1. Remove the integration: Settings → Devices & Services → Spotify Statistics → Delete
2. Delete the cache file: `/config/.spotify_cache_{username}`
3. Reconfigure the integration from Step 3

### No Data in Sensors

**Problem**: Sensors exist but show 0 or no data

**Solution**:
1. Make sure you're actively using Spotify
2. Top stats require at least a few weeks of listening history
3. Recently played requires active listening in the last few hours
4. Wait for the next update cycle (check update intervals)

### Export Services Not Working

**Problem**: Export services don't create files

**Solution**:
1. Verify the directory exists: `/config/www/spotify/`
2. Check file permissions on the directory
3. Review Home Assistant logs for write errors
4. Try a different filepath in the service call

## Getting Help

If you encounter issues:

1. **Check the Logs**
   - Go to: Settings → System → Logs
   - Look for entries mentioning "spotify_stats"

2. **Search Existing Issues**
   - Visit: https://github.com/ianpleasance/home-assistant-spotify-stats/issues

3. **Report a Bug**
   - Include:
     - Home Assistant version
     - Integration version
     - Error messages from logs
     - Steps to reproduce

4. **Ask for Help**
   - GitHub Discussions: https://github.com/ianpleasance/home-assistant-spotify-stats/discussions
   - Home Assistant Community: https://community.home-assistant.io/

## Next Steps

- Check out [README.md](README.md) for feature documentation
- Review example automations in [examples/automations.yaml](examples/automations.yaml)
- Explore dashboard examples in [examples/dashboard.yaml](examples/dashboard.yaml)
- Set up automated exports and backups

Enjoy tracking your Spotify statistics! 🎵
