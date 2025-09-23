import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
import aiohttp

from .const import DOMAIN
from .pangolin_api import PangolinAuthError, PangolinConnectionError, PangolinAPIError


async def validate_input(hass, data):
    """Проверка логина и получения доступа к API."""
    import logging
    _LOGGER = logging.getLogger(__name__)
    
    _LOGGER.info("Starting validation with data: %s", {k: v if k != 'password' else '***' for k, v in data.items()})
    
    try:
        async with aiohttp.ClientSession() as session:
            # сначала логинимся
            login_url = f"{data['base_url'].rstrip('/')}/api/v1/auth/login"
            payload = {"email": data["email"], "password": data["password"]}
            
            _LOGGER.info("Attempting login to: %s", login_url)

            async with session.post(login_url, json=payload) as resp:
                _LOGGER.info("Login response status: %s", resp.status)
                
                if resp.status == 401:
                    _LOGGER.error("Authentication failed: Invalid credentials")
                    raise InvalidAuth
                elif resp.status >= 400:
                    response_text = await resp.text()
                    _LOGGER.error("Login failed with status %s: %s", resp.status, response_text)
                    raise CannotConnect
                
                try:
                    login_data = await resp.json()
                    _LOGGER.info("Login response data keys: %s", list(login_data.keys()) if isinstance(login_data, dict) else "Not a dict")
                except Exception as json_err:
                    _LOGGER.error("Failed to parse login response as JSON: %s", json_err)
                    raise CannotConnect

            token = login_data.get("token")
            if not token:
                _LOGGER.error("No token received in login response")
                raise InvalidAuth
            
            _LOGGER.info("Token received successfully")

            # проверяем доступ к sites
            sites_url = f"{data['base_url'].rstrip('/')}/api/v1/org/home/sites"
            headers = {"Authorization": f"Bearer {token}"}
            _LOGGER.info("Testing sites access: %s", sites_url)
            
            async with session.get(sites_url, headers=headers) as resp:
                _LOGGER.info("Sites response status: %s", resp.status)
                
                if resp.status >= 400:
                    response_text = await resp.text()
                    _LOGGER.error("Sites access failed with status %s: %s", resp.status, response_text)
                    raise CannotConnect
                
                try:
                    sites_data = await resp.json()
                    _LOGGER.info("Sites response received, data keys: %s", list(sites_data.keys()) if isinstance(sites_data, dict) else "Not a dict")
                except Exception as json_err:
                    _LOGGER.error("Failed to parse sites response as JSON: %s", json_err)
                    raise CannotConnect

    except aiohttp.ClientError as err:
        _LOGGER.error("HTTP client error during validation: %s", err)
        raise CannotConnect
    except InvalidAuth:
        _LOGGER.error("Authentication error during validation")
        raise
    except CannotConnect:
        _LOGGER.error("Connection error during validation")
        raise
    except Exception as err:
        _LOGGER.error("Unknown error during validation: %s", err, exc_info=True)
        raise UnknownError from err

    _LOGGER.info("Validation completed successfully")
    return {"title": "Pangolin Monitor"}


class PangolinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        import logging
        _LOGGER = logging.getLogger(__name__)
        
        errors = {}
        if user_input is not None:
            _LOGGER.info("User input received for config flow")
            try:
                await validate_input(self.hass, user_input)
                _LOGGER.info("Validation successful, creating config entry")
            except (CannotConnect, PangolinConnectionError) as err:
                _LOGGER.error("Connection error in config flow: %s", err)
                errors["base"] = "cannot_connect"
            except (InvalidAuth, PangolinAuthError) as err:
                _LOGGER.error("Auth error in config flow: %s", err)
                errors["base"] = "invalid_auth"
            except (UnknownError, PangolinAPIError) as err:
                _LOGGER.error("Unknown/API error in config flow: %s", err)
                errors["base"] = "unknown"
            except Exception as err:
                _LOGGER.error("Unexpected error in config flow: %s", err, exc_info=True)
                errors["base"] = "unknown"
            else:
                # сохраняем base_url/email/password в конфиг
                _LOGGER.info("Creating config entry with title: Pangolin")
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
