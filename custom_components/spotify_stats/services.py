"""Services for Spotify Statistics integration."""
from __future__ import annotations

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_APPEND,
    ATTR_ENTITY_TYPE,
    ATTR_FILEPATH,
    ATTR_INCLUDE_AUDIO_FEATURES,
    ATTR_TIME_RANGE,
    ATTR_USERNAME,
    CONF_NOW_PLAYING_INTERVAL,
    CONF_RECENTLY_PLAYED_INTERVAL,
    DOMAIN,
    SERVICE_EXPORT_FOLLOWED_ARTISTS,
    SERVICE_EXPORT_PLAYLISTS,
    SERVICE_EXPORT_RECENTLY_PLAYED_CSV,
    SERVICE_EXPORT_SAVED_LIBRARY,
    SERVICE_EXPORT_TOP_STATS_CSV,
    SERVICE_REFRESH_NOW_PLAYING,
    SERVICE_SET_UPDATE_INTERVAL,
    TIME_RANGE_LONG,
    TIME_RANGE_MEDIUM,
    TIME_RANGE_SHORT,
)
from .coordinator import SpotifyStatsCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
EXPORT_FOLLOWED_ARTISTS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_USERNAME): cv.string,
        vol.Required(ATTR_FILEPATH): cv.string,
    }
)

EXPORT_SAVED_LIBRARY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_USERNAME): cv.string,
        vol.Required(ATTR_FILEPATH): cv.string,
    }
)

EXPORT_PLAYLISTS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_USERNAME): cv.string,
        vol.Required(ATTR_FILEPATH): cv.string,
    }
)

EXPORT_RECENTLY_PLAYED_CSV_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_USERNAME): cv.string,
        vol.Required(ATTR_FILEPATH): cv.string,
        vol.Optional(ATTR_APPEND, default=True): cv.boolean,
        vol.Optional(ATTR_INCLUDE_AUDIO_FEATURES, default=False): cv.boolean,
    }
)

EXPORT_TOP_STATS_CSV_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_USERNAME): cv.string,
        vol.Required(ATTR_FILEPATH): cv.string,
        vol.Required(ATTR_ENTITY_TYPE): vol.In(["artists", "tracks"]),
        vol.Required(ATTR_TIME_RANGE): vol.In(["short_term", "medium_term", "long_term"]),
    }
)

SET_UPDATE_INTERVAL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_USERNAME): cv.string,
        vol.Optional(CONF_NOW_PLAYING_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=30, max=300)
        ),
        vol.Optional(CONF_RECENTLY_PLAYED_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=300, max=3600)
        ),
    }
)

REFRESH_NOW_PLAYING_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_USERNAME): cv.string,
    }
)


def sanitize_username(username: str) -> str:
    """Convert username to valid format."""
    return username.lower().replace(" ", "_").replace("-", "_")


