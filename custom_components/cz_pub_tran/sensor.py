"""Support for cz_pub_tran sensors."""
import voluptuous as vol
import logging
from homeassistant.helpers import config_validation as cv, discovery
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_NAME
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity, async_generate_entity_id
import asyncio
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'cz_pub_tran'
COMPONENT_NAME = 'sensor'
ENTITY_ID_FORMAT = COMPONENT_NAME + ".{}"

ICON_BUS = "mdi:bus"

DESCRIPTION_FORMAT_OPTIONS = ['HTML','text']

CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_USERID = "userId"
CONF_COMBINATION_ID = "combination_id"
CONF_FORCE_REFRESH_PERIOD = "force_refresh_period"
CONF_DESCRIPTION_FORMAT = "description_format"

ATTR_DURATION = "duration"
ATTR_DEPARTURE = "departure"
ATTR_CONNECTIONS = "connections"
ATTR_DESCRIPTION = "description"
ATTR_DETAIL = "detail"
ATTR_START_TIME = "start_time"
ATTR_DELAY = "delay"

TRACKABLE_DOMAINS = ["sensor"]

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_FORCE_REFRESH_PERIOD = 5
DEFAULT_DESCRIPTION_FORMAT = 'text'
DEFAULT_COMBINATION_ID = "ABCz"
DEFAULT_NAME = "cz_pub_tran"

HTTP_TIMEOUT = 5

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_ORIGIN): cv.string,
        vol.Required(CONF_DESTINATION): cv.string,
        vol.Optional(CONF_COMBINATION_ID, default=DEFAULT_COMBINATION_ID): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_USERID,default=""): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
                vol.Optional(CONF_DESCRIPTION_FORMAT, default=DEFAULT_DESCRIPTION_FORMAT): vol.In(DESCRIPTION_FORMAT_OPTIONS),
                vol.Optional(CONF_FORCE_REFRESH_PERIOD, default=DEFAULT_FORCE_REFRESH_PERIOD): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA])
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    if discovery_info is None:
        return
    devs = []
    for sensor in discovery_info:
        devs.append(CZPubTranSensor(hass, SENSOR_SCHEMA(sensor)))
    async_add_entities(devs,True)

class CZPubTranSensor(Entity):
    """Representation of a openroute service travel time sensor."""
    def __init__(self, hass, config):
        """Initialize the sensor."""
        self._name = config.get(CONF_NAME)
        self._origin = config.get(CONF_ORIGIN)
        self._destination = config.get(CONF_DESTINATION)
        self._combination_id = config.get(CONF_COMBINATION_ID)
        self._forced_refresh_countdown = 1
        self._start_time = None
        self.load_defaults()
        # _LOGGER.debug(f'Entity {self._name} inicialized')

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
        res[ATTR_START_TIME] = self._start_time
        res[ATTR_DETAIL] = self._detail
        return res

    @property
    def icon(self):
        return ICON_BUS

    def scheduled_connection(self,forced_refresh_period):
        """Return False if Connection needs to be updated."""
        try:
            if self._forced_refresh_countdown <= 0 or self._departure == '':
                self._forced_refresh_countdown = forced_refresh_period if forced_refresh_period > 0 else 1
                return False
            departure_time=datetime.strptime(self._departure,"%H:%M").time()
            now=datetime.now().time()
            if forced_refresh_period == 0:
                return bool(now < departure_time or ( now.hour> 22 and departure_time < 6 ))
            else:
                if now < departure_time or ( now.hour> 22 and departure_time < 6 ):
                    self._forced_refresh_countdown -= 1
                    return True
                else:
                    self._forced_refresh_countdown = forced_refresh_period
                    return False
        except:
            return False # Refresh data on Error

    def update_status(self,departure,duration,state,connections,description,detail,delay):
        self._departure = departure
        self._duration = duration
        self._state = state
        self._connections = connections
        self._description = description
        self._detail = detail
        self._delay = delay

    def load_defaults(self):
        self.update_status("","","","","",[[],[]],"")
        
    async def async_added_to_hass(self):
        """Entity added. Entity ID ready"""
        self.hass.data[DOMAIN].add_entity_id(self.entity_id)
        self.hass.data[DOMAIN].add_sensor(self)
        # _LOGGER.debug(f'Entity {self.entity_id} added')
