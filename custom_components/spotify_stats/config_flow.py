"""Config flow for Spotify Statistics integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_NOW_PLAYING_INTERVAL,
    CONF_RECENTLY_PLAYED_INTERVAL,
    CONF_USERNAME,
    DEFAULT_NOW_PLAYING_INTERVAL,
    DEFAULT_RECENTLY_PLAYED_INTERVAL,
    DOMAIN,
    MAX_NOW_PLAYING_INTERVAL,
    MAX_RECENTLY_PLAYED_INTERVAL,
    MIN_NOW_PLAYING_INTERVAL,
    MIN_RECENTLY_PLAYED_INTERVAL,
    SPOTIFY_SCOPES,
)

_LOGGER = logging.getLogger(__name__)


def sanitize_username(username: str) -> str:
    """Convert username to valid entity ID format."""
    return username.lower().replace(" ", "_").replace("-", "_")


class SpotifyStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Spotify Statistics."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._now_playing_interval: int = DEFAULT_NOW_PLAYING_INTERVAL
        self._recently_played_interval: int = DEFAULT_RECENTLY_PLAYED_INTERVAL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate username uniqueness
            username = sanitize_username(user_input[CONF_USERNAME])
            
            existing_usernames = [
                sanitize_username(entry.data[CONF_USERNAME])
                for entry in self._async_current_entries()
            ]
            
            if username in existing_usernames:
                errors["username"] = "already_configured"
            else:
                # Store credentials and proceed to OAuth
                self._username = user_input[CONF_USERNAME]
                self._client_id = user_input[CONF_CLIENT_ID]
                self._client_secret = user_input[CONF_CLIENT_SECRET]
                self._now_playing_interval = user_input.get(
                    CONF_NOW_PLAYING_INTERVAL, DEFAULT_NOW_PLAYING_INTERVAL
                )
                self._recently_played_interval = user_input.get(
                    CONF_RECENTLY_PLAYED_INTERVAL, DEFAULT_RECENTLY_PLAYED_INTERVAL
                )
                
                # Create entry
                return self.async_create_entry(
                    title=f"Spotify Stats ({self._username})",
                    data={
                        CONF_USERNAME: self._username,
                        CONF_CLIENT_ID: self._client_id,
                        CONF_CLIENT_SECRET: self._client_secret,
                        CONF_NOW_PLAYING_INTERVAL: self._now_playing_interval,
                        CONF_RECENTLY_PLAYED_INTERVAL: self._recently_played_interval,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Optional(
                        CONF_NOW_PLAYING_INTERVAL,
                        default=DEFAULT_NOW_PLAYING_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_NOW_PLAYING_INTERVAL,
                            max=MAX_NOW_PLAYING_INTERVAL,
                        ),
                    ),
                    vol.Optional(
                        CONF_RECENTLY_PLAYED_INTERVAL,
                        default=DEFAULT_RECENTLY_PLAYED_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_RECENTLY_PLAYED_INTERVAL,
                            max=MAX_RECENTLY_PLAYED_INTERVAL,
                        ),
                    ),
                }
            ),
            errors=errors,
            description_placeholders={
                "username_help": "Your Spotify username or display name (e.g., 'ian')",
                "interval_help": "Update intervals in seconds",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SpotifyStatsOptionsFlowHandler:
        """Get the options flow for this handler."""
        return SpotifyStatsOptionsFlowHandler(config_entry)


class SpotifyStatsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Spotify Statistics."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry with new options
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NOW_PLAYING_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_NOW_PLAYING_INTERVAL,
                            DEFAULT_NOW_PLAYING_INTERVAL,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_NOW_PLAYING_INTERVAL,
                            max=MAX_NOW_PLAYING_INTERVAL,
                        ),
                    ),
                    vol.Optional(
                        CONF_RECENTLY_PLAYED_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_RECENTLY_PLAYED_INTERVAL,
                            DEFAULT_RECENTLY_PLAYED_INTERVAL,
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_RECENTLY_PLAYED_INTERVAL,
                            max=MAX_RECENTLY_PLAYED_INTERVAL,
                        ),
                    ),
                }
            ),
        )
