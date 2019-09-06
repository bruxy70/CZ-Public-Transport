"""Support for cz_pub_tran domain
The async_update connections checks all connections every minute
If the connection is scheduled, it skips the update. 
But every 5 minutes it updates all connections regardless - to check on delay
"""

from . import (
    CZPubTranSensor,
    CONF_ORIGIN,
    CONF_DESTINATION,
    CONF_USERID,
    CONF_COMBINATION_ID,
)
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_NAME
)
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
import logging, json, requests
from datetime import datetime, date, time, timedelta
import asyncio
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'cz_pub_tran'
COMPONENT_NAME = 'sensor'
DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_COMBINATION_ID = "ABCz"
DEFAULT_NAME = "cz_pub_tran"

ENTITY_ID_FORMAT = COMPONENT_NAME + ".{}"
FORCED_REFRESH_COUNT = 5
HTTP_TIMEOUT = 5

SENSOR_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_ORIGIN): cv.string,
    vol.Required(CONF_DESTINATION): cv.string,
    vol.Optional(CONF_COMBINATION_ID, default=DEFAULT_COMBINATION_ID): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_USERID,default=""): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period,
        vol.Optional(CONF_SENSORS, default={}): SENSOR_SCHEMA,
    })
})

async def async_setup(hass, config):
    """Setup the sensor platform."""
    user_id = config.get(CONF_USERID)
    scan_interval = config.get(CONF_SCAN_INTERVAL).total_seconds()
    hass.data[DOMAIN]= ConnectionPlatform(user_id,scan_interval,session)

    discovery.load_platform(hass, COMPONENT_NAME, DOMAIN, conf[CONF_SENSORS], config)
    async_call_later(hass,1, hass.data[DOMAIN].async_update_Connections())
    return True

class ConnectionPlatform(Entity):
    def __init__(self,user_id,scan_interval,session):
        self._user_id = user_id
        self._scan_interval = scan_interval
        self._session = session
        self._entity_ids = []
        self._connections = []

    def add_sensor(self,sensor):
        self._connections.append(self,sensor)

    def entity_ids(self):
        return self._entity_ids

    def add_entity_if(self,id):
        self._entity_ids.append(id)

    async def async_update_CombinationInfo(self,combination_id):
        if CombinationID.guid_exist(combination_id):
            return True
        url_combination  = 'https://ext.crws.cz/api/'
        _LOGGER.debug( f'Updating CombinationInfo guid {combination_id}')
        if self._user_id=="":
            payload = {}
        else:
            payload= {'userId':self._user_id}
        try:
            with async_timeout.timeout(HTTP_TIMEOUT):            
                combination_response = await self._session.get(url_combination,params=payload)
            if combination_response is None:
                raise ErrorGettingData('Response timeout')
            _LOGGER.debug( f'url - {combination_response.url}')
            if combination_response.status != 200:
                raise ErrorGettingData(f'API returned response code {combination_response.status} ({await combination_response.text()})')
            combination_decoded = await combination_response.json()
            if combination_decoded is None:
                raise ErrorGettingData('Error passing the JSON response')
            if "data" not in combination_decoded:
                raise ErrorGettingData('API returned no data')
            for combination in combination_decoded["data"]:
                if combination["id"] == combination_id:
                    CombinationID.clean_combination_ids(combination_id)
                    CombinationID.combination_ids[combination["id"]]=(CombinationID(combination["guid"],datetime.strptime(combination["ttValidTo"], "%d.%m.%Y").date()))
                    _LOGGER.debug( f"found guid {combination['guid']} valid till {datetime.strptime(combination['ttValidTo'], '%d.%m.%Y').date()}")
                    return True
        except ErrorGettingData as e:
            _LOGGER.error( f'Error getting CombinatonInfo: {e.value}')
        except:
            _LOGGER.error( 'Exception reading guid data')
        return False

    async def async_update_Connections(self):
        for entity in self._connections:
            if not CombinationID.guid_exist(entity._combination_id):
                if not await Connection.async_update_CombinationInfo(entity._combination_id,self._user_id):
                    continue
            if entity.scheduled_connection():
                _LOGGER.debug( f'({entity._name}) departure already scheduled for {entity._departure} - not checking connections')
                continue
            url_connection = f'https://ext.crws.cz/api/{CombinationID.get_guid(entity._combination_id)}/connections'
            if self._user_id=="":
                payload= {'from':entity._origin, 'to':entity._destination}
            else:
                payload= {'from':entity._origin, 'to':entity._destination,'userId':self._user_id}
            _LOGGER.debug( f'({entity._name}) Checking connection from {entity._origin} to {entity._destination}')            
            try:
                with async_timeout.timeout(HTTP_TIMEOUT):            
                    connection_response = await self._session.get(url_connection,params=payload)

                if connection_response is None:
                    raise ErrorGettingData('Response timeout')
                _LOGGER.debug( f'({entity._name}) url - {str(connection_response.url)}')
                if connection_response.status != 200:
                    raise ErrorGettingData(f'API returned response code {connection_response.status} ({await connection_response.text()})')
                connection_decoded = await connection_response.json()
                if connection_decoded is None:
                    raise ErrorGettingData('Error passing the JSON response')
                if "handle" not in connection_decoded:
                    raise ErrorGettingData(f'Did not find any connection from {entity._origin} to {entity._destination}')

                connection = connection_decoded["connInfo"]["connections"][0]
                _LOGGER.debug( f"({entity._name}) connection from {entity._origin} to {entity._destination}: found id {str(connection['id'])}")
                duration = connection["timeLength"]
                departure = connection["trains"][0]["trainData"]["route"][0]["depTime"]
                connections_short=''
                connections_long=''
                delay=''
                long_delim=''
                for trains in connection["trains"]:
                    line=str(trains["trainData"]["info"]["num1"])
                    depTime=trains["trainData"]["route"][0]["depTime"]
                    depStation=trains["trainData"]["route"][0]["station"]["name"]
                    if "arrTime" in trains["trainData"]["route"][1]:
                        arrTime=trains["trainData"]["route"][1]["arrTime"]
                    else:
                        arrTime=trains["trainData"]["route"][1]["depTime"]
                    arrStation=trains["trainData"]["route"][1]["station"]["name"]
                    if long_delim=='':
                        connections_short=line
                    else:
                        connections_short=connections_short+"-"+depStation.replace(" (PZ)","")+"-"+line
                    if 'delay' in trains and trains['delay'] >0:
                        connections_long=connections_long+long_delim+f'{line:<4} {depTime:<5} ({depStation}) -> {arrTime:<5} ({arrStation})   !!! {trains["delay"]}min delayed'
                        if delay=='':
                            delay = f'line {line} - {trains["delay"]}min delay'
                        else:
                            delay = delay + f' | line {line} - {trains["delay"]}min delay'
                    else:
                        connections_long=connections_long+long_delim+f'{line:<4} {depTime:<5} ({depStation}) -> {arrTime:<5} ({arrStation})'
                    long_delim='\n'
                entity.update_status(departure,duration,departure+" ("+connections_short+")",connections_short,connections_long,delay)
            except ErrorGettingData as e:
                _LOGGER.error( f'({entity._name}) Error getting connection: {e.value}')
                entity.load_defaults()
            except:
                _LOGGER.error( f'({entity._name}) Exception getting connection data')
                entity.load_defaults()
        async_call_later(self.hass, self._scan_interval, self.async_update_Connections())

class ErrorGettingData(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
