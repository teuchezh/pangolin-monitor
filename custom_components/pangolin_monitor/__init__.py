import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .pangolin_api import PangolinApiClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Настройка интеграции Pangolin Monitor через config entry."""
    base_url = entry.data["base_url"]
    email = entry.data["email"]
    password = entry.data["password"]

    api = PangolinApiClient(email, password, base_url)
    await api.authenticate()

    async def async_update_data():
        """Функция, которая будет вызываться координатором каждые 5 минут."""
        return await api.get_sites()  # метод в pangolin_api.py должен возвращать JSON с сайтами

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="pangolin_monitor",
        update_method=async_update_data,
        update_interval=timedelta(minutes=5),
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
