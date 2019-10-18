"""Adds config flow for GarbageCollection."""
from collections import OrderedDict
import logging
from homeassistant.core import callback
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from datetime import datetime
import uuid

from .constants import (
    DOMAIN,
    ENTITY_ID_FORMAT,
    ICON_BUS,
    DESCRIPTION_FORMAT_OPTIONS,
    CONF_ORIGIN,
    CONF_DESTINATION,
    CONF_USERID,
    CONF_COMBINATION_ID,
    CONF_FORCE_REFRESH_PERIOD,
    CONF_DESCRIPTION_FORMAT,
    SENSOR_SCHEMA,
)

from homeassistant.const import CONF_NAME

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class CZPubTranFlowHandler(config_entries.ConfigFlow):
    """Config flow for garbage_collection."""

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
        """

        C O N F I G U R A T I O N   S T E P   1

        """
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
        """Configuration STEP 1 - SHOW FORM"""
        # Defaults
        name = ""
        origin = ""
        destination = ""
        combination_id = ""
        if user_input is not None:
            if CONF_NAME in user_input:
                name = user_input[CONF_NAME]
            if CONF_ORIGIN in user_input:
                origin= user_input[CONF_ORIGIN]
            if CONF_DESTINATION in user_input:
                destination = user_input[CONF_DESTINATION]
            if CONF_COMBINATION_ID in user_input:
                combination_id = user_input[CONF_COMBINATION_ID]
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_NAME, default=name)] = str
        data_schema[vol.Required(CONF_ORIGIN, default=origin)] = str
        data_schema[vol.Required(CONF_DESTINATION, default=destination)] = str
        data_schema[vol.Required(CONF_COMBINATION_ID, default=combination_id)] = str
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

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     if config_entry.options.get("unique_id", None) is not None:
    #         return OptionsFlowHandler(config_entry)
    #     else:
    #         return EmptyOptions(config_entry)



# class OptionsFlowHandler(config_entries.OptionsFlow):
#     def __init__(self, config_entry):
#         self.config_entry = config_entry
#         self._data = config_entry.options

#     async def async_step_init(self, user_input=None):
#         """

#         O P T I O N S   S T E P   1

#         """
#         self._errors = {}
#         if user_input is not None:
#             # Remember Frequency
#             self._data.update(user_input)
#             # Call next step
#             if user_input[CONF_FREQUENCY] in ANNUAL_FREQUENCY:
#                 return await self.async_step_detail_annual()
#             else:
#                 return await self.async_step_detail()
#             return await self._show_init_form(user_input)
#         return await self._show_init_form(user_input)

#     async def _show_init_form(self, user_input):
#         """Options STEP 1 - SHOW FORM"""
#         # Defaults
#         data_schema = OrderedDict()
#         data_schema[
#             vol.Required(
#                 CONF_FREQUENCY, default=self.config_entry.options.get(CONF_FREQUENCY)
#             )
#         ] = vol.In(FREQUENCY_OPTIONS)
#         data_schema[
#             vol.Required(
#                 CONF_ICON_NORMAL,
#                 default=self.config_entry.options.get(CONF_ICON_NORMAL),
#             )
#         ] = str
#         data_schema[
#             vol.Required(
#                 CONF_ICON_TOMORROW,
#                 default=self.config_entry.options.get(CONF_ICON_TOMORROW),
#             )
#         ] = str
#         data_schema[
#             vol.Required(
#                 CONF_ICON_TODAY,
#                 default=self.config_entry.options.get(CONF_ICON_TOMORROW),
#             )
#         ] = str
#         data_schema[
#             vol.Required(
#                 CONF_VERBOSE_STATE,
#                 default=self.config_entry.options.get(CONF_VERBOSE_STATE),
#             )
#         ] = bool
#         return self.async_show_form(
#             step_id="init", data_schema=vol.Schema(data_schema), errors=self._errors
#         )

#     async def async_step_detail(
#         self, user_input={}
#     ):  # pylint: disable=dangerous-default-value
#         """

#         O P T I O N S   S T E P   2

#         """
#         self._errors = {}
#         if user_input is not None and user_input != {}:
#             day_selected = False
#             detail_info = {}
#             detail_info[CONF_COLLECTION_DAYS] = []
#             for day in WEEKDAYS:
#                 if user_input[f"collection_days_{day.lower()}"]:
#                     day_selected = True
#                     detail_info[CONF_COLLECTION_DAYS].append(day)
#             if day_selected:
#                 # Remember Detail
#                 self._data.update(detail_info)
#                 # Call last step
#                 return await self.async_step_final()
#             else:
#                 self._errors["base"] = "days"
#         return await self._show_detail_form(user_input)

#     async def _show_detail_form(self, user_input):
#         """Configuration STEP 2 - SHOW FORM"""
#         data_schema = OrderedDict()
#         for day in WEEKDAYS:
#             data_schema[
#                 vol.Required(
#                     f"collection_days_{day.lower()}",
#                     default=bool(
#                         day.lower()
#                         in self.config_entry.options.get(CONF_COLLECTION_DAYS)
#                     ),
#                 )
#             ] = bool
#         return self.async_show_form(
#             step_id="detail", data_schema=vol.Schema(data_schema), errors=self._errors
#         )

