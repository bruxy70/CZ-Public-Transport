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
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'cz_pub_tran'

async def async_setup(hass, base_config):
    """Setup the sensor platform."""
    hass.data[DOMAIN] = False
    return True
