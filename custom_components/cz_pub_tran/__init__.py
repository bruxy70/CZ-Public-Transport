"""Support for cz_pub_tran domain
The async_update connections checks all connections every minute
If the connection is scheduled, it skips the update.
But every 5 minutes it updates all connections regardless - to check on delay
"""
from czpubtran.api import czpubtran
import logging
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant import config_entries
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_ENTITY_ID,
    CONF_NAME,
)
from .constants import (
    VERSION,
    ISSUE_URL,
    DESCRIPTION_HEADER,
    DESCRIPTION_FOOTER,
    DESCRIPTION_LINE_DELAY,
    DESCRIPTION_LINE_NO_DELAY,
    DOMAIN,
    CONF_USERID,
    CONF_FORCE_REFRESH_PERIOD,
    CONF_DESCRIPTION_FORMAT,
    CONFIG_SCHEMA,
    SET_START_TIME_SCHEMA,
    ATTR_START_TIME,
    PLATFORM,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.entity import Entity, async_generate_entity_id
import asyncio
from homeassistant.helpers.event import async_call_later
from integrationhelper.const import CC_STARTUP_VERSION

_LOGGER = logging.getLogger(__name__)

STATUS_NO_CONNECTION = "-"

async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""
    if config_entry.source == config_entries.SOURCE_IMPORT:
        # We get here if the integration is set up using YAML
        hass.async_create_task(hass.config_entries.async_remove(config_entry.entry_id))
        return False
    # Print startup message
    _LOGGER.info(
        CC_STARTUP_VERSION.format(name=DOMAIN, version=VERSION, issue_link=ISSUE_URL)
    )
    config_entry.options = config_entry.data
    config_entry.add_update_listener(update_listener)
    # Add sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, PLATFORM)
    )
    return True


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, PLATFORM)
        _LOGGER.info(
            "Successfully removed sensor from the garbage_collection integration"
        )
    except ValueError:
        pass

async def update_listener(hass, entry):
    """Update listener."""
    entry.data = entry.options
    await hass.config_entries.async_forward_entry_unload(entry, PLATFORM)
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, PLATFORM))

async def async_setup(hass, config):
    """Setup the cz_pub_tran platform."""
    if config.get(DOMAIN) is None:
        # We get here if the integration is set up using config flow
        return True
    conf = CONFIG_SCHEMA(config).get(DOMAIN)
    user_id = conf.get(CONF_USERID)
    scan_interval = conf.get(CONF_SCAN_INTERVAL).total_seconds()
    force_refresh_period = conf.get(CONF_FORCE_REFRESH_PERIOD)
    description_format = conf.get(CONF_DESCRIPTION_FORMAT)
    session = async_get_clientsession(hass)
    hass.data[DOMAIN] = ConnectionPlatform(
        hass, user_id, scan_interval, force_refresh_period, description_format, session
    )
    hass.helpers.discovery.load_platform(
        PLATFORM, DOMAIN, conf[CONF_SENSORS], config
    )
    hass.services.async_register(
        DOMAIN,
        "set_start_time",
        hass.data[DOMAIN].handle_set_time,
        schema=SET_START_TIME_SCHEMA,
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    async_call_later(hass, 1, hass.data[DOMAIN].async_update_Connections())
    return True

class ConnectionPlatform:
    def __init__(
        self,
        hass,
        user_id,
        scan_interval,
        force_refresh_period,
        description_format,
        session,
    ):
        self.__hass = hass
        self.__user_id = user_id
        self.__scan_interval = scan_interval
        self.__force_refresh_period = force_refresh_period
        self.__description_format = description_format
        self.__entity_ids = []
        self.__connections = []
        self.__api = czpubtran(session, user_id)

    def handle_set_time(self, call):
        """Handle the cz_pub_tran.set_time call"""
        _time = call.data.get(ATTR_START_TIME)
        _entity_id = call.data.get(CONF_ENTITY_ID)
        if _time is None:
            _LOGGER.debug(f"Received call to reset the start time in {_entity_id}")
        else:
            _LOGGER.debug(
                f"Received call to set the start time in entity {_entity_id} "
                f"to {_time}"
            )
        entity = next(
            (entity for entity in self.__connections if entity.entity_id == _entity_id),
            None,
        )
        if entity is not None:
            if _time is None:
                entity.start_time = None
            else:
                entity.start_time = _time.strftime("%H:%M")
            entity.load_defaults()
            async_call_later(self.__hass, 0, self.async_update_Connections())

    def add_sensor(self, sensor):
        self.__connections.append(sensor)

    def entity_ids(self):
        return self.__entity_ids

    def add_entity_id(self, id):
        self.__entity_ids.append(id)

    async def async_update_Connections(self):
        for entity in self.__connections:
            if entity.scheduled_connection(self.__force_refresh_period):
                # _LOGGER.debug(
                #     f'({entity.name}) departure already scheduled '
                #     f'for {entity.departure} - not checking connections'
                # )
                continue
            if await self.__api.async_find_connection(
                entity.origin,
                entity.destination,
                entity.combination_id,
                entity.start_time,
            ):
                description = DESCRIPTION_HEADER[self.__description_format]
                connections = ""
                delay = ""
                if (
                    self.__api.connection_detail is not None
                    and len(self.__api.connection_detail) >= 1
                ):
                    for i, trains in enumerate(self.__api.connection_detail[0]):
                        line = trains["line"]
                        depTime = trains["depTime"]
                        depStation = trains["depStation"]
                        arrTime = trains["arrTime"]
                        arrStation = trains["arrStation"]
                        depStationShort = "-" + depStation.replace(" (PZ)", "") + "-"
                        connections += f'{depStationShort if i > 0 else ""}{line}'
                        if trains["delay"] != "":
                            description += (
                                "\n" if i > 0 else ""
                            ) + DESCRIPTION_LINE_DELAY[
                                self.__description_format
                            ].format(
                                line,
                                depTime,
                                depStation,
                                arrTime,
                                arrStation,
                                trains["delay"],
                            )
                            delay += f'{"" if delay=="" else " | "}line {line} - {trains["delay"]}min delay'
                        else:
                            description += (
                                "\n" if i > 0 else ""
                            ) + DESCRIPTION_LINE_NO_DELAY[
                                self.__description_format
                            ].format(
                                line, depTime, depStation, arrTime, arrStation
                            )
                description += DESCRIPTION_FOOTER[self.__description_format]
                entity.update_status(
                    self.__api.departure,
                    self.__api.duration,
                    self.__api.departure + " (" + connections + ")",
                    connections,
                    description,
                    self.__api.connection_detail,
                    delay,
                )
            else:
                entity.update_status("", "", STATUS_NO_CONNECTION, "", "", None, "")
        async_call_later(
            self.__hass, self.__scan_interval, self.async_update_Connections()
        )
