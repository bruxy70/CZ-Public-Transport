"""Support for cz_pub_tran sensors."""
import logging, json, requests
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import async_timeout
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
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
ATTR_COMBINATION_GUID = "combination_guid"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ORIGIN): cv.string,
    vol.Required(CONF_DESTINATION): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_COMBINATION_ID, default=DEFAULT_COMBINATION_ID): cv.string,
    vol.Optional(CONF_USERID,default=""): cv.string,
})

SCAN_INTERVAL = timedelta(seconds=60)
THROTTLE_INTERVAL = timedelta(seconds=60)
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
    async_add_entities([CZPubTranSensor(name, origin, destination,combination_id,user_id)],True)


class CZPubTranSensor(Entity):
    """Representation of a openroute service travel time sensor."""
    def __init__(self, name, origin, destination,combination_id,user_id):
        """Initialize the sensor."""
        self._name = name
        self._origin = origin
        self._destination = destination
        self._combination_id = combination_id
        self._user_id = user_id
        self._combination_guid = None
        self._guid_valid_to = None
        self._lastupdated = None
        self._duration = ""
        self._departure = ""
        self._connections = ""
        self._description = ""
        self._state = ""

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
        res[ATTR_COMBINATION_GUID] = self._combination_guid
        return res

    @property
    def icon(self):
        return ICON_BUS
    
    @Throttle(THROTTLE_INTERVAL)
    async def async_update(self):
        """ Call the do_update function based on scan interval and throttle    """
        today=datetime.now().date()
        now=datetime.now().time()
        if self._combination_guid == None or self._guid_valid_to <= today:
            await self.async_update_CombinationInfo()
        else:
            _LOGGER.debug( "(" + self._name + ") guid valid until " + self._guid_valid_to.strftime("%d-%m-%Y") + " - not updating")
            if self._departure == "":
                await self.async_update_Connection()
            else:
                departure_time=datetime.strptime(self._departure,"%H:%M").time()
                if now > departure_time and (now.hour <= 22 or departure_time.hour >= 5):
                    await self.async_update_Connection()
                else:
                    _LOGGER.info( "(" + self._name + ") departure already secheduled for "+ self._departure +" - not checking connections")


    async def async_update_CombinationInfo(self):
        url_combination  = 'https://ext.crws.cz/api/'
        _LOGGER.info( "(" + self._name + ") Updating CombinationInfo guid")
        self._combination_guid = None
        self._guid_valid_to = None
        if self._user_id=="":
            payload = {}
        else:
            payload= {'userId':self._user_id}
        session = async_get_clientsession(self.hass)
        self._combination_guid = None
        self._guid_valid_to = None
        try:
            with async_timeout.timeout(HTTP_TIMEOUT):            
                combination_response = await session.get(url_combination,params=payload)
            if combination_response is None:
                raise ErrorGettingData('No response')
            _LOGGER.debug( "(" + self._name + ") url - " + str(combination_response.url))
            if combination_response.status != 200:
                raise ErrorGettingData('API returned response code '+str(combination_response.status)+" ("+await combination_response.text()+")" )
            combination_decoded = await combination_response.json()
            if combination_decoded is None:
                raise ErrorGettingData('Error passing the JSON response')
            if "data" not in combination_decoded:
                raise ErrorGettingData('API returned no data')
            for combination in combination_decoded["data"]:
                if combination["id"] == self._combination_id:
                    self._combination_guid = combination["guid"]
                    self._guid_valid_to = datetime.strptime(combination["ttValidTo"], "%d.%m.%Y").date()
                    _LOGGER.debug( "(" + self._name + ") found guid - " + self._combination_guid +" valid till "+self._guid_valid_to.strftime("%d-%m-%Y"))
        except ErrorGettingData as e:
            _LOGGER.error( "(" + self._name + ") Error getting CombinatonInfo: "+ e.value)
        except:
            _LOGGER.error( "(" + self._name + ") Exception reading guid data")
        if self._combination_guid is None:
            self._state = ""
            self._duration = ""
            self._departure = ""
            self._connections = ""
            self._description = ""

    async def async_update_Connection(self):
        if self._combination_guid is None:
            return
        url_connection = "https://ext.crws.cz/api/"+self._combination_guid+"/connections"        
        if self._user_id=="":
            payload= {'from':self._origin, 'to':self._destination}
        else:
            payload= {'from':self._origin, 'to':self._destination,'userId':self._user_id}
        _LOGGER.info( "(" + self._name + ") Checking connection from "+ self._origin+" to "+self._destination)            
        session = async_get_clientsession(self.hass)
        self._combination_guid = None
        self._guid_valid_to = None
        try:
            with async_timeout.timeout(HTTP_TIMEOUT):            
                connection_response = await session.get(url_connection,params=payload)
            if connection_response is None:
                raise ErrorGettingData('No response')
            _LOGGER.debug( "(" + self._name + ") url - " + str(connection_response.url))
            if connection_response.status != 200:
                raise ErrorGettingData('API returned response code '+str(connection_response.status)+" ("+await connection_response.text()+")")
            connection_decoded = await connection_response.json()
            if connection_decoded is None:
                raise ErrorGettingData('Error passing the JSON response')
            if "handle" not in connection_decoded:
                raise ErrorGettingData('Did not find any connection from '+self._origin+" to "+self._destination)

            connection = connection_decoded["connInfo"]["connections"][0]
            _LOGGER.info( "(" + self._name + ") connection from "+self._origin+" to "+self._destination+ ": id"+str(connection["id"]))
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
            _LOGGER.error( "(" + self._name + ") Error getting connection: "+ e.value)
            self._state = ""
            self._duration = ""
            self._departure = ""
            self._connections = ""
            self._description = ""
        except:
            _LOGGER.error( "(" + self._name + ") Exception getting connection data")
            self._state = ""
            self._duration = ""
            self._departure = ""
            self._connections = ""
            self._description = ""
