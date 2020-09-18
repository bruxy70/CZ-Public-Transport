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
    """Add devices for sensor config flow."""
    _LOGGER.debug(f"async_setup_entry   config_entry.data {config_entry.data}")
    async_add_devices([CZPubTranSensor(hass, config_entry.data)], True)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Add devices for platform (YAML)."""
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
        self._name = config.get(CONF_NAME)
        self._origin = config.get(CONF_ORIGIN)
        self._destination = config.get(CONF_DESTINATION)
        self._combination_id = config.get(CONF_COMBINATION_ID)
        self._forced_refresh_countdown = 1
        self._unique_id = config.get("unique_id", None)
        self._start_time = None
        self.load_defaults()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def origin(self):
        """Return the origin."""
        return self._origin

    @property
    def destination(self):
        """Return the destination."""
        return self._destination

    @property
    def combination_id(self):
        """Return the combination id."""
        return self._combination_id

    @property
    def start_time(self):
        """Return the start time."""
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        """Sets start time property"""
        self._start_time = value

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
        """Return the icon - constant."""
        return ICON_BUS

    @property
    def unique_id(self):
        """Return unique_id."""
        return self._unique_id

    def scheduled_connection(self, forced_refresh_period):
        """Return False if Connection needs to be updated."""
        try:
            if self._forced_refresh_countdown <= 0 or self._departure == "":
                self._forced_refresh_countdown = (
                    forced_refresh_period if forced_refresh_period > 0 else 1
                )
                return False
            departure_time = datetime.strptime(self._departure, "%H:%M").time()
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
                    self._forced_refresh_countdown -= 1
                    return True
                else:
                    self._forced_refresh_countdown = forced_refresh_period
                    return False
        except:
            return False  # Refresh data on Error

    def update_status(
        self, departure, duration, state, connections, description, detail, delay
    ):
        """Update the status from parameters."""
        self._departure = departure
        self._duration = duration
        self._state = state
        self._connections = connections
        self._description = description
        self._detail = detail
        self._delay = delay

    def load_defaults(self):
        """Initiate empty defaults."""
        self.update_status("", "", "", "", "", [[], []], "")

    async def async_added_to_hass(self):
        """Entity added. Entity ID ready"""
        self.hass.data[DOMAIN].add_entity_id(self.entity_id)
        self.hass.data[DOMAIN].add_sensor(self)
