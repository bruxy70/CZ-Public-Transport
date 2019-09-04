"""Support for cz_pub_tran sensors."""
from . import Connection
import logging, json, requests
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "cz_pub_tran"

ICON_BUS = "mdi:bus"

CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_USERID = "userId"

CONF_COMBINATION_ID = "combination_id"
DEFAULT_COMBINATION_ID = "ABCz"

ATTR_DURATION = "duration"
ATTR_DEPARTURE = "departure"
ATTR_CONNECTIONS = "connections"
ATTR_DESCRIPTION = "description"
ATTR_DELAY = "delay"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ORIGIN): cv.string,
    vol.Required(CONF_DESTINATION): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_COMBINATION_ID, default=DEFAULT_COMBINATION_ID): cv.string,
    vol.Optional(CONF_USERID,default=""): cv.string,
})

SCAN_INTERVAL = timedelta(seconds=60)
THROTTLE_INTERVAL = timedelta(seconds=10)
HTTP_TIMEOUT = 5

TRACKABLE_DOMAINS = ["sensor"]

class ErrorGettingData(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    origin = config[CONF_ORIGIN]
    destination = config[CONF_DESTINATION]
    name = config.get(CONF_NAME)
    combination_id = config.get(CONF_COMBINATION_ID)
    user_id = config.get(CONF_USERID)
    session = async_get_clientsession(hass)
    async_add_entities([CZPubTranSensor(hass, session, name, origin, destination,combination_id,user_id)],True)


class CZPubTranSensor(Connection):
    """Representation of a openroute service travel time sensor."""
    def __init__(self, hass, session, name, origin, destination,combination_id,user_id):
        """Initialize the sensor."""
        super().__init__(hass,session, name, origin, destination,combination_id,user_id)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the name of the sensor."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        res = {}
        res[ATTR_DEPARTURE] = self._departure
        res[ATTR_DURATION] = self._duration
        res[ATTR_DELAY] = self._delay
        res[ATTR_CONNECTIONS] = self._connections
        res[ATTR_DESCRIPTION] = self._description
        return res

    @property
    def icon(self):
        return ICON_BUS