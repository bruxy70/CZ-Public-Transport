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

HTTP_TIMEOUT = 5

async def async_setup(hass, base_config):
    """Setup the sensor platform."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN]['traffic_light'] = False
    hass.data[DOMAIN]['combination_ids'] = {}
    Connection.session = async_get_clientsession(hass)
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


class Connection(Entity):

    """Representation of a device entity. Will pass to binary_sensor and others"""
    entity_ids = []
    connections = []
    session = None

    @staticmethod
    def guid_exist(combination_id):
        return CombinationID.guid_exist(combination_id)

    @staticmethod
    def guid(combination_id):
        return CombinationID.guid(combination_id)

    def __init__(self,hass,session, name, origin, destination,combination_id,user_id):
        """Initialize the device."""
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
        self.entity_id=async_generate_entity_id('sensor.{}',name,Connection.entity_ids)
        Connection.entity_ids.append(self.entity_id)
        _LOGGER.debug("Entity %s inicialized",self.entity_id)
        
    async def async_added_to_hass(self):
        """I probably do not need this! To be removed! Call when entity is added to hass."""
        Connection.connections.append(self)
        _LOGGER.debug( "Entity %s added",self.entity_id)

    class ErrorGettingData(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)

    @staticmethod
    async def async_update_CombinationInfo(combination_id,user_id):
        if CombinationID.guid_exist(combination_id):
            return
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
                raise ErrorGettingData('No response')
            _LOGGER.debug( "url - %s",str(combination_response.url))
            if combination_response.status != 200:
                raise ErrorGettingData('API returned response code '+str(combination_response.status)+" ("+await combination_response.text()+")" )
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
        except ErrorGettingData as e:
            _LOGGER.error( "Error getting CombinatonInfo: %s",e.value)
        except:
            _LOGGER.error( "Exception reading guid data")