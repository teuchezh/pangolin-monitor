import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
import aiohttp

from .const import DOMAIN
from .pangolin_api import PangolinAuthError, PangolinConnectionError, PangolinAPIError


async def validate_input(hass, data):
    """Проверка логина и получения доступа к API."""
    try:
        async with aiohttp.ClientSession() as session:
            # сначала логинимся
            login_url = f"{data['base_url'].rstrip('/')}/api/v1/auth/login"
            payload = {"email": data["email"], "password": data["password"]}

            async with session.post(login_url, json=payload) as resp:
                if resp.status == 401:
                    raise InvalidAuth
                elif resp.status >= 400:
                    raise CannotConnect
                login_data = await resp.json()

            token = login_data.get("token")
            if not token:
                raise InvalidAuth

            # проверяем доступ к sites
            sites_url = f"{data['base_url'].rstrip('/')}/api/v1/org/home/sites"
            headers = {"Authorization": f"Bearer {token}"}
            async with session.get(sites_url, headers=headers) as resp:
                if resp.status >= 400:
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
            except (CannotConnect, PangolinConnectionError):
                errors["base"] = "cannot_connect"
            except (InvalidAuth, PangolinAuthError):
                errors["base"] = "invalid_auth"
            except (UnknownError, PangolinAPIError):
                errors["base"] = "unknown"
            else:
                # сохраняем base_url/email/password в конфиг
                return self.async_create_entry(title="Pangolin", data=user_input)

        schema = vol.Schema({
            vol.Required("base_url"): str,
            vol.Required("email"): str,
            vol.Required("password"): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class CannotConnect(HomeAssistantError):
    """Ошибка соединения."""


class InvalidAuth(HomeAssistantError):
    """Ошибка авторизации."""


class UnknownError(HomeAssistantError):
    """Неизвестная ошибка."""
