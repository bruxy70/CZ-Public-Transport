"""Support for cz_pub_tran domain"""
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
HTTP_TIMEOUT = 5

async def async_setup(hass, base_config):
    """Setup the sensor platform."""
    Connection.session = async_get_clientsession(hass)
    async_call_later(hass,10, Connection.async_update_Connections())
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
    def guid(combination_id):
        if combination_id in CombinationID.combination_ids:
            return CombinationID.combination_ids[combination_id].guid
        else:
            _LOGGER.error("GUID for combination ID %s not found!",combination_id)
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
        if self._departure == "":
            return False
        departure_time=datetime.strptime(self._departure,"%H:%M").time()
        now=datetime.now().time()
        if now < departure_time or ( now.hour> 22 and departure_time < 6 ):
            return True
        else:
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
        self._duration = ""
        self._departure = ""
        self._connections = ""
        self._description = ""
        self._state = ""
        self.entity_id=async_generate_entity_id(ENTITY_ID_FORMAT,name,Connection.entity_ids)
        Connection.entity_ids.append(self.entity_id)
        _LOGGER.debug("Entity %s inicialized",self.entity_id)
        
    async def async_added_to_hass(self):
        """I probably do not need this! To be removed! Call when entity is added to hass."""
        Connection.connections.append(self)
        _LOGGER.debug( "Entity %s added",self.entity_id)


    @staticmethod
    async def async_update_CombinationInfo(combination_id,user_id):
        if CombinationID.guid_exist(combination_id):
            return True
        url_combination  = 'https://ext.crws.cz/api/'
        _LOGGER.debug( "Updating CombinationInfo guid %s",combination_id)
        if user_id=="":
            payload = {}
        else:
            payload= {'userId':user_id}
        combination_guid = None
        guid_valid_to = None
        try:
            with async_timeout.timeout(HTTP_TIMEOUT):            
                combination_response = await Connection.session.get(url_combination,params=payload)
            if combination_response is None:
                raise ErrorGettingData('Response timeout')
            _LOGGER.debug( "url - %s",str(combination_response.url))
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
                    _LOGGER.debug( "found guid %s valid till %s",combination["guid"],datetime.strptime(combination["ttValidTo"], "%d.%m.%Y").date())
                    return True
        except ErrorGettingData as e:
            _LOGGER.error( "Error getting CombinatonInfo: %s",e.value)
        except:
            _LOGGER.error( "Exception reading guid data")
        return False

    @staticmethod
    async def async_update_Connections():
        for entity in Connection.connections:
            if not CombinationID.guid_exist(entity._combination_id):
                if not await Connection.async_update_CombinationInfo(entity._combination_id,entity._user_id):
                    continue
            if entity.scheduled_connection():
                _LOGGER.debug( "(%s) departure already secheduled for %s - not checking connections", entity._name, entity._departure)
                continue
            url_connection = "https://ext.crws.cz/api/"+CombinationID.guid(entity._combination_id)+"/connections"
            if entity._user_id=="":
                payload= {'from':entity._origin, 'to':entity._destination}
            else:
                payload= {'from':entity._origin, 'to':entity._destination,'userId':entity._user_id}
            _LOGGER.debug( "(%s) Checking connection from %s to %s", entity._name,entity._origin,entity._destination)            
            try:
                with async_timeout.timeout(HTTP_TIMEOUT):            
                    connection_response = await Connection.session.get(url_connection,params=payload)

                if connection_response is None:
                    raise ErrorGettingData('Response timeout')
                _LOGGER.debug( "(%s) url - %s",entity._name,str(connection_response.url))
                if connection_response.status != 200:
                    raise ErrorGettingData(f'API returned response code {connection_response.status} ({await connection_response.text()})')
                connection_decoded = await connection_response.json()
                if connection_decoded is None:
                    raise ErrorGettingData('Error passing the JSON response')
                if "handle" not in connection_decoded:
                    raise ErrorGettingData('Did not find any connection from '+entity._origin+" to "+entity._destination)

                connection = connection_decoded["connInfo"]["connections"][0]
                _LOGGER.debug( "(%s) connection from %s to %s: found id %s",entity._name,entity._origin,entity._destination,str(connection["id"]))
                entity._duration = connection["timeLength"]
                entity._departure = connection["trains"][0]["trainData"]["route"][0]["depTime"]
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
                        connections_long=f'{line:<4} {depTime:<5} ({depStation}) -> {arrTime:<5} ({arrStation})'
                        first=False
                    else:
                        connections_short=connections_short+"-"+depStation.replace(" (PZ)","")+"-"+line
                        connections_long=connections_long+'\n'+f'{line:<4} {depTime:<5} ({depStation}) -> {arrTime:<5} ({arrStation})'
                entity._state = entity._departure+" ("+connections_short+")"
                entity._connections = connections_short
                entity._description = connections_long
            except ErrorGettingData as e:
                _LOGGER.error( "(%s) Error getting connection: %s",entity._name,e.value)
                entity._state = ""
                entity._duration = ""
                entity._departure = ""
                entity._connections = ""
                entity._description = ""
            except:
                _LOGGER.error( "(%s) Exception getting connection data",entity._name)
                entity._state = ""
                entity._duration = ""
                entity._departure = ""
                entity._connections = ""
                entity._description = ""
        async_call_later(Connection.hass, SCAN_INTERVAL, Connection.async_update_Connections())
