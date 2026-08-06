"""The Spotify Statistics integration."""
from __future__ import annotations

import logging
import asyncio
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.setup import async_wait_component as async_wait_for_domain

from .const import DOMAIN, SETUP_TIMEOUT_SECONDS
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
        # Wrap setup in timeout to prevent hanging indefinitely
        async with asyncio.timeout(SETUP_TIMEOUT_SECONDS):
            # Wait for the core Spotify integration to be ready.
            # NOTE: hass.config_entries.async_wait_component(entry) resolves
            # to entry.domain internally - since `entry` here is this very
            # spotify_stats entry, that call was waiting on the
            # "spotify_stats" domain (itself, still mid-setup) rather than
            # on "spotify" as intended, causing an unresolvable self-wait
            # that always ran out the clock at the bootstrap timeout.
            # async_wait_component from homeassistant.setup takes a domain
            # string directly and correctly waits on a *different*
            # integration's setup.
            await async_wait_for_domain(hass, "spotify")
            
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
                
                try:
                    spotify_implementations = await config_entry_oauth2_flow.async_get_implementations(
                        hass, "spotify"
                    )
                except Exception as err:
                    _LOGGER.warning("Failed to get Spotify implementations: %s", err)
                    raise ConfigEntryNotReady("Waiting for Spotify integration to be ready") from err
                
                if not spotify_implementations:
                    _LOGGER.warning("Spotify integration not configured or not ready yet")
                    raise ConfigEntryNotReady("Spotify integration not configured. Please set up the Spotify integration first.")
                
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
                try:
                    implementation = (
                        await config_entry_oauth2_flow.async_get_config_entry_implementation(
                            hass, entry
                        )
                    )
                except ValueError as err:
                    _LOGGER.warning("Still cannot get implementation after registration")
                    raise ConfigEntryNotReady("OAuth implementation not ready, will retry") from err
            
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
            
            # Return True inside the timeout block
            return True
        
    except asyncio.TimeoutError:
        _LOGGER.error("Spotify Statistics setup timed out after %s seconds", SETUP_TIMEOUT_SECONDS)
        raise ConfigEntryNotReady("Spotify integration taking too long to initialize, will retry")
        
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

