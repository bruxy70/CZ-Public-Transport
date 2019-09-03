"""Support for cz_pub_tran domain"""
import logging, json, requests
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import async_timeout
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity, async_generate_entity_id

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'cz_pub_tran'

async def async_setup(hass, base_config):
    """Setup the sensor platform."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]['traffic_light'] = False
    hass.data[DOMAIN]['combination_ids'] = {}
    return True

class Connection(Entity):
    """Representation of a device entity. Will pass to binary_sensor and others"""
    entity_ids = []
    connections = []

    def __init__(self,hass,session, name, origin, destination,combination_id,user_id):
        """Initialize the device."""
        self._session = session
        self._name = name
        self._origin = origin
        self._destination = destination
        self._combination_id = combination_id
        self._user_id = user_id
        self._lastupdated = None
        self._duration = ""
        self._departure = ""
        self._connections = ""
        self._description = ""
        self._state = ""
        self.entity_id=async_generate_entity_id('sensor.{}',name,Connection.entity_ids)
        Connection.entity_ids.append(self.entity_id)
        _LOGGER.debug("Entity %s inicialized",self.entity_id)
        
    async def async_added_to_hass(self):
        """I probably do not need this! To be removed! Call when entity is added to hass."""
        Connection.connections.append(self)
        _LOGGER.debug( "Entity %s added",self.entity_id)