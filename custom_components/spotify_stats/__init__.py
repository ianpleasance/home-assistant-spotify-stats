"""The Spotify Statistics integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN
from .coordinator import SpotifyStatsCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify Statistics from a config entry."""
    _LOGGER.debug("Setting up Spotify Statistics for user: %s", entry.data.get("username"))

    try:
        # Create coordinator for this user
        coordinator = SpotifyStatsCoordinator(hass, entry)
        
        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()
        
        # Store coordinator
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = coordinator
        
        # Setup platforms
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        # Register services
        await async_setup_services(hass)
        
        # Listen for options updates
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))
        
        _LOGGER.info("Successfully set up Spotify Statistics for user: %s", entry.data.get("username"))
        return True
        
    except ConfigEntryAuthFailed as err:
        _LOGGER.error("Authentication failed for user %s: %s", entry.data.get("username"), err)
        raise
    except Exception as err:
        _LOGGER.error("Error setting up Spotify Statistics for user %s: %s", entry.data.get("username"), err)
        raise ConfigEntryNotReady from err


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Spotify Statistics for user: %s", entry.data.get("username"))
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        
        # Cancel any pending updates
        if hasattr(coordinator, 'async_shutdown'):
            await coordinator.async_shutdown()
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    _LOGGER.debug("Reloading Spotify Statistics for user: %s", entry.data.get("username"))
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the integration."""
    from .services import async_setup_services as setup_services
    
    # Only setup services once
    if DOMAIN not in hass.services.async_services():
        await setup_services(hass)
