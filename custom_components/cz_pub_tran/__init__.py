"""Support for cz_pub_tran domain
The async_update connections checks all connections every minute
If the connection is scheduled, it skips the update. 
But every 5 minutes it updates all connections regardless - to check on delay
"""
from czpubtran.api import czpubtran
import logging
from homeassistant.helpers import config_validation as cv, discovery
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_NAME
)
from .constants import (
    CONNECTION_DETAIL_HEADER,
    CONNECTION_DETAIL_FOOTER,
    CONNECTION_DETAIL_LINE_DELAY,
    CONNECTION_DETAIL_LINE_NO_DELAY
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity, async_generate_entity_id
import asyncio
from homeassistant.helpers.event import async_call_later
from .sensor import (
    DOMAIN,
    CONF_USERID,
    DEFAULT_SCAN_INTERVAL,
    CONF_FORCE_REFRESH_INTERVAL,
    CONF_DETAIL_FORMAT,
    CONFIG_SCHEMA,
    COMPONENT_NAME
)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Setup the cz_pub_tran platform."""
    conf = CONFIG_SCHEMA(config).get(DOMAIN)
    user_id = conf.get(CONF_USERID)
    scan_interval = conf.get(CONF_SCAN_INTERVAL).total_seconds()
    force_refresh_interval = conf.get(CONF_FORCE_REFRESH_INTERVAL)
    detail_format=conf.get(CONF_DETAIL_FORMAT)
    session = async_get_clientsession(hass)
    hass.data[DOMAIN]= ConnectionPlatform(hass,user_id,scan_interval,force_refresh_interval,detail_format,session)
    hass.helpers.discovery.load_platform(COMPONENT_NAME,DOMAIN, conf[CONF_SENSORS], config)
    async_call_later(hass,1, hass.data[DOMAIN].async_update_Connections())
    return True

class ConnectionPlatform():
    def __init__(self,hass,user_id,scan_interval,force_refresh_interval,detail_format,session):
        self._hass = hass
        self._user_id = user_id
        self._scan_interval = scan_interval
        self._force_refresh_interval = force_refresh_interval
        self._detail_format = detail_format
        self._entity_ids = []
        self._connections = []
        self._api = czpubtran(session,user_id)

    def add_sensor(self,sensor):
        self._connections.append(sensor)

    def entity_ids(self):
        return self._entity_ids

    def add_entity_id(self,id):
        self._entity_ids.append(id)

    async def async_update_Connections(self):
        for entity in self._connections:
            if entity.scheduled_connection(self._force_refresh_interval):
                _LOGGER.debug( f'({entity._name}) departure already scheduled for {entity._departure} - not checking connections')
                continue
            if await self._api.async_find_connection(entity._origin,entity._destination,entity._combination_id):
                detail = CONNECTION_DETAIL_HEADER[self._detail_format]
                connections=''
                delay=''
                for i,trains in enumerate(self._api.connections):
                    line=trains['line']
                    depTime=trains['depTime']
                    depStation=trains['depStation']
                    arrTime=trains['arrTime']
                    arrStation=trains['arrStation']
                    depStationShort="-"+depStation.replace(" (PZ)","")+"-"
                    connections += f'{depStationShort if i>0 else ""}{line}'
                    if trains['delay'] != '':
                        detail += ('\n' if i>0 else '') + CONNECTION_DETAIL_LINE_DELAY[self._detail_format].format(line,depTime,depStation,arrTime,arrStation,trains["delay"])
                        delay += f'{"" if delay=="" else " | "}line {line} - {trains["delay"]}min delay'
                    else:
                        detail += ('\n' if i>0 else '') + CONNECTION_DETAIL_LINE_NO_DELAY[self._detail_format].format(line,depTime,depStation,arrTime,arrStation)
                detail += CONNECTION_DETAIL_FOOTER[self._detail_format]
                entity.update_status(self._api.departure,self._api.duration,self._api.departure+" ("+connections+")",connections,self._api.connections if self._detail_format=='list' else detail,delay)
            else:
                entity.update_status('','','no connection','',[] if self._detail_format=='list' else "","")
        async_call_later(self._hass, self._scan_interval, self.async_update_Connections())
