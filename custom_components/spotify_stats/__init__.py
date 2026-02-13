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


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Spotify Statistics component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spotify Statistics from a config entry."""
    _LOGGER.debug("Setting up Spotify Statistics for user: %s", entry.data.get("username"))

    try:
        # Wait for Spotify integration to be ready
        await hass.config_entries.async_wait_component(entry)
        
        # Get OAuth2 session - try to get implementation
        try:
            implementation = (
                await config_entry_oauth2_flow.async_get_config_entry_implementation(
                    hass, entry
                )
            )
        except ValueError:
            # Implementation not found - register from spotify domain
            _LOGGER.debug("OAuth implementation not found, registering from spotify domain")
            spotify_implementations = await config_entry_oauth2_flow.async_get_implementations(
                hass, "spotify"
            )
            
            if not spotify_implementations:
                _LOGGER.error("Spotify integration not configured. Please set up the Spotify integration first.")
                raise ConfigEntryNotReady("Spotify integration not configured")
            
            # Register the first available implementation for our domain
            for impl_domain, impl in spotify_implementations.items():
                config_entry_oauth2_flow.async_register_implementation(
                    hass,
                    DOMAIN,
                    impl,
                )
                _LOGGER.info("Registered Spotify OAuth implementation: %s", impl_domain)
                break
            
            # Now get the implementation
            implementation = (
                await config_entry_oauth2_flow.async_get_config_entry_implementation(
                    hass, entry
                )
            )
        
        _LOGGER.debug("Got OAuth2 implementation: %s", implementation)
        
        session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
        _LOGGER.debug("Created OAuth2 session")
        
        # Create coordinator for this user
        coordinator = SpotifyStatsCoordinator(hass, entry, session)
        
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
        _LOGGER.error("Error setting up Spotify Statistics for user %s: %s", entry.data.get("username"), err, exc_info=True)
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
