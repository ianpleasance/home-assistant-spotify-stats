"""DataUpdateCoordinator for Spotify Statistics."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_NOW_PLAYING_INTERVAL,
    CONF_RECENTLY_PLAYED_INTERVAL,
    CONF_USERNAME,
    DOMAIN,
    SENSOR_FOLLOWED_ARTISTS,
    SENSOR_NOW_PLAYING,
    SENSOR_RECENTLY_PLAYED,
    SENSOR_SAVED_ALBUMS,
    SENSOR_SAVED_TRACKS,
    SENSOR_TOP_ARTISTS_4WEEKS,
    SENSOR_TOP_ARTISTS_6MONTHS,
    SENSOR_TOP_ARTISTS_ALLTIME,
    SENSOR_TOP_TRACKS_4WEEKS,
    SENSOR_TOP_TRACKS_6MONTHS,
    SENSOR_TOP_TRACKS_ALLTIME,
    SENSOR_USER_PLAYLISTS,
    TIME_RANGE_LONG,
    TIME_RANGE_MEDIUM,
    TIME_RANGE_SHORT,
    UPDATE_INTERVAL_FOLLOWED,
    UPDATE_INTERVAL_TOP_STATS,
)

_LOGGER = logging.getLogger(__name__)


class SpotifyStatsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Spotify data."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, session: OAuth2Session
    ) -> None:
        """Initialize the coordinator."""
        _LOGGER.debug("SpotifyStatsCoordinator.__init__ starting for user: %s", entry.data.get(CONF_USERNAME))
        
        self.session = session
        self.entry = entry
        self.username = entry.data[CONF_USERNAME]

        # Get update intervals from config
        self.now_playing_interval = entry.data.get(
            CONF_NOW_PLAYING_INTERVAL, 30
        )
        self.recently_played_interval = entry.data.get(
            CONF_RECENTLY_PLAYED_INTERVAL, 300
        )
        
        _LOGGER.debug("SpotifyStatsCoordinator: Update intervals - now_playing: %s, recently_played: %s", 
                     self.now_playing_interval, self.recently_played_interval)

        # Spotify client (will be initialized lazily)
        self.sp: spotipy.Spotify | None = None
        self._sp_initialized = False
        
        _LOGGER.debug("SpotifyStatsCoordinator: Spotify client variables initialized")

        # Track last update times for different data types
        self._last_followed_update = None
        self._last_top_stats_update = None
        
        _LOGGER.debug("SpotifyStatsCoordinator: About to call super().__init__")

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.username}",
            update_interval=timedelta(seconds=self.now_playing_interval),
        )
        
        _LOGGER.debug("SpotifyStatsCoordinator.__init__ completed for user: %s", self.username)

    async def _async_ensure_token_valid(self) -> str:
        """Ensure we have a valid access token."""
        try:
            await self.session.async_ensure_token_valid()
            token = self.session.token
            _LOGGER.debug("Token keys available: %s", list(token.keys()))
            
            # OAuth2 tokens use 'access_token' not CONF_ACCESS_TOKEN
            if "access_token" in token:
                access_token = token["access_token"]
            elif CONF_ACCESS_TOKEN in token:
                access_token = token[CONF_ACCESS_TOKEN]
            else:
                _LOGGER.error("No access_token found in token dict. Available keys: %s", list(token.keys()))
                raise ConfigEntryAuthFailed("No access token in session")
            
            _LOGGER.debug("Got access token: %s...", access_token[:20] if access_token else "None")
            return access_token
        except Exception as err:
            _LOGGER.error("Failed to refresh Spotify token: %s", err, exc_info=True)
            raise ConfigEntryAuthFailed from err

    def _init_spotify_client(self, access_token: str) -> None:
        """Initialize the Spotify client with access token."""
        _LOGGER.debug("_init_spotify_client called for user: %s with token: %s...", 
                     self.username, access_token[:20] if access_token else "None")
        
        try:
            # Always recreate the client with the latest token
            # spotipy.Spotify(auth=token) creates a simple client that uses bearer token auth
            self.sp = spotipy.Spotify(auth=access_token)
            self._sp_initialized = True
            
            _LOGGER.debug("Initialized Spotify client for user: %s", self.username)
        except Exception as err:
            _LOGGER.error("Failed to initialize Spotify client: %s", err, exc_info=True)
            raise ConfigEntryAuthFailed from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Spotify API."""
        _LOGGER.debug("_async_update_data called for user: %s", self.username)
        
        try:
            # Ensure we have a valid token
            _LOGGER.debug("_async_update_data: Checking for valid token...")
            access_token = await self._async_ensure_token_valid()
            _LOGGER.debug("_async_update_data: Got valid access token: %s...", access_token[:20] if access_token else "None")
            
            # Initialize/update Spotify client
            _LOGGER.debug("_async_update_data: Initializing Spotify client...")
            await self.hass.async_add_executor_job(
                self._init_spotify_client, access_token
            )
            _LOGGER.debug("_async_update_data: Spotify client initialized successfully")
            
        except ConfigEntryAuthFailed as err:
            _LOGGER.error("_async_update_data: Authentication failed: %s", err, exc_info=True)
            raise
        except Exception as err:
            _LOGGER.error("_async_update_data: Failed to setup Spotify client: %s", err, exc_info=True)
            raise UpdateFailed(f"Authentication failed: {err}") from err
        
        try:
            data = {}
            
            _LOGGER.debug("_async_update_data: Fetching now playing")
            # Always update now playing and recently played
            data[SENSOR_NOW_PLAYING] = await self.hass.async_add_executor_job(
                self._fetch_now_playing
            )
            _LOGGER.debug("_async_update_data: Now playing fetched successfully")
            
            _LOGGER.debug("_async_update_data: Fetching recently played")
            data[SENSOR_RECENTLY_PLAYED] = await self.hass.async_add_executor_job(
                self._fetch_recently_played
            )
            _LOGGER.debug("_async_update_data: Recently played fetched successfully")

            # Update followed artists hourly
            if self._should_update_followed():
                data[SENSOR_FOLLOWED_ARTISTS] = await self.hass.async_add_executor_job(
                    self._fetch_followed_artists
                )
                self._last_followed_update = dt_util.utcnow()
            else:
                data[SENSOR_FOLLOWED_ARTISTS] = self.data.get(SENSOR_FOLLOWED_ARTISTS)

            # Update top stats daily
            if self._should_update_top_stats():
                data.update(await self.hass.async_add_executor_job(
                    self._fetch_top_stats
                ))
                self._last_top_stats_update = dt_util.utcnow()
            else:
                # Use cached data
                for key in [
                    SENSOR_TOP_ARTISTS_4WEEKS,
                    SENSOR_TOP_ARTISTS_6MONTHS,
                    SENSOR_TOP_ARTISTS_ALLTIME,
                    SENSOR_TOP_TRACKS_4WEEKS,
                    SENSOR_TOP_TRACKS_6MONTHS,
                    SENSOR_TOP_TRACKS_ALLTIME,
                ]:
                    data[key] = self.data.get(key)

            _LOGGER.debug("_async_update_data: Fetching playlists")
            data[SENSOR_USER_PLAYLISTS] = await self.hass.async_add_executor_job(
                self._fetch_user_playlists
            )
            _LOGGER.debug("_async_update_data: Playlists fetched successfully")
            
            _LOGGER.debug("_async_update_data: Fetching saved tracks")
            data[SENSOR_SAVED_TRACKS] = await self.hass.async_add_executor_job(
                self._fetch_saved_tracks
            )
            _LOGGER.debug("_async_update_data: Saved tracks fetched successfully")
            
            _LOGGER.debug("_async_update_data: Fetching saved albums")
            data[SENSOR_SAVED_ALBUMS] = await self.hass.async_add_executor_job(
                self._fetch_saved_albums
            )
            _LOGGER.debug("_async_update_data: Saved albums fetched successfully")

            return data

        except spotipy.exceptions.SpotifyException as err:
            if err.http_status == 401:
                raise ConfigEntryAuthFailed("Spotify authentication expired") from err
            raise UpdateFailed(f"Error communicating with Spotify API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _should_update_followed(self) -> bool:
        """Check if followed artists should be updated."""
        if self._last_followed_update is None:
            return True

        time_since_update = (
            dt_util.utcnow() - self._last_followed_update
        ).total_seconds()
        return time_since_update >= UPDATE_INTERVAL_FOLLOWED

    def _should_update_top_stats(self) -> bool:
        """Check if top stats should be updated."""
        if self._last_top_stats_update is None:
            return True

        time_since_update = (
            dt_util.utcnow() - self._last_top_stats_update
        ).total_seconds()
        return time_since_update >= UPDATE_INTERVAL_TOP_STATS

    def _fetch_now_playing(self) -> dict[str, Any]:
        """Fetch currently playing track."""
        _LOGGER.debug("_fetch_now_playing: Starting fetch")
        _LOGGER.debug("_fetch_now_playing: Spotify client auth: %s", 
                     self.sp.auth if hasattr(self.sp, 'auth') else "No auth")
        try:
            _LOGGER.debug("_fetch_now_playing: Calling current_playback()")
            current = self.sp.current_playback()
            _LOGGER.debug("_fetch_now_playing: Got response from Spotify API")
        except spotipy.exceptions.SpotifyException as err:
            _LOGGER.error("_fetch_now_playing: Spotify API error: %s (status: %s)", 
                         err, err.http_status, exc_info=True)
            _LOGGER.error("_fetch_now_playing: Response body: %s", err.msg if hasattr(err, 'msg') else "No message")
            raise
        except Exception as err:
            _LOGGER.error("_fetch_now_playing: Unexpected error: %s", err, exc_info=True)
            raise

        if not current or not current.get("item"):
            _LOGGER.debug("_fetch_now_playing: Nothing currently playing")
            return {"state": "idle"}

        track = current["item"]
        return {
            "state": "playing" if current["is_playing"] else "paused",
            "track_id": track["id"],
            "track_name": track["name"],
            "artist_id": track["artists"][0]["id"],
            "artist_name": track["artists"][0]["name"],
            "album_name": track["album"]["name"],
            "album_id": track["album"]["id"],
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "duration_ms": track["duration_ms"],
            "progress_ms": current.get("progress_ms", 0),
            "popularity": track.get("popularity", 0),
            "track_url": track["external_urls"]["spotify"],
            "is_playing": current["is_playing"],
            "shuffle_state": current.get("shuffle_state", False),
            "repeat_state": current.get("repeat_state", "off"),
        }

    def _fetch_recently_played(self) -> dict[str, Any]:
        """Fetch recently played tracks."""
        recent = self.sp.current_user_recently_played(limit=20)

        tracks = []
        for item in recent.get("items", []):
            track = item["track"]
            tracks.append({
                "played_at": item["played_at"],
                "track_id": track["id"],
                "track_name": track["name"],
                "artist_id": track["artists"][0]["id"],
                "artist_name": track["artists"][0]["name"],
                "album_name": track["album"]["name"],
                "album_id": track["album"]["id"],
                "track_url": track["external_urls"]["spotify"],
                "duration_ms": track["duration_ms"],
                "popularity": track.get("popularity", 0),
                "explicit": track.get("explicit", False),
            })

        return {
            "count": len(tracks),
            "tracks": tracks,
            "last_played": tracks[0]["played_at"] if tracks else None,
        }

    def _fetch_followed_artists(self) -> dict[str, Any]:
        """Fetch followed artists."""
        results = []
        after = None

        # Spotify returns max 50 at a time, paginate through all
        while True:
            response = self.sp.current_user_followed_artists(limit=50, after=after)
            artists = response["artists"]

            for artist in artists["items"]:
                results.append({
                    "id": artist["id"],
                    "name": artist["name"],
                    "url": artist["external_urls"]["spotify"],
                    "image": artist["images"][0]["url"] if artist["images"] else None,
                    "genres": artist.get("genres", []),
                    "popularity": artist.get("popularity", 0),
                })

            if not artists["next"]:
                break

            after = artists["cursors"]["after"]

        return {
            "count": len(results),
            "artists": results[:20],  # Limit to 20 in sensor attributes
            "all_artists": results,  # Store all for export
        }

    def _fetch_top_stats(self) -> dict[str, Any]:
        """Fetch top artists and tracks for all time ranges."""
        data = {}

        # Top artists
        for period, time_range in [
            ("4weeks", TIME_RANGE_SHORT),
            ("6months", TIME_RANGE_MEDIUM),
            ("alltime", TIME_RANGE_LONG),
        ]:
            artists = self.sp.current_user_top_artists(limit=50, time_range=time_range)
            data[f"top_artists_{period}"] = {
                "count": len(artists["items"]),
                "period": time_range,
                "artists": [
                    {
                        "id": artist["id"],
                        "name": artist["name"],
                        "url": artist["external_urls"]["spotify"],
                        "rank": idx + 1,
                        "genres": artist.get("genres", []),
                        "popularity": artist.get("popularity", 0),
                    }
                    for idx, artist in enumerate(artists["items"])
                ],
            }

        # Top tracks
        for period, time_range in [
            ("4weeks", TIME_RANGE_SHORT),
            ("6months", TIME_RANGE_MEDIUM),
            ("alltime", TIME_RANGE_LONG),
        ]:
            tracks = self.sp.current_user_top_tracks(limit=50, time_range=time_range)
            data[f"top_tracks_{period}"] = {
                "count": len(tracks["items"]),
                "period": time_range,
                "tracks": [
                    {
                        "id": track["id"],
                        "name": track["name"],
                        "artist_name": track["artists"][0]["name"],
                        "artist_id": track["artists"][0]["id"],
                        "album_name": track["album"]["name"],
                        "url": track["external_urls"]["spotify"],
                        "rank": idx + 1,
                        "popularity": track.get("popularity", 0),
                    }
                    for idx, track in enumerate(tracks["items"])
                ],
            }

        return data

    def _fetch_user_playlists(self) -> dict[str, Any]:
        """Fetch user's playlists."""
        _LOGGER.debug("_fetch_user_playlists: Starting fetch")
        
        try:
            playlists = []
            results = self.sp.current_user_playlists(limit=50)
            
            while results:
                for playlist in results["items"]:
                    playlists.append({
                        "id": playlist["id"],
                        "name": playlist["name"],
                        "url": playlist["external_urls"]["spotify"],
                        "uri": playlist["uri"],
                        "tracks_total": playlist["tracks"]["total"],
                        "description": playlist.get("description", ""),
                        "public": playlist.get("public", False),
                        "collaborative": playlist.get("collaborative", False),
                        "owner": playlist["owner"]["display_name"],
                        "owner_id": playlist["owner"]["id"],
                    })
                
                # Get next page if available
                if results["next"]:
                    results = self.sp.next(results)
                else:
                    results = None
            
            _LOGGER.debug("_fetch_user_playlists: Found %s playlists", len(playlists))
            
            # Store only first 20 in attributes to avoid database size issues
            playlists_for_attributes = playlists[:20]
            
            return {
                "count": len(playlists),
                "playlists": playlists_for_attributes,
                "all_playlists": playlists,  # Keep full list for export services
            }
        except Exception as err:
            _LOGGER.error("_fetch_user_playlists: Error: %s", err, exc_info=True)
            return {"count": 0, "playlists": [], "all_playlists": []}

    def _fetch_saved_tracks(self) -> dict[str, Any]:
        """Fetch user's saved tracks."""
        _LOGGER.debug("_fetch_saved_tracks: Starting fetch")
        
        try:
            # Get total count first
            results = self.sp.current_user_saved_tracks(limit=1)
            total_count = results["total"]
            
            # Fetch first 50 tracks with details
            tracks = []
            results = self.sp.current_user_saved_tracks(limit=50)
            
            for item in results["items"]:
                track = item.get("track")
                
                # Skip if track is None (deleted/unavailable)
                if not track:
                    _LOGGER.warning("Skipping saved track with no data (possibly deleted)")
                    continue
                
                # Skip if track doesn't have required fields
                if not track.get("id") or not track.get("artists") or not track.get("album"):
                    _LOGGER.warning("Skipping track with missing data: %s", track.get("name", "Unknown"))
                    continue
                
                try:
                    tracks.append({
                        "id": track["id"],
                        "name": track.get("name", "Unknown Track"),
                        "artist_name": track["artists"][0]["name"],
                        "artist_id": track["artists"][0]["id"],
                        "album_name": track["album"]["name"],
                        "album_id": track["album"]["id"],
                        "url": track["external_urls"]["spotify"],
                        "uri": track.get("uri", ""),
                        "duration_ms": track.get("duration_ms", 0),
                        "popularity": track.get("popularity", 0),
                        "added_at": item.get("added_at", ""),
                    })
                except (KeyError, IndexError, TypeError) as err:
                    _LOGGER.warning("Error processing track %s: %s", track.get("name", "Unknown"), err)
                    continue
            
            _LOGGER.debug("_fetch_saved_tracks: Total %s tracks, fetched %s", total_count, len(tracks))
            
            # Store only first 20 in attributes to avoid database size issues
            tracks_for_attributes = tracks[:20]
            
            return {
                "count": total_count,
                "tracks": tracks_for_attributes,
            }
        except Exception as err:
            _LOGGER.error("_fetch_saved_tracks: Error: %s", err, exc_info=True)
            return {"count": 0, "tracks": []}

    def _fetch_saved_albums(self) -> dict[str, Any]:
        """Fetch user's saved albums."""
        _LOGGER.debug("_fetch_saved_albums: Starting fetch")
        
        try:
            # Get total count first
            results = self.sp.current_user_saved_albums(limit=1)
            total_count = results["total"]
            
            # Fetch first 50 albums with details
            albums = []
            results = self.sp.current_user_saved_albums(limit=50)
            
            for item in results["items"]:
                album = item.get("album")
                
                # Skip if album is None (deleted/unavailable)
                if not album:
                    _LOGGER.warning("Skipping saved album with no data (possibly deleted)")
                    continue
                
                # Skip if album doesn't have required fields
                if not album.get("id") or not album.get("artists"):
                    _LOGGER.warning("Skipping album with missing data: %s", album.get("name", "Unknown"))
                    continue
                
                try:
                    albums.append({
                        "id": album["id"],
                        "name": album.get("name", "Unknown Album"),
                        "artist_name": album["artists"][0]["name"],
                        "artist_id": album["artists"][0]["id"],
                        "url": album["external_urls"]["spotify"],
                        "uri": album.get("uri", ""),
                        "total_tracks": album.get("total_tracks", 0),
                        "release_date": album.get("release_date", ""),
                        "added_at": item.get("added_at", ""),
                    })
                except (KeyError, IndexError, TypeError) as err:
                    _LOGGER.warning("Error processing album %s: %s", album.get("name", "Unknown"), err)
                    continue
            
            _LOGGER.debug("_fetch_saved_albums: Total %s albums, fetched %s", total_count, len(albums))
            
            # Store only first 20 in attributes to avoid database size issues
            albums_for_attributes = albums[:20]
            
            return {
                "count": total_count,
                "albums": albums_for_attributes,
            }
        except Exception as err:
            _LOGGER.error("_fetch_saved_albums: Error: %s", err, exc_info=True)
            return {"count": 0, "albums": []}

    async def async_set_update_interval(
        self, now_playing: int | None = None, recently_played: int | None = None
    ) -> None:
        """Dynamically update polling intervals."""
        if now_playing is not None:
            self.now_playing_interval = now_playing
            _LOGGER.debug(
                "Updated now_playing interval to %s seconds for user %s",
                now_playing,
                self.username,
            )

        if recently_played is not None:
            self.recently_played_interval = recently_played
            _LOGGER.debug(
                "Updated recently_played interval to %s seconds for user %s",
                recently_played,
                self.username,
            )

        # Update the coordinator's update interval to the shorter of the two
        min_interval = min(
            self.now_playing_interval,
            self.recently_played_interval,
        )
        self.update_interval = timedelta(seconds=min_interval)

        # Trigger an immediate update
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Clean up resources."""
        _LOGGER.debug("Shutting down coordinator for user: %s", self.username)
