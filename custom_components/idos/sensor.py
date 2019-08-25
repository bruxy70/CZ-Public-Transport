"""Support for IDOS sensors."""
import logging, json, requests
from requests import get
from datetime import datetime, date, time, timedelta

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.util import Throttle
from homeassistant.const import (
    CONF_NAME
)
from homeassistant.core import HomeAssistant, State
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "idos"

ICON_BUS = "mdi:bus"

CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_NAME = "name"
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

TRACKABLE_DOMAINS = ["sensor"]

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    origin = config[CONF_ORIGIN]
    destination = config[CONF_DESTINATION]
    name = config.get(CONF_NAME)
    combination_id = config.get(CONF_COMBINATION_ID)
    user_id = config.get(CONF_USERID)
    add_devices([IdosSensor(hass, name, origin, destination,combination_id,user_id)])

class IdosSensor(Entity):
    """Representation of a openroute service travel time sensor."""
    def __init__(self, hass, name, origin, destination,combination_id,user_id):
        """Initialize the sensor."""
        self._hass = hass
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
    def update(self):
        """ Call the do_update function based on scan interval and throttle    """
        self.do_update("Scan Interval")

    def do_update(self, reason):
        """Get the latest data and updates the states."""
        _LOGGER.info( "(" + self._name + ") Calling update due to " + reason )

        update_guid = True
        if self._combination_guid != None:
            today=datetime.now().date()
            if self._guid_valid_to > today:
                update_guid = False
        
        if update_guid:
            url_combination  = 'https://ext.crws.cz/api/'
            combination_decoded = {}
            _LOGGER.info( "(" + self._name + ") Updating CombinationInfo guid")
            if self._user_id=="":
                try:
                    combination_response = get(url_combination)
                    _LOGGER.debug( "(" + self._name + ") url - " + combination_response.url)
                except:
                    _LOGGER.info( "(" + self._name + ") Exception reading guid data")
            else:
                payload= {'userId':self._user_id}
                try:
                    combination_response = get(url_combination,params=payload)
                    _LOGGER.debug( "(" + self._name + ") url - " + combination_response.url)
                except:
                    _LOGGER.info( "(" + self._name + ") Exception reading guid data")

            if combination_response.status_code == 200:
                combination_json_input = combination_response.text
                # _LOGGER.debug( "(" + self._name + ") response - " + combination_json_input)
                combination_decoded = json.loads(combination_json_input)
                if "data" in combination_decoded:
                    try:
                        for combination in combination_decoded["data"]:
                            if combination["id"] == self._combination_id:
                                self._combination_guid = combination["guid"]
                                self._guid_valid_to = datetime.strptime(combination["ttValidTo"], "%d.%m.%Y").date()
                                _LOGGER.debug( "(" + self._name + ") found guid - " + self._combination_guid +" valid to "+self._guid_valid_to.strftime("%d-%m-%Y"))
                    except:
                        _LOGGER.error( "(" + self._name + ") Exception parsing guid")
                else:
                    _LOGGER.error( "(" + self._name + ") Reading guid - API returned no data")
            else:
                _LOGGER.error( "(" + self._name + ") Reading guid - API returned code " + str(combination_response.status_code))
        else:
            _LOGGER.debug( "(" + self._name + ") guid valid until " + self._guid_valid_to.strftime("%d-%m-%Y") + " - not updating")
        
        update_connection = True
        if self._combination_guid == None:
            _LOGGER.error( "(" + self._name + ") No CombinationInfo guid - not checking connections")
            update_connection = False
            self._state = ""
            self._duration = ""
            self._departure = ""
            self._connections = ""
            self._description = ""
        else:
            if self._departure != "":
                now=datetime.now().time()
                departure_time=datetime.strptime(self._departure,"%H:%M").time()
                if now < departure_time or (now.hour>=22 and departure_time.hour<=5):
                    _LOGGER.info( "(" + self._name + ") departure already secheduled for "+ self._departure +" - not checking connections")
                    update_connection = False

        if update_connection:
            url_connection = "https://ext.crws.cz/api/"+self._combination_guid+"/connections"
            if self._user_id=="":
                payload= {'from':self._origin, 'to':self._destination}
            else:
                payload= {'from':self._origin, 'to':self._destination,'userId':self._user_id}
            _LOGGER.info( "(" + self._name + ") Checking connection from "+ self._origin+" to "+self._destination)            
            try:
                connection_response = get(url_connection,params=payload)
                _LOGGER.debug( "(" + self._name + ") url - " + connection_response.url)
            except:
                _LOGGER.error( "(" + self._name + ") Exception reading connection data")

            if connection_response.status_code == 200:
                connection_json_input = connection_response.text
                # _LOGGER.debug( "(" + self._name + ") response - " + connection_json_input)
                connection_decoded = json.loads(connection_json_input)

                if "handle" in connection_decoded:
                    try:
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
                                connections_long=connections_long+"</br>\n"+line+" "+depTime+" ("+depStation+") -> "+arrTime+" ("+arrStation+")"
                        self._state = self._departure+" ("+connections_short+")"
                        self._connections = connections_short
                        self._description = connections_long
                    except:
                        _LOGGER.error( "(" + self._name + ") Exception parsing connecton")
                        self._state = ""
                        self._duration = ""
                        self._departure = ""
                        self._connections = ""
                        self._description = ""
                else:
                    _LOGGER.error( "(" + self._name + ") connection from "+self._origin+" to "+self._destination+ " not found!")
                    self._state = ""
                    self._duration = ""
                    self._departure = ""
                    self._connections = ""
                    self._description = ""
            else:
                _LOGGER.error( "(" + self._name + ") Reading connection data - API returned code " + str(connection_response.status_code))
                self._state = ""
                self._duration = ""
                self._departure = ""
                self._connections = ""
                self._description = ""

