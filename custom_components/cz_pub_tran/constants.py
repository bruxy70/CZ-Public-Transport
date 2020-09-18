"""Text constants for cz_pub_tran sensor."""

from datetime import date, datetime, time, timedelta

import voluptuous as vol
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
)
from homeassistant.helpers import config_validation as cv

DESCRIPTION_HEADER = {
    "text": "",
    "HTML": "<table>\n"
    "<tr>"
    '<th align="left">Line</th>'
    '<th align="left">Departure</th>'
    '<th align="left">From</th>'
    '<th align="left">Arrival</th>'
    '<th align="left">To</th>'
    '<th align="left">Delay</th>'
    "</tr>",
}

DESCRIPTION_LINE_DELAY = {
    "text": "{:<4} {:<5} ({}) -> {:<5} ({})   !!! {}min delayed",
    "HTML": "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}min</td></tr>",
}

DESCRIPTION_LINE_NO_DELAY = {
    "text": "{:<4} {:<5} ({}) -> {:<5} ({})",
    "HTML": "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td></td></tr>",
}

DESCRIPTION_FOOTER = {"text": "", "HTML": "\n</table>"}

DOMAIN = "cz_pub_tran"
PLATFORM = "sensor"
VERSION = "0.0.1"
ISSUE_URL = "https://github.com/bruxy70/CZ-Public-Transport/issues"
ATTRIBUTION = "Data from this is provided by cz_pub_tran."

ENTITY_ID_FORMAT = PLATFORM + ".{}"

ICON_BUS = "mdi:bus"

DESCRIPTION_FORMAT_OPTIONS = ["HTML", "text"]

CONF_ORIGIN = "origin"
CONF_DESTINATION = "destination"
CONF_USERID = "userId"
CONF_COMBINATION_ID = "combination_id"
CONF_FORCE_REFRESH_PERIOD = "force_refresh_period"
CONF_DESCRIPTION_FORMAT = "description_format"

ATTR_DURATION = "duration"
ATTR_DEPARTURE = "departure"
ATTR_CONNECTIONS = "connections"
ATTR_DESCRIPTION = "description"
ATTR_DETAIL = "detail"
ATTR_START_TIME = "start_time"
ATTR_DELAY = "delay"

TRACKABLE_DOMAINS = ["sensor"]

DEFAULT_SCAN_INTERVAL = timedelta(seconds=60)
DEFAULT_FORCE_REFRESH_PERIOD = 5
DEFAULT_DESCRIPTION_FORMAT = "text"
DEFAULT_COMBINATION_ID = "ABCz"
DEFAULT_NAME = "cz_pub_tran"

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_ORIGIN): cv.string,
        vol.Required(CONF_DESTINATION): cv.string,
        vol.Optional(CONF_COMBINATION_ID, default=DEFAULT_COMBINATION_ID): cv.string,
    }
)

SET_START_TIME_SCHEMA = vol.Schema(
    {vol.Optional(ATTR_START_TIME): cv.time, vol.Required(CONF_ENTITY_ID): cv.string}
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_USERID, default=""): cv.string,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): cv.time_period,
                vol.Optional(
                    CONF_DESCRIPTION_FORMAT, default=DEFAULT_DESCRIPTION_FORMAT
                ): vol.In(DESCRIPTION_FORMAT_OPTIONS),
                vol.Optional(
                    CONF_FORCE_REFRESH_PERIOD, default=DEFAULT_FORCE_REFRESH_PERIOD
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)
