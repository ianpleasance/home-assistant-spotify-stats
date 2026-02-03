"""DataUpdateCoordinator for Spotify Statistics."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_NOW_PLAYING_INTERVAL,
    CONF_RECENTLY_PLAYED_INTERVAL,
    CONF_USERNAME,
    DOMAIN,
    SENSOR_FOLLOWED_ARTISTS,
    SENSOR_NOW_PLAYING,
    SENSOR_RECENTLY_PLAYED,
    SENSOR_TOP_ARTISTS_4WEEKS,
    SENSOR_TOP_ARTISTS_6MONTHS,
    SENSOR_TOP_ARTISTS_ALLTIME,
    SENSOR_TOP_TRACKS_4WEEKS,
    SENSOR_TOP_TRACKS_6MONTHS,
    SENSOR_TOP_TRACKS_ALLTIME,
    SPOTIFY_SCOPES,
    TIME_RANGE_LONG,
    TIME_RANGE_MEDIUM,
    TIME_RANGE_SHORT,
    UPDATE_INTERVAL_FOLLOWED,
    UPDATE_INTERVAL_TOP_STATS,
)

_LOGGER = logging.getLogger(__name__)


class SpotifyStatsCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Spotify data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.username = entry.data[CONF_USERNAME]
        self._client_id = entry.data[CONF_CLIENT_ID]
        self._client_secret = entry.data[CONF_CLIENT_SECRET]
        
        # Get update intervals from config
        self.now_playing_interval = entry.data.get(
            CONF_NOW_PLAYING_INTERVAL, 30
        )
        self.recently_played_interval = entry.data.get(
            CONF_RECENTLY_PLAYED_INTERVAL, 300
        )
        
        # Initialize Spotify client
        self.sp: spotipy.Spotify | None = None
        self._init_spotify_client()
        
        # Initialize data storage
        self.data: dict[str, Any] = {}
        
        # Track last update times for different data types
        self._last_followed_update = None
        self._last_top_stats_update = None
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.username}",
            update_interval=timedelta(seconds=self.now_playing_interval),
        )

    def _init_spotify_client(self) -> None:
        """Initialize the Spotify client with OAuth."""
        try:
            auth_manager = SpotifyOAuth(
                client_id=self._client_id,
                client_secret=self._client_secret,
                redirect_uri=f"{self.hass.config.api.base_url}/auth/external/callback",
                scope=" ".join(SPOTIFY_SCOPES),
                cache_path=self.hass.config.path(f".spotify_cache_{self.username}"),
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            _LOGGER.debug("Initialized Spotify client for user: %s", self.username)
        except Exception as err:
            _LOGGER.error("Failed to initialize Spotify client: %s", err)
            raise ConfigEntryAuthFailed from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Spotify API."""
        try:
            data = {}
            
            # Always update now playing and recently played
            data[SENSOR_NOW_PLAYING] = await self.hass.async_add_executor_job(
                self._fetch_now_playing
            )
            data[SENSOR_RECENTLY_PLAYED] = await self.hass.async_add_executor_job(
                self._fetch_recently_played
            )
            
            # Update followed artists hourly
            if self._should_update_followed():
                data[SENSOR_FOLLOWED_ARTISTS] = await self.hass.async_add_executor_job(
                    self._fetch_followed_artists
                )
                self._last_followed_update = self.hass.helpers.utcnow()
            else:
                data[SENSOR_FOLLOWED_ARTISTS] = self.data.get(SENSOR_FOLLOWED_ARTISTS)
            
            # Update top stats daily
            if self._should_update_top_stats():
                data.update(await self.hass.async_add_executor_job(
                    self._fetch_top_stats
                ))
                self._last_top_stats_update = self.hass.helpers.utcnow()
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
            self.hass.helpers.utcnow() - self._last_followed_update
        ).total_seconds()
        return time_since_update >= UPDATE_INTERVAL_FOLLOWED

    def _should_update_top_stats(self) -> bool:
        """Check if top stats should be updated."""
        if self._last_top_stats_update is None:
            return True
        
        time_since_update = (
            self.hass.helpers.utcnow() - self._last_top_stats_update
        ).total_seconds()
        return time_since_update >= UPDATE_INTERVAL_TOP_STATS

    def _fetch_now_playing(self) -> dict[str, Any]:
        """Fetch currently playing track."""
        current = self.sp.current_playback()
        
        if not current or not current.get("item"):
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
        recent = self.sp.current_user_recently_played(limit=50)
        
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
