"""Support for cz_pub_tran sensors."""
from . import Connection
import logging, json, requests
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (
    CONF_NAME
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

ICON_BUS = "mdi:bus"

CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_USERID = "userId"

CONF_COMBINATION_ID = "combination_id"

ATTR_DURATION = "duration"
ATTR_DEPARTURE = "departure"
ATTR_CONNECTIONS = "connections"
ATTR_DESCRIPTION = "description"
ATTR_DELAY = "delay"

TRACKABLE_DOMAINS = ["sensor"]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    origin = config[CONF_ORIGIN]
    destination = config[CONF_DESTINATION]
    name = config.get(CONF_NAME)
    combination_id = config.get(CONF_COMBINATION_ID)
    async_add_entities([CZPubTranSensor(hass, name, origin, destination,combination_id)],True)


class CZPubTranSensor(Entity):
    """Representation of a openroute service travel time sensor."""
    def __init__(self, hass, session, name, origin, destination,combination_id):
        """Initialize the sensor."""
        self._name = name
        self._origin = origin
        self._destination = destination
        self._combination_id = combination_id
        self._lastupdated = None
        self._forced_refresh_countdown = 0
        self.load_defaults()
        self.entity_id=async_generate_entity_id(ENTITY_ID_FORMAT,name,hass.data[DOMAIN].entity_ids())
        hass.data[DOMAIN].add_entity_id(self.entity_id)
        _LOGGER.debug(f'Entity {self.entity_id} inicialized')

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

    def scheduled_connection(self):
        """Return False if Connection needs to be updated."""
        try:
            if self.forced_refresh_countdown <= 0 or self._departure == "":
                self.forced_refresh_countdown = FORCED_REFRESH_COUNT
                return False
            departure_time=datetime.strptime(self._departure,"%H:%M").time()
            now=datetime.now().time()
            if now < departure_time or ( now.hour> 22 and departure_time < 6 ):
                self.forced_refresh_countdown = self.forced_refresh_countdown - 1
                return True
            else:
                self.forced_refresh_countdown = FORCED_REFRESH_COUNT
                return False
        except:
            return False # Refresh data on Error

    def update_status(self,departure,duration,state,connections,description,delay):
        self._departure = departure
        self._duration = duration
        self._state = state
        self._connections = connectiobs
        self._description = description
        self._delay = delay

    def load_defaults(self):
        self.update_status("","","","","","")
        
    async def async_added_to_hass(self):
        """I probably do not need this! To be removed! Call when entity is added to hass."""
        hass.data[DOMAIN].add_sensor(self)
        _LOGGER.debug(f'Entity {self.entity_id} added')
