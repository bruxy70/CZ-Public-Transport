"""Adds config flow for cz_pub_tran."""
import logging
import uuid
from collections import OrderedDict
from datetime import datetime

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from czpubtran.api import czpubtran
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .constants import (
    CONF_COMBINATION_ID,
    CONF_DESCRIPTION_FORMAT,
    CONF_DESTINATION,
    CONF_FORCE_REFRESH_PERIOD,
    CONF_ORIGIN,
    CONF_USERID,
    DEFAULT_COMBINATION_ID,
    DESCRIPTION_FORMAT_OPTIONS,
    DOMAIN,
    ENTITY_ID_FORMAT,
    ICON_BUS,
    SENSOR_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class CZPubTranFlowHandler(config_entries.ConfigFlow):
    """Config flow for czpubtran."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self._data = {}
        self._data["unique_id"] = str(uuid.uuid4())

    async def async_step_user(
        self, user_input={}
    ):  # pylint: disable=dangerous-default-value
        """CONFIG FLOW"""
        self._errors = {}
        if user_input is not None:
            if user_input[CONF_NAME] != "":
                # Remember Frequency
                self._data.update(user_input)
                # Call next step
                return self.async_create_entry(
                    title=self._data["name"], data=self._data
                )
            else:
                self._errors["base"] = "name"
            return await self._show_user_form(user_input)
        return await self._show_user_form(user_input)

    async def _show_user_form(self, user_input):
        """SHOW FORM"""
        # Defaults
        name = ""
        origin = ""
        destination = ""
        combination_id = DEFAULT_COMBINATION_ID
        if user_input is not None:
            if CONF_NAME in user_input:
                name = user_input[CONF_NAME]
            if CONF_ORIGIN in user_input:
                origin = user_input[CONF_ORIGIN]
            if CONF_DESTINATION in user_input:
                destination = user_input[CONF_DESTINATION]
            if CONF_COMBINATION_ID in user_input:
                combination_id = user_input[CONF_COMBINATION_ID]

        pubtran = czpubtran(
            self.hass.data[DOMAIN].session, self.hass.data[DOMAIN].user_id
        )
        combination_ids = await pubtran.async_list_combination_ids()
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_NAME, default=name)] = str
        data_schema[vol.Required(CONF_ORIGIN, default=origin)] = str
        data_schema[vol.Required(CONF_DESTINATION, default=destination)] = str
        data_schema[vol.Required(CONF_COMBINATION_ID, default=combination_id)] = vol.In(
            combination_ids
        )
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_import(self, user_input):  # pylint: disable=unused-argument
        """Import a config entry.
        
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        if config_entry.options.get("unique_id", None) is not None:
            return OptionsFlowHandler(config_entry)
        else:
            return EmptyOptions(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._data = config_entry.options

    async def async_step_init(self, user_input=None):
        """OPTION FLOW"""
        self._errors = {}
        if user_input is not None:
            # Update entry
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)
        return await self._show_init_form(user_input)

    async def _show_init_form(self, user_input):
        """SHOW FORM"""
        pubtran = czpubtran(
            self.hass.data[DOMAIN].session, self.hass.data[DOMAIN].user_id
        )
        combination_ids = await pubtran.async_list_combination_ids()
        data_schema = OrderedDict()
        data_schema[
            vol.Required(
                CONF_ORIGIN, default=self.config_entry.options.get(CONF_ORIGIN)
            )
        ] = str
        data_schema[
            vol.Required(
                CONF_DESTINATION,
                default=self.config_entry.options.get(CONF_DESTINATION),
            )
        ] = str
        data_schema[
            vol.Required(
                CONF_COMBINATION_ID,
                default=self.config_entry.options.get(CONF_COMBINATION_ID),
            )
        ] = vol.In(combination_ids)
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(data_schema), errors=self._errors
        )


class EmptyOptions(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
