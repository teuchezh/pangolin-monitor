import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .pangolin_api import PangolinApiClient, PangolinAuthError, PangolinConnectionError, PangolinAPIError

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Настройка интеграции Pangolin Monitor через config entry."""
    _LOGGER.info("Setting up Pangolin Monitor integration")
    _LOGGER.info("Entry data keys: %s", list(entry.data.keys()))
    
    base_url = entry.data["base_url"]
    email = entry.data["email"]
    password = entry.data["password"]
    update_interval = entry.data.get("update_interval", 5)  # По умолчанию 5 минут
    
    _LOGGER.info("Base URL: %s", base_url)
    _LOGGER.info("Email: %s", email)
    _LOGGER.info("Update interval: %s minutes", update_interval)

    try:
        api = PangolinApiClient(email, password, base_url)
        _LOGGER.info("Created API client, attempting authentication")
        await api.authenticate()
        _LOGGER.info("Authentication successful")
    except Exception as err:
        _LOGGER.error("Failed to authenticate during setup: %s", err, exc_info=True)
        raise

    async def async_update_data():
        """Функция, которая будет вызываться координатором каждые N минут."""
        try:
            return await api.get_sites()  # метод в pangolin_api.py должен возвращать JSON с сайтами
        except PangolinAuthError as err:
            _LOGGER.error("Authentication error updating data: %s", err)
            # Запускаем reauth flow при ошибке аутентификации
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "reauth", "entry_id": entry.entry_id},
                    data=entry.data,
                )
            )
            # Возвращаем пустые данные
            return {"sites": []}
        except (PangolinConnectionError, PangolinAPIError) as err:
            _LOGGER.error("Error updating data: %s", err)
            # Возвращаем пустые данные вместо краша
            return {"sites": []}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="pangolin_monitor",
        update_method=async_update_data,
        update_interval=timedelta(minutes=update_interval),
    )

    # первая загрузка данных (важно для инициализации сенсоров)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Удаление интеграции и остановка клиента."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if data:
        api: PangolinApiClient = data["api"]
        await api.close()

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
