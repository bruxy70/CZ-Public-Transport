"""Support for cz_pub_tran domain
The async_update connections checks all connections every minute
If the connection is scheduled, it skips the update. 
But every 5 minutes it updates all connections regardless - to check on delay
"""

import logging, json, requests
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import async_timeout
import asyncio
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_call_later

_LOGGER = logging.getLogger(__name__)
DOMAIN = 'sensor'
SCAN_INTERVAL = 60
ENTITY_ID_FORMAT = DOMAIN + ".{}"
FORCED_REFRESH_COUNT = 5
HTTP_TIMEOUT = 5

async def async_setup(hass, base_config):
    """Setup the sensor platform."""
    Connection.session = async_get_clientsession(hass)
    async_call_later(hass,1, Connection.async_update_Connections())
    return True

class CombinationID():
    combination_ids = {}
    def __init__(self,guid,validTo):
        self.validTo = validTo
        self.guid=guid
    
    @staticmethod
    def guid_exist(combination_id):
        if combination_id in CombinationID.combination_ids:
            today=datetime.now().date()
            if CombinationID.combination_ids[combination_id].validTo >= today:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def get_guid(combination_id):
        if combination_id in CombinationID.combination_ids:
            return CombinationID.combination_ids[combination_id].guid
        else:
            _LOGGER.error(f'GUID for combination ID {combination_id} not found!')
            return ''

    @staticmethod
    def clean_combination_ids(combination_id):
        if combination_id in CombinationID.combination_ids:
            del CombinationID[combination_id]

class ErrorGettingData(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Connection(Entity):
    """Representation of a device entity. Will pass to binary_sensor and others"""
    entity_ids = []
    connections = []
    session = None
    hass = None

    def scheduled_connection(self):
        if self._departure == "" or self.forced_refresh_countdown <= 0:
            self.forced_refresh_countdown = FORCED_REFRESH_COUNT
            return False
        departure_time=datetime.strptime(self._departure,"%H:%M").time()
        now=datetime.now().time()
        if now < departure_time or ( now.hour> 22 and departure_time < 6 ):
            self.forced_refresh_countdown = self.forced_refresh_countdown - 1
            return True
        else:
            self.forced_refresh_countdown = FORCED_REFRESH_COUNT
            return False

    def __init__(self,hass,session, name, origin, destination,combination_id,user_id):
        """Initialize the device."""
        Connection.hass = hass
        self._session = session
        self._name = name
        self._origin = origin
        self._destination = destination
        self._combination_id = combination_id
        self._user_id = user_id
        self._lastupdated = None
        self._forced_refresh_countdown = 0
        self.load_defaults()
        self.entity_id=async_generate_entity_id(ENTITY_ID_FORMAT,name,Connection.entity_ids)
        Connection.entity_ids.append(self.entity_id)
        _LOGGER.debug(f'Entity {self.entity_id} inicialized')
    
    def load_defaults(self):
        self._state = ""
        self._delay = ""
        self._duration = ""
        self._departure = ""
        self._connections = ""
        self._description = ""
        
    async def async_added_to_hass(self):
        """I probably do not need this! To be removed! Call when entity is added to hass."""
        Connection.connections.append(self)
        _LOGGER.debug(f'Entity {self.entity_id} added')


    @staticmethod
    async def async_update_CombinationInfo(combination_id,user_id):
        if CombinationID.guid_exist(combination_id):
            return True
        url_combination  = 'https://ext.crws.cz/api/'
        _LOGGER.debug( f'Updating CombinationInfo guid {combination_id}')
        if user_id=="":
            payload = {}
        else:
            payload= {'userId':user_id}
        try:
            with async_timeout.timeout(HTTP_TIMEOUT):            
                combination_response = await Connection.session.get(url_combination,params=payload)
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

    @staticmethod
    async def async_update_Connections():
        for entity in Connection.connections:
            if not CombinationID.guid_exist(entity._combination_id):
                if not await Connection.async_update_CombinationInfo(entity._combination_id,entity._user_id):
                    continue
            if entity.scheduled_connection():
                _LOGGER.debug( f'({entity._name}) departure already scheduled for {entity._departure} - not checking connections')
                continue
            url_connection = f'https://ext.crws.cz/api/{CombinationID.get_guid(entity._combination_id)}/connections'
            if entity._user_id=="":
                payload= {'from':entity._origin, 'to':entity._destination}
            else:
                payload= {'from':entity._origin, 'to':entity._destination,'userId':entity._user_id}
            _LOGGER.debug( f'({entity._name}) Checking connection from {entity._origin} to {entity._destination}')            
            try:
                with async_timeout.timeout(HTTP_TIMEOUT):            
                    connection_response = await Connection.session.get(url_connection,params=payload)

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
                entity._duration = connection["timeLength"]
                entity._departure = connection["trains"][0]["trainData"]["route"][0]["depTime"]
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
                entity._state = entity._departure+" ("+connections_short+")"
                entity._connections = connections_short
                entity._description = connections_long
                entity._delay = delay
            except ErrorGettingData as e:
                _LOGGER.error( f'({entity._name}) Error getting connection: {e.value}')
                entity.load_defaults()
            except:
                _LOGGER.error( f'({entity._name}) Exception getting connection data')
                entity.load_defaults()
        async_call_later(Connection.hass, SCAN_INTERVAL, Connection.async_update_Connections())
