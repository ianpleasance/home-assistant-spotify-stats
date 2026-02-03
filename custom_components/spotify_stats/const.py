"""Constants for the Spotify Statistics integration."""
from homeassistant.const import Platform

DOMAIN = "spotify_stats"
PLATFORMS = [Platform.SENSOR]

# Configuration constants
CONF_USERNAME = "username"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_NOW_PLAYING_INTERVAL = "now_playing_interval"
CONF_RECENTLY_PLAYED_INTERVAL = "recently_played_interval"

# Default values
DEFAULT_NOW_PLAYING_INTERVAL = 30  # seconds
DEFAULT_RECENTLY_PLAYED_INTERVAL = 300  # seconds
MIN_NOW_PLAYING_INTERVAL = 30
MAX_NOW_PLAYING_INTERVAL = 300
MIN_RECENTLY_PLAYED_INTERVAL = 300
MAX_RECENTLY_PLAYED_INTERVAL = 3600

# Spotify API scopes required
SPOTIFY_SCOPES = [
    "user-read-currently-playing",
    "user-read-recently-played",
    "user-top-read",
    "user-follow-read",
    "user-library-read",
    "playlist-read-private",
    "playlist-read-collaborative",
]

# Sensor types
SENSOR_NOW_PLAYING = "now_playing"
SENSOR_RECENTLY_PLAYED = "recently_played"
SENSOR_FOLLOWED_ARTISTS = "followed_artists"
SENSOR_TOP_ARTISTS_4WEEKS = "top_artists_4weeks"
SENSOR_TOP_ARTISTS_6MONTHS = "top_artists_6months"
SENSOR_TOP_ARTISTS_ALLTIME = "top_artists_alltime"
SENSOR_TOP_TRACKS_4WEEKS = "top_tracks_4weeks"
SENSOR_TOP_TRACKS_6MONTHS = "top_tracks_6months"
SENSOR_TOP_TRACKS_ALLTIME = "top_tracks_alltime"

# Time ranges for top stats
TIME_RANGE_SHORT = "short_term"  # 4 weeks
TIME_RANGE_MEDIUM = "medium_term"  # 6 months
TIME_RANGE_LONG = "long_term"  # all time

TIME_RANGE_MAP = {
    "4weeks": TIME_RANGE_SHORT,
    "6months": TIME_RANGE_MEDIUM,
    "alltime": TIME_RANGE_LONG,
}

# Service names
SERVICE_EXPORT_FOLLOWED_ARTISTS = "export_followed_artists"
SERVICE_EXPORT_SAVED_LIBRARY = "export_saved_library"
SERVICE_EXPORT_PLAYLISTS = "export_playlists"
SERVICE_EXPORT_RECENTLY_PLAYED_CSV = "export_recently_played_csv"
SERVICE_EXPORT_TOP_STATS_CSV = "export_top_stats_csv"
SERVICE_SET_UPDATE_INTERVAL = "set_update_interval"
SERVICE_REFRESH_NOW_PLAYING = "refresh_now_playing"

# Service parameters
ATTR_USERNAME = "username"
ATTR_FILEPATH = "filepath"
ATTR_APPEND = "append"
ATTR_INCLUDE_AUDIO_FEATURES = "include_audio_features"
ATTR_ENTITY_TYPE = "entity_type"
ATTR_TIME_RANGE = "time_range"

# Update intervals (in seconds)
UPDATE_INTERVAL_NOW_PLAYING = 30
UPDATE_INTERVAL_RECENTLY_PLAYED = 300
UPDATE_INTERVAL_TOP_STATS = 86400  # Daily
UPDATE_INTERVAL_FOLLOWED = 3600  # Hourly
