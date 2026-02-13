"""Application credentials platform for Spotify Statistics."""
from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

from .const import DOMAIN

OAUTH2_AUTHORIZE = "https://accounts.spotify.com/authorize"
OAUTH2_TOKEN = "https://accounts.spotify.com/api/token"


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server."""
    return AuthorizationServer(
        authorize_url=OAUTH2_AUTHORIZE,
        token_url=OAUTH2_TOKEN,
    )


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials dialog."""
    return {
        "oauth_url": "https://developer.spotify.com/dashboard/applications",
        "more_info_url": "https://github.com/ianpleasance/home-assistant-spotify-stats",
    }
