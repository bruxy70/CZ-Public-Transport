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
    hass.data[DOMAIN]['entity_ids'] = []
    hass.data[DOMAIN]['entities'] = {}
    return True


class My_Entity(Entity):
    """Representation of a device entity. Will pass to binary_sensor and others"""

    def __init__(self,hass,name):
        """Initialize the device."""
        self.entity_id=async_generate_entity_id('sensor.{}',name,hass.data[DOMAIN]['entity_ids'])
        hass.data[DOMAIN]['entity_ids'].append(self.entity_id)
        self._name2 = name
        _LOGGER.debug( "(cz_pub_tran init) Entity {} inicialized".format(self.entity_id))
        
    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self.hass.data[DOMAIN]['entities'][self.entity_id] = {}
        self.hass.data[DOMAIN]['entities'][self.entity_id]['last_updated'] = None
        self.hass.data[DOMAIN]['entities'][self.entity_id]['data_changed'] = False
        self.hass.data[DOMAIN]['entities'][self.entity_id]['duration'] = ""
        self.hass.data[DOMAIN]['entities'][self.entity_id]['departure'] = ""
        self.hass.data[DOMAIN]['entities'][self.entity_id]['connection'] = ""
        self.hass.data[DOMAIN]['entities'][self.entity_id]['description'] = ""
        self.hass.data[DOMAIN]['entities'][self.entity_id]['state'] = ""
        # self._origin = origin
        # self._destination = destination
        # self._combination_id = combination_id
        _LOGGER.debug( "(cz_pub_tran init) Entity {} added".format(self.entity_id))