def get_coordinator_for_username(
    hass: HomeAssistant, username: str
) -> SpotifyStatsCoordinator | None:
    """Get coordinator for a specific username."""
    sanitized = sanitize_username(username)
    
    for entry_id, coordinator in hass.data[DOMAIN].items():
        if sanitize_username(coordinator.username) == sanitized:
            return coordinator
    
    _LOGGER.error("No coordinator found for username: %s", username)
    return None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Spotify Statistics."""

    async def export_followed_artists(call: ServiceCall) -> None:
        """Export followed artists to JSON."""
        username = call.data[ATTR_USERNAME]
        filepath = call.data[ATTR_FILEPATH]
        
        _LOGGER.info("Export followed artists called - username: %s, filepath: %s", username, filepath)
        
        coordinator = get_coordinator_for_username(hass, username)
        if not coordinator:
            _LOGGER.error("No coordinator found for username: %s", username)
            return
        
        try:
            # Get all followed artists
            followed_data = coordinator.data.get("followed_artists", {})
            all_artists = followed_data.get("all_artists", [])
            
            _LOGGER.debug("Found %s followed artists in coordinator data", len(all_artists))
            
            if not all_artists:
                _LOGGER.warning("No followed artists data available for %s", username)
                return
            
            # Make filepath absolute if it's not
            if not os.path.isabs(filepath):
                filepath = os.path.join(hass.config.config_dir, filepath)
            
            _LOGGER.debug("Using absolute filepath: %s", filepath)
            
            # Fetch complete metadata for all artists
            artists_full = await hass.async_add_executor_job(
                _fetch_all_artists_metadata, coordinator.sp, all_artists
            )
            
            export_data = {
                "exported_at": dt_util.utcnow().isoformat(),
                "username": username,
                "total_count": len(artists_full),
                "artists": artists_full,
            }
            
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
                _LOGGER.debug("Created directory: %s", directory)
            
            # Write JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            _LOGGER.info(
                "Successfully exported %s followed artists for %s to %s",
                len(artists_full),
                username,
                filepath,
            )
        except Exception as err:
            _LOGGER.error("Failed to export followed artists: %s", err, exc_info=True)

    async def export_saved_library(call: ServiceCall) -> None:
        """Export saved albums and tracks to JSON."""
        username = call.data[ATTR_USERNAME]
        filepath = call.data[ATTR_FILEPATH]
        
        coordinator = get_coordinator_for_username(hass, username)
        if not coordinator:
            return
        
        try:
            library_data = await hass.async_add_executor_job(
                _fetch_saved_library, coordinator.sp
            )
            
            export_data = {
                "exported_at": dt_util.utcnow().isoformat(),
                "username": username,
                "albums": library_data["albums"],
                "tracks": library_data["tracks"],
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            _LOGGER.info(
                "Exported library for %s (%s albums, %s tracks) to %s",
                username,
                library_data["albums"]["total_count"],
                library_data["tracks"]["total_count"],
                filepath,
            )
        except Exception as err:
            _LOGGER.error("Failed to export saved library: %s", err)

    async def export_playlists(call: ServiceCall) -> None:
        """Export playlists with track listings to JSON."""
        username = call.data[ATTR_USERNAME]
        filepath = call.data[ATTR_FILEPATH]
        
        _LOGGER.info("Export playlists called - username: %s, filepath: %s", username, filepath)
        
        coordinator = get_coordinator_for_username(hass, username)
        if not coordinator:
            _LOGGER.error("No coordinator found for username: %s", username)
            return
        
        try:
            # Make filepath absolute if it's not
            if not os.path.isabs(filepath):
                filepath = os.path.join(hass.config.config_dir, filepath)
            
            _LOGGER.debug("Fetching playlists via API")
            playlists_data = await hass.async_add_executor_job(
                _fetch_playlists, coordinator.sp
            )
            
            export_data = {
                "exported_at": dt_util.utcnow().isoformat(),
                "username": username,
                "total_count": len(playlists_data),
                "playlists": playlists_data,
            }
            
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            
            # Write JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            _LOGGER.info(
                "Successfully exported %s playlists for %s to %s",
                len(playlists_data),
                username,
                filepath,
            )
        except Exception as err:
            _LOGGER.error("Failed to export playlists: %s", err, exc_info=True)

    async def export_recently_played_csv(call: ServiceCall) -> None:
        """Export recently played tracks to CSV."""
        username = call.data[ATTR_USERNAME]
        filepath = call.data[ATTR_FILEPATH]
        append = call.data[ATTR_APPEND]
        include_audio_features = call.data[ATTR_INCLUDE_AUDIO_FEATURES]
        
        coordinator = get_coordinator_for_username(hass, username)
        if not coordinator:
            return
        
        try:
            recently_played = coordinator.data.get("recently_played", {})
            tracks = recently_played.get("tracks", [])
            
            if not tracks:
                _LOGGER.warning("No recently played tracks to export for %s", username)
                return
            
            # Get existing timestamps to avoid duplicates
            existing_timestamps = set()
            if append and os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    existing_timestamps = {row["played_at"] for row in reader if "played_at" in row}
            
            # Filter new tracks
            new_tracks = [
                track for track in tracks
                if track["played_at"] not in existing_timestamps
            ]
            
            if not new_tracks:
                _LOGGER.info("No new tracks to export for %s", username)
                return
            
            # Fetch audio features if requested
            if include_audio_features:
                track_ids = [t["track_id"] for t in new_tracks]
                audio_features = await hass.async_add_executor_job(
                    coordinator.sp.audio_features, track_ids
                )
                # Merge audio features into tracks
                for track, features in zip(new_tracks, audio_features):
                    if features:
                        track.update({
                            "danceability": features.get("danceability"),
                            "energy": features.get("energy"),
                            "key": features.get("key"),
                            "loudness": features.get("loudness"),
                            "mode": features.get("mode"),
                            "speechiness": features.get("speechiness"),
                            "acousticness": features.get("acousticness"),
                            "instrumentalness": features.get("instrumentalness"),
                            "liveness": features.get("liveness"),
                            "valence": features.get("valence"),
                            "tempo": features.get("tempo"),
                        })
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Define CSV columns
            columns = [
                "username",
                "played_at",
                "track_id",
                "track_name",
                "artist_id",
                "artist_name",
                "album_name",
                "album_id",
                "duration_ms",
                "popularity",
                "explicit",
                "track_url",
            ]
            
            if include_audio_features:
                columns.extend([
                    "danceability",
                    "energy",
                    "key",
                    "loudness",
                    "mode",
                    "speechiness",
                    "acousticness",
                    "instrumentalness",
                    "liveness",
                    "valence",
                    "tempo",
                ])
            
            # Write CSV
            mode = "a" if append and os.path.exists(filepath) else "w"
            write_header = not (append and os.path.exists(filepath))
            
            with open(filepath, mode, encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                
                if write_header:
                    writer.writeheader()
                
                for track in new_tracks:
                    row = {"username": username}
                    row.update({col: track.get(col, "") for col in columns if col != "username"})
                    writer.writerow(row)
            
            _LOGGER.info(
                "Exported %s tracks for %s to %s",
                len(new_tracks),
                username,
                filepath,
            )
        except Exception as err:
            _LOGGER.error("Failed to export recently played CSV: %s", err)

    async def export_top_stats_csv(call: ServiceCall) -> None:
        """Export top stats snapshot to CSV."""
        username = call.data[ATTR_USERNAME]
        filepath = call.data[ATTR_FILEPATH]
        entity_type = call.data[ATTR_ENTITY_TYPE]
        time_range = call.data[ATTR_TIME_RANGE]
        
        coordinator = get_coordinator_for_username(hass, username)
        if not coordinator:
            return
        
        try:
            # Map time_range to period key
            period_map = {
                TIME_RANGE_SHORT: "4weeks",
                TIME_RANGE_MEDIUM: "6months",
                TIME_RANGE_LONG: "alltime",
            }
            period = period_map[time_range]
            
            # Get data
            data_key = f"top_{entity_type}_{period}"
            data = coordinator.data.get(data_key, {})
            items = data.get(entity_type, [])
            
            if not items:
                _LOGGER.warning("No %s data to export for %s", entity_type, username)
                return
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Define CSV columns
            if entity_type == "artists":
                columns = ["username", "export_date", "rank", "id", "name", "url", "genres", "popularity"]
            else:  # tracks
                columns = ["username", "export_date", "rank", "id", "name", "artist_name", "artist_id", "album_name", "url", "popularity"]
            
            # Write CSV
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=columns)
                writer.writeheader()
                
                export_date = dt_util.utcnow().date().isoformat()
                
                for item in items:
                    row = {
                        "username": username,
                        "export_date": export_date,
                        "rank": item.get("rank"),
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "url": item.get("url"),
                    }
                    
                    if entity_type == "artists":
                        row["genres"] = ";".join(item.get("genres", []))
                        row["popularity"] = item.get("popularity", "")
                    else:  # tracks
                        row["artist_name"] = item.get("artist_name")
                        row["artist_id"] = item.get("artist_id")
                        row["album_name"] = item.get("album_name")
                        row["popularity"] = item.get("popularity", "")
                    
                    writer.writerow(row)
            
            _LOGGER.info(
                "Exported %s top %s for %s to %s",
                len(items),
                entity_type,
                username,
                filepath,
            )
        except Exception as err:
            _LOGGER.error("Failed to export top stats CSV: %s", err)

    async def set_update_interval(call: ServiceCall) -> None:
        """Set update intervals for a user."""
        username = call.data[ATTR_USERNAME]
        now_playing = call.data.get(CONF_NOW_PLAYING_INTERVAL)
        recently_played = call.data.get(CONF_RECENTLY_PLAYED_INTERVAL)
        
        coordinator = get_coordinator_for_username(hass, username)
        if not coordinator:
            return
        
        try:
            await coordinator.async_set_update_interval(now_playing, recently_played)
            _LOGGER.info("Updated intervals for %s", username)
        except Exception as err:
            _LOGGER.error("Failed to set update interval: %s", err)

    async def refresh_now_playing(call: ServiceCall) -> None:
        """Immediately refresh now playing sensor."""
        username = call.data[ATTR_USERNAME]
        
        coordinator = get_coordinator_for_username(hass, username)
        if not coordinator:
            return
        
        try:
            await coordinator.async_request_refresh()
            _LOGGER.info("Refreshed now playing for %s", username)
        except Exception as err:
            _LOGGER.error("Failed to refresh now playing: %s", err)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_FOLLOWED_ARTISTS,
        export_followed_artists,
        schema=EXPORT_FOLLOWED_ARTISTS_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_SAVED_LIBRARY,
        export_saved_library,
        schema=EXPORT_SAVED_LIBRARY_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_PLAYLISTS,
        export_playlists,
        schema=EXPORT_PLAYLISTS_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_RECENTLY_PLAYED_CSV,
        export_recently_played_csv,
        schema=EXPORT_RECENTLY_PLAYED_CSV_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_TOP_STATS_CSV,
        export_top_stats_csv,
        schema=EXPORT_TOP_STATS_CSV_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_UPDATE_INTERVAL,
        set_update_interval,
        schema=SET_UPDATE_INTERVAL_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH_NOW_PLAYING,
        refresh_now_playing,
        schema=REFRESH_NOW_PLAYING_SCHEMA,
    )
    
    _LOGGER.info("Registered Spotify Statistics services")


def _fetch_all_artists_metadata(sp, artists: list[dict]) -> list[dict]:
    """Fetch complete metadata for all artists."""
    result = []
    
    for artist in artists:
        try:
            full_artist = sp.artist(artist["id"])
            result.append({
                "id": full_artist["id"],
                "name": full_artist["name"],
                "url": full_artist["external_urls"]["spotify"],
                "uri": full_artist["uri"],
                "followers": full_artist["followers"]["total"],
                "genres": full_artist.get("genres", []),
                "images": full_artist.get("images", []),
                "popularity": full_artist.get("popularity", 0),
                "type": full_artist["type"],
            })
        except Exception as err:
            _LOGGER.warning("Failed to fetch artist %s: %s", artist["id"], err)
            result.append(artist)  # Use basic data if fetch fails
    
    return result


def _fetch_saved_library(sp) -> dict[str, Any]:
    """Fetch all saved albums and tracks."""
    albums = []
    tracks = []
    
    # Fetch albums
    offset = 0
    while True:
        results = sp.current_user_saved_albums(limit=50, offset=offset)
        albums.extend(results["items"])
        
        if not results["next"]:
            break
        offset += 50
    
    # Fetch tracks
    offset = 0
    while True:
        results = sp.current_user_saved_tracks(limit=50, offset=offset)
        tracks.extend(results["items"])
        
        if not results["next"]:
            break
        offset += 50
    
    return {
        "albums": {
            "total_count": len(albums),
            "items": albums,
        },
        "tracks": {
            "total_count": len(tracks),
            "items": tracks,
        },
    }


def _fetch_playlists(sp) -> list[dict]:
    """Fetch all playlists with full track listings."""
    playlists = []
    
    # Get user's playlists
    offset = 0
    while True:
        results = sp.current_user_playlists(limit=50, offset=offset)
        
        for playlist in results["items"]:
            try:
                # Fetch full playlist with tracks
                full_playlist = sp.playlist(playlist["id"])
                playlists.append(full_playlist)
            except spotipy.exceptions.SpotifyException as err:
                if err.http_status == 404:
                    _LOGGER.warning(
                        "Playlist %s (%s) not found (deleted or private), skipping",
                        playlist["name"],
                        playlist["id"],
                    )
                    # Add basic info without tracks
                    playlists.append({
                        "id": playlist["id"],
                        "name": playlist["name"],
                        "owner": playlist["owner"],
                        "tracks": {"total": playlist["tracks"]["total"]},
                        "public": playlist.get("public"),
                        "collaborative": playlist.get("collaborative"),
                        "external_urls": playlist.get("external_urls", {}),
                        "note": "Unable to fetch full details (404 error)",
                    })
                else:
                    _LOGGER.error("Error fetching playlist %s: %s", playlist["id"], err)
            except Exception as err:
                _LOGGER.error("Unexpected error fetching playlist %s: %s", playlist["id"], err)
        
        if not results["next"]:
            break
        offset += 50
    
    return playlists
