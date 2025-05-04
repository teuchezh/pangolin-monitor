import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

class PangolinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Pangolin", data=user_input)

        schema = vol.Schema({
            vol.Required("base_url"): str,
            vol.Required("email"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PangolinOptionsFlowHandler(config_entry)

class PangolinOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required("base_url", default=self.config_entry.data.get("base_url")): str,
            vol.Required("email", default=self.config_entry.data.get("email")): str,
            vol.Required("password", default=self.config_entry.data.get("password")): str,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
