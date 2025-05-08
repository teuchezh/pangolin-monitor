import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
import aiohttp

from .const import DOMAIN

async def validate_input(hass, data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data['base_url']}/api/v1/org/home/sites", cookies={}) as resp:
                if resp.status == 401:
                    raise InvalidAuth
                elif resp.status >= 400:
                    raise CannotConnect
    except aiohttp.ClientError:
        raise CannotConnect
    except Exception as err:
        raise UnknownError from err

    return {"title": "Pangolin Monitor"}

class PangolinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except UnknownError:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Pangolin", data=user_input)

        schema = vol.Schema({
            vol.Required("base_url"): str,
            vol.Required("email"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

class CannotConnect(HomeAssistantError):
    pass

class InvalidAuth(HomeAssistantError):
    pass

class UnknownError(HomeAssistantError):
    pass
