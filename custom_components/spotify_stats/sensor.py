"""Sensor platform for Spotify Statistics."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
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
)
from .coordinator import SpotifyStatsCoordinator

_LOGGER = logging.getLogger(__name__)


def sanitize_username(username: str) -> str:
    """Convert username to valid entity ID format."""
    return username.lower().replace(" ", "_").replace("-", "_")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Spotify Statistics sensors."""
    coordinator: SpotifyStatsCoordinator = hass.data[DOMAIN][entry.entry_id]
    username = entry.data[CONF_USERNAME]
    
    sensors = [
        SpotifyNowPlayingSensor(coordinator, username),
        SpotifyRecentlyPlayedSensor(coordinator, username),
        SpotifyFollowedArtistsSensor(coordinator, username),
        SpotifyTopArtistsSensor(coordinator, username, "4weeks"),
        SpotifyTopArtistsSensor(coordinator, username, "6months"),
        SpotifyTopArtistsSensor(coordinator, username, "alltime"),
        SpotifyTopTracksSensor(coordinator, username, "4weeks"),
        SpotifyTopTracksSensor(coordinator, username, "6months"),
        SpotifyTopTracksSensor(coordinator, username, "alltime"),
        SpotifyUserPlaylistsSensor(coordinator, username),
        SpotifySavedTracksSensor(coordinator, username),
        SpotifySavedAlbumsSensor(coordinator, username),
    ]
    
    async_add_entities(sensors)
    _LOGGER.debug("Added %s Spotify sensors for user: %s", len(sensors), username)


class SpotifyStatsBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Spotify Statistics sensors."""

    def __init__(
        self,
        coordinator: SpotifyStatsCoordinator,
        username: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.username = username
        self._sanitized_username = sanitize_username(username)
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._sanitized_username}_account")},
            name=f"Spotify Stats ({self.username})",
            manufacturer="Spotify",
            model="Account",
        )


class SpotifyNowPlayingSensor(SpotifyStatsBaseSensor):
    """Sensor for currently playing track."""

    def __init__(self, coordinator: SpotifyStatsCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_name = f"{username} Spotify Stats Now Playing"
        self._attr_unique_id = f"{self._sanitized_username}_spotify_stats_now_playing"
        self._attr_icon = "mdi:spotify"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        data = self.coordinator.data.get(SENSOR_NOW_PLAYING, {})
        return data.get("state", "idle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(SENSOR_NOW_PLAYING, {})
        
        if data.get("state") == "idle":
            return {"state": "idle"}
        
        return {
            "track_id": data.get("track_id"),
            "track_name": data.get("track_name"),
            "artist_id": data.get("artist_id"),
            "artist_name": data.get("artist_name"),
            "album_name": data.get("album_name"),
            "album_id": data.get("album_id"),
            "image_url": data.get("image_url"),
            "duration_ms": data.get("duration_ms"),
            "progress_ms": data.get("progress_ms"),
            "popularity": data.get("popularity"),
            "track_url": data.get("track_url"),
            "is_playing": data.get("is_playing"),
            "shuffle_state": data.get("shuffle_state"),
            "repeat_state": data.get("repeat_state"),
        }


class SpotifyRecentlyPlayedSensor(SpotifyStatsBaseSensor):
    """Sensor for recently played tracks."""

    def __init__(self, coordinator: SpotifyStatsCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_name = f"{username} Spotify Stats Recently Played"
        self._attr_unique_id = f"{self._sanitized_username}_spotify_stats_recently_played"
        self._attr_icon = "mdi:history"

    @property
    def native_value(self) -> str | None:
        """Return the timestamp of the most recent track."""
        data = self.coordinator.data.get(SENSOR_RECENTLY_PLAYED, {})
        return data.get("last_played")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(SENSOR_RECENTLY_PLAYED, {})
        return {
            "count": data.get("count", 0),
            "tracks": data.get("tracks", []),
        }


class SpotifyFollowedArtistsSensor(SpotifyStatsBaseSensor):
    """Sensor for followed artists."""

    def __init__(self, coordinator: SpotifyStatsCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_name = f"{username} Spotify Stats Followed Artists"
        self._attr_unique_id = f"{self._sanitized_username}_spotify_stats_followed_artists"
        self._attr_icon = "mdi:account-music"

    @property
    def native_value(self) -> int:
        """Return the count of followed artists."""
        data = self.coordinator.data.get(SENSOR_FOLLOWED_ARTISTS, {})
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(SENSOR_FOLLOWED_ARTISTS, {})
        return {
            "artists": data.get("artists", []),  # Limited to 20
            "total_count": data.get("count", 0),
        }


class SpotifyTopArtistsSensor(SpotifyStatsBaseSensor):
    """Sensor for top artists."""

    def __init__(
        self, coordinator: SpotifyStatsCoordinator, username: str, period: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self.period = period
        self._attr_name = f"{username} Spotify Stats Top Artists {period.title()}"
        self._attr_unique_id = (
            f"{self._sanitized_username}_spotify_stats_top_artists_{period}"
        )
        self._attr_icon = "mdi:trophy"

    @property
    def native_value(self) -> int:
        """Return the count of top artists."""
        data = self.coordinator.data.get(f"top_artists_{self.period}", {})
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(f"top_artists_{self.period}", {})
        return {
            "period": data.get("period"),
            "artists": data.get("artists", []),
        }


class SpotifyTopTracksSensor(SpotifyStatsBaseSensor):
    """Sensor for top tracks."""

    def __init__(
        self, coordinator: SpotifyStatsCoordinator, username: str, period: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self.period = period
        self._attr_name = f"{username} Spotify Stats Top Tracks {period.title()}"
        self._attr_unique_id = (
            f"{self._sanitized_username}_spotify_stats_top_tracks_{period}"
        )
        self._attr_icon = "mdi:music-note"

    @property
    def native_value(self) -> int:
        """Return the count of top tracks."""
        data = self.coordinator.data.get(f"top_tracks_{self.period}", {})
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(f"top_tracks_{self.period}", {})
        return {
            "period": data.get("period"),
            "tracks": data.get("tracks", []),
        }


class SpotifyUserPlaylistsSensor(SpotifyStatsBaseSensor):
    """Sensor for user playlists."""

    def __init__(self, coordinator: SpotifyStatsCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_name = f"{username} Spotify Stats Playlists"
        self._attr_unique_id = f"{self._sanitized_username}_spotify_stats_playlists"
        self._attr_icon = "mdi:playlist-music"

    @property
    def native_value(self) -> int:
        """Return the count of playlists."""
        data = self.coordinator.data.get(SENSOR_USER_PLAYLISTS, {})
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(SENSOR_USER_PLAYLISTS, {})
        return {
            "playlists": data.get("playlists", []),
        }


class SpotifySavedTracksSensor(SpotifyStatsBaseSensor):
    """Sensor for saved tracks."""

    def __init__(self, coordinator: SpotifyStatsCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_name = f"{username} Spotify Stats Saved Tracks"
        self._attr_unique_id = f"{self._sanitized_username}_spotify_stats_saved_tracks"
        self._attr_icon = "mdi:heart"

    @property
    def native_value(self) -> int:
        """Return the count of saved tracks."""
        data = self.coordinator.data.get(SENSOR_SAVED_TRACKS, {})
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(SENSOR_SAVED_TRACKS, {})
        return {
            "tracks": data.get("tracks", []),
        }


class SpotifySavedAlbumsSensor(SpotifyStatsBaseSensor):
    """Sensor for saved albums."""

    def __init__(self, coordinator: SpotifyStatsCoordinator, username: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, username)
        self._attr_name = f"{username} Spotify Stats Saved Albums"
        self._attr_unique_id = f"{self._sanitized_username}_spotify_stats_saved_albums"
        self._attr_icon = "mdi:album"

    @property
    def native_value(self) -> int:
        """Return the count of saved albums."""
        data = self.coordinator.data.get(SENSOR_SAVED_ALBUMS, {})
        return data.get("count", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        data = self.coordinator.data.get(SENSOR_SAVED_ALBUMS, {})
        return {
            "albums": data.get("albums", []),
        }
