"""Support for cz_pub_tran sensors."""
from . import Connection
import logging, json, requests
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import async_timeout
import asyncio
import random
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle, slugify
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "cz_pub_tran"
DOMAIN = "cz_pub_tran"

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
ATTR_COMBINATION_GUID = "combination_guid"

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
        res[ATTR_CONNECTIONS] = self._connections
        res[ATTR_DESCRIPTION] = self._description
        return res

    @property
    def icon(self):
        return ICON_BUS
    
    @Throttle(THROTTLE_INTERVAL)
    async def async_update(self):
        """ Call the do_update function based on scan interval and throttle    """
        today=datetime.now().date()
        now=datetime.now().time()
        if not CZPubTranSensor.guid_exist(self._combination_id):
            await CZPubTranSensor.async_update_CombinationInfo(self._combination_id,self._user_id)
            await self.async_update_Connection()
        else:
            if self._departure == "":
                await self.async_update_Connection()
            else:
                departure_time=datetime.strptime(self._departure,"%H:%M").time()
                if now > departure_time and (now.hour <= 22 or departure_time.hour >= 5):
                    await self.async_update_Connection()
                else:
                    _LOGGER.debug( "(%s) departure already secheduled for %s - not checking connections", self._name, self._departure)

    async def reserve_resource(self):
        i=0
        while self.hass.data[DOMAIN]['traffic_light']:
            await asyncio.sleep(random.randrange(2,8,1))
            i=i+1
            if i==6:
                return False
        self.hass.data[DOMAIN]['traffic_light'] = True
        await asyncio.sleep(1)
        return True
    
    def release_resource(self):
        self.hass.data[DOMAIN]['traffic_light'] = False


    async def async_update_Connection(self):

        if not CZPubTranSensor.guid_exist(self._combination_id):
            return
        url_connection = "https://ext.crws.cz/api/"+CZPubTranSensor.guid(self._combination_id)+"/connections"        
        if self._user_id=="":
            payload= {'from':self._origin, 'to':self._destination}
        else:
            payload= {'from':self._origin, 'to':self._destination,'userId':self._user_id}
        _LOGGER.debug( "(%s) Checking connection from %s to %s", self._name,self._origin,self._destination)            
        try:
            # Use traffic light to avoid concurrent access to the website
            if not await self.reserve_resource():
                return
            with async_timeout.timeout(HTTP_TIMEOUT):            
                connection_response = await self._session.get(url_connection,params=payload)
            self.release_resource()

            if connection_response is None:
                raise ErrorGettingData('No response')
            _LOGGER.debug( "(%s) url - %s",self._name,str(connection_response.url))
            if connection_response.status != 200:
                raise ErrorGettingData('API returned response code '+str(connection_response.status)+" ("+await connection_response.text()+")")
            connection_decoded = await connection_response.json()
            if connection_decoded is None:
                raise ErrorGettingData('Error passing the JSON response')
            if "handle" not in connection_decoded:
                raise ErrorGettingData('Did not find any connection from '+self._origin+" to "+self._destination)

            connection = connection_decoded["connInfo"]["connections"][0]
            _LOGGER.debug( "(%s) connection from %s to %s: found id %s",self._name,self._origin,self._destination,str(connection["id"]))
            self._duration = connection["timeLength"]
            self._departure = connection["trains"][0]["trainData"]["route"][0]["depTime"]
            connections_short=""
            connections_long=""
            first=True
            for trains in connection["trains"]:
                line=str(trains["trainData"]["info"]["num1"])
                depTime=trains["trainData"]["route"][0]["depTime"]
                depStation=trains["trainData"]["route"][0]["station"]["name"]
                if "arrTime" in trains["trainData"]["route"][1]:
                    arrTime=trains["trainData"]["route"][1]["arrTime"]
                else:
                    arrTime=trains["trainData"]["route"][1]["depTime"]
                arrStation=trains["trainData"]["route"][1]["station"]["name"]
                if first:
                    connections_short=line
                    connections_long=line+" "+depTime+" ("+depStation+") -> "+arrTime+" ("+arrStation+")"
                    first=False
                else:
                    connections_short=connections_short+"-"+depStation.replace(" (PZ)","")+"-"+line
                    connections_long=connections_long+"\n"+line+" "+depTime+" ("+depStation+") -> "+arrTime+" ("+arrStation+")"
            self._state = self._departure+" ("+connections_short+")"
            self._connections = connections_short
            self._description = connections_long
        except ErrorGettingData as e:
            _LOGGER.error( "(%s) Error getting connection: %s",self._name,e.value)
            self._state = ""
            self._duration = ""
            self._departure = ""
            self._connections = ""
            self._description = ""
        except:
            _LOGGER.error( "(%s) Exception getting connection data",self._name)
            self._state = ""
            self._duration = ""
            self._departure = ""
            self._connections = ""
            self._description = ""