#     async def async_step_detail_annual(
#         self, user_input={}
#     ):  # pylint: disable=dangerous-default-value
#         """

#         C O N F I G U R A T I O N   S T E P   2a

#         """
#         self._errors = {}
#         if user_input is not None and user_input != {}:
#             if is_month_day(user_input[CONF_DATE]):
#                 # Remember Frequency
#                 self._data.update(user_input)
#                 # Call last step
#                 return self.async_create_entry(title="", data=self._data)
#             else:
#                 self._errors["base"] = "month_day"
#         return await self._show_detail_annual_form(user_input)

#     async def _show_detail_annual_form(self, user_input):
#         """Configuration STEP 2a - SHOW FORM"""
#         # Defaults
#         data_schema = OrderedDict()
#         data_schema[
#             vol.Optional(CONF_DATE, default=self.config_entry.options.get(CONF_DATE))
#         ] = str
#         return self.async_show_form(
#             step_id="detail_annual",
#             data_schema=vol.Schema(data_schema),
#             errors=self._errors,
#         )

#     async def async_step_final(
#         self, user_input={}
#     ):  # pylint: disable=dangerous-default-value
#         """

#         C O N F I G U R A T I O N   S T E P   3

#         """
#         self._errors = {}
#         if user_input is not None and user_input != {}:
#             final_info = {}
#             final_info[CONF_FIRST_MONTH] = user_input[CONF_FIRST_MONTH]
#             final_info[CONF_LAST_MONTH] = user_input[CONF_LAST_MONTH]
#             if self._data[CONF_FREQUENCY] in MONTHLY_FREQUENCY:
#                 day_selected = False
#                 final_info[CONF_WEEKDAY_ORDER_NUMBER] = []
#                 for i in range(4):
#                     if user_input[f"weekday_order_number_{i+1}"]:
#                         day_selected = True
#                         final_info[CONF_WEEKDAY_ORDER_NUMBER].append(i + 1)
#                 if not day_selected:
#                     self._errors["base"] = CONF_WEEKDAY_ORDER_NUMBER
#             final_info[CONF_INCLUDE_DATES] = string_to_list(
#                 user_input[CONF_INCLUDE_DATES]
#             )
#             final_info[CONF_EXCLUDE_DATES] = string_to_list(
#                 user_input[CONF_EXCLUDE_DATES]
#             )
#             if not is_dates(final_info[CONF_INCLUDE_DATES]) or not is_dates(
#                 final_info[CONF_EXCLUDE_DATES]
#             ):
#                 self._errors["base"] = "date"
#             if self._data[CONF_FREQUENCY] in WEEKLY_FREQUENCY_X:
#                 final_info[CONF_PERIOD] = user_input[CONF_PERIOD]
#                 final_info[CONF_FIRST_WEEK] = user_input[CONF_FIRST_WEEK]
#             if self._errors == {}:
#                 self._data.update(final_info)
#                 return self.async_create_entry(title="", data=self._data)
#         return await self._show_final_form(user_input)

#     async def _show_final_form(self, user_input):
#         """Configuration STEP 3 - SHOW FORM"""
#         data_schema = OrderedDict()
#         data_schema[
#             vol.Optional(
#                 CONF_FIRST_MONTH,
#                 default=self.config_entry.options.get(CONF_FIRST_MONTH),
#             )
#         ] = vol.In(MONTH_OPTIONS)
#         data_schema[
#             vol.Optional(
#                 CONF_LAST_MONTH,
#                 default=self.config_entry.options.get(CONF_LAST_MONTH),
#             )
#         ] = vol.In(MONTH_OPTIONS)
#         if self._data[CONF_FREQUENCY] in WEEKLY_FREQUENCY_X:
#             data_schema[
#                 vol.Required(
#                     CONF_PERIOD, default=self.config_entry.options.get(CONF_PERIOD)
#                 )
#             ] = vol.All(vol.Coerce(int), vol.Range(min=1, max=52))
#             data_schema[
#                 vol.Required(
#                     CONF_FIRST_WEEK,
#                     default=self.config_entry.options.get(CONF_FIRST_WEEK),
#                 )
#             ] = vol.All(vol.Coerce(int), vol.Range(min=1, max=52))
#         if self._data[CONF_FREQUENCY] in MONTHLY_FREQUENCY:
#             for i in range(4):
#                 data_schema[
#                     vol.Required(
#                         f"weekday_order_number_{i+1}",
#                         default=bool(
#                             i
#                             in self.config_entry.options.get(CONF_WEEKDAY_ORDER_NUMBER)
#                         ),
#                     )
#                 ] = bool
#         data_schema[
#             vol.Optional(
#                 CONF_INCLUDE_DATES,
#                 default=",".join(self.config_entry.options.get(CONF_INCLUDE_DATES)),
#             )
#         ] = str
#         data_schema[
#             vol.Optional(
#                 CONF_EXCLUDE_DATES,
#                 default=",".join(self.config_entry.options.get(CONF_EXCLUDE_DATES)),
#             )
#         ] = str
#         return self.async_show_form(
#             step_id="final", data_schema=vol.Schema(data_schema), errors=self._errors
#         )


# class EmptyOptions(config_entries.OptionsFlow):
#     def __init__(self, config_entry):
#         self.config_entry = config_entry
