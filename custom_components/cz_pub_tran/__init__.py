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
    """Setup the sensor platform."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]['traffic_light'] = False
    hass.data[DOMAIN]['combination_ids'] = {}
    # for sensor in base_config['sensor']:
    #     if sensor['platform'] == 'cz_pub_tran':
            # _LOGGER.debug( "(cz_pub_tran init) Found entity: "+ sensor['name'])
            # _LOGGER.debug( "(cz_pub_tran init) Sensor entity: "+ str(sensor))
    return True


class My_Entity(Entity):
    """Representation of a device entity. Will pass to binary_sensor and others"""

    def __init__(self, my_device):
        """Initialize the device."""        
        
    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        _LOGGER.debug( "(cz_pub_tran init) Entity {} added".format(self.entity_id))
