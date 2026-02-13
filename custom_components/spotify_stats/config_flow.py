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


class SpotifyStatsFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for Spotify Statistics."""

    DOMAIN = DOMAIN
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self._username: str | None = None
        self._now_playing_interval: int = DEFAULT_NOW_PLAYING_INTERVAL
        self._recently_played_interval: int = DEFAULT_RECENTLY_PLAYED_INTERVAL

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": " ".join(SPOTIFY_SCOPES)}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        # Use Spotify's OAuth implementation from the main spotify integration
        implementations = await config_entry_oauth2_flow.async_get_implementations(
            self.hass, "spotify"  # Use spotify domain, not our domain
        )
        
        if not implementations:
            return self.async_abort(
                reason="missing_configuration",
                description_placeholders={
                    "docs_url": "https://www.home-assistant.io/integrations/spotify/"
                }
            )
        
        # Register Spotify's implementation for our domain
        for impl_domain, impl in implementations.items():
            config_entry_oauth2_flow.async_register_implementation(
                self.hass,
                self.DOMAIN,
                impl,
            )
            _LOGGER.info("Registered Spotify OAuth implementation: %s", impl_domain)
        
        if user_input is not None:
            # Store username and intervals
            self._username = user_input[CONF_USERNAME]
            self._now_playing_interval = user_input.get(
                CONF_NOW_PLAYING_INTERVAL, DEFAULT_NOW_PLAYING_INTERVAL
            )
            self._recently_played_interval = user_input.get(
                CONF_RECENTLY_PLAYED_INTERVAL, DEFAULT_RECENTLY_PLAYED_INTERVAL
            )
            
            # Check if username already exists
            username = sanitize_username(self._username)
            existing_usernames = [
                sanitize_username(entry.data.get(CONF_USERNAME, ""))
                for entry in self._async_current_entries()
            ]
            
            if username in existing_usernames:
                return self.async_abort(reason="already_configured")
            
            # Continue to OAuth step
            return await self.async_step_pick_implementation()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
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
            description_placeholders={
                "username_help": "Your Spotify username (e.g., 'planetbuilders')",
            },
        )

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create an entry for the flow."""
        _LOGGER.info("async_oauth_create_entry called for user: %s", self._username)
        
        # Combine OAuth data with our stored values
        data[CONF_USERNAME] = self._username
        data[CONF_NOW_PLAYING_INTERVAL] = self._now_playing_interval
        data[CONF_RECENTLY_PLAYED_INTERVAL] = self._recently_played_interval
        
        return self.async_create_entry(
            title=f"Spotify Stats ({self._username})",
            data=data,
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
            new_data = dict(self.config_entry.data)
            new_data[CONF_NOW_PLAYING_INTERVAL] = user_input[CONF_NOW_PLAYING_INTERVAL]
            new_data[CONF_RECENTLY_PLAYED_INTERVAL] = user_input[CONF_RECENTLY_PLAYED_INTERVAL]
            
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=new_data,
            )
            
            return self.async_create_entry(title="", data={})

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
