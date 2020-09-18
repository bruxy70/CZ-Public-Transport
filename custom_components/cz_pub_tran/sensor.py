"""Support for cz_pub_tran sensors."""
import asyncio
import logging
from datetime import date, datetime, time, timedelta

import voluptuous as vol
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity, async_generate_entity_id

from .constants import (
    ATTR_CONNECTIONS,
    ATTR_DELAY,
    ATTR_DEPARTURE,
    ATTR_DESCRIPTION,
    ATTR_DETAIL,
    ATTR_DURATION,
    ATTR_START_TIME,
    CONF_COMBINATION_ID,
    CONF_DESCRIPTION_FORMAT,
    CONF_DESTINATION,
    CONF_FORCE_REFRESH_PERIOD,
    CONF_ORIGIN,
    CONF_USERID,
    DESCRIPTION_FORMAT_OPTIONS,
    DOMAIN,
    ENTITY_ID_FORMAT,
    ICON_BUS,
    PLATFORM,
    SENSOR_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

HTTP_TIMEOUT = 5


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    _LOGGER.debug(f"async_setup_entry   config_entry.data {config_entry.data}")
    async_add_devices([CZPubTranSensor(hass, config_entry.data)], True)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    if discovery_info is None:
        return
    devs = []
    _LOGGER.debug(f"async_setup_platform   discovery_info {discovery_info}")
    for sensor in discovery_info:
        devs.append(CZPubTranSensor(hass, SENSOR_SCHEMA(sensor)))
    async_add_entities(devs, True)


class CZPubTranSensor(Entity):
    """Representation of a openroute service travel time sensor."""

    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.__name = config.get(CONF_NAME)
        self.__origin = config.get(CONF_ORIGIN)
        self.__destination = config.get(CONF_DESTINATION)
        self.__combination_id = config.get(CONF_COMBINATION_ID)
        self.__forced_refresh_countdown = 1
        self.__unique_id = config.get("unique_id", None)
        self.__start_time = None
        self.load_defaults()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.__name

    @property
    def origin(self):
        """Return the origin."""
        return self.__origin

    @property
    def destination(self):
        """Return the destination."""
        return self.__destination

    @property
    def combination_id(self):
        """Return the combination id."""
        return self.__combination_id

    @property
    def start_time(self):
        """Return the start time."""
        return self.__start_time

    @start_time.setter
    def start_time(self, value):
        """Sets start time property"""
        self.__start_time = value

    @property
    def state(self):
        """Return the name of the sensor."""
        return self.__state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        res = {}
        res[ATTR_DEPARTURE] = self.__departure
        res[ATTR_DURATION] = self.__duration
        res[ATTR_DELAY] = self.__delay
        res[ATTR_CONNECTIONS] = self.__connections
        res[ATTR_DESCRIPTION] = self.__description
        res[ATTR_START_TIME] = self.__start_time
        res[ATTR_DETAIL] = self.__detail
        return res

    @property
    def icon(self):
        return ICON_BUS

    @property
    def unique_id(self):
        return self.__unique_id

    def scheduled_connection(self, forced_refresh_period):
        """Return False if Connection needs to be updated."""
        try:
            if self.__forced_refresh_countdown <= 0 or self.__departure == "":
                self.__forced_refresh_countdown = (
                    forced_refresh_period if forced_refresh_period > 0 else 1
                )
                return False
            departure_time = datetime.strptime(self.__departure, "%H:%M").time()
            now = datetime.now().time()
            connection_valid = bool(
                now < departure_time or (now.hour > 22 and departure_time < 6)
            )
            if forced_refresh_period == 0:
                return bool(
                    now < departure_time or (now.hour > 22 and departure_time < 6)
                )
            else:
                if connection_valid:
                    self.__forced_refresh_countdown -= 1
                    return True
                else:
                    self.__forced_refresh_countdown = forced_refresh_period
                    return False
        except:
            return False  # Refresh data on Error

    def update_status(
        self, departure, duration, state, connections, description, detail, delay
    ):
        self.__departure = departure
        self.__duration = duration
        self.__state = state
        self.__connections = connections
        self.__description = description
        self.__detail = detail
        self.__delay = delay

    def load_defaults(self):
        self.update_status("", "", "", "", "", [[], []], "")

    async def async_added_to_hass(self):
        """Entity added. Entity ID ready"""
        self.hass.data[DOMAIN].add_entity_id(self.entity_id)
        self.hass.data[DOMAIN].add_sensor(self)
