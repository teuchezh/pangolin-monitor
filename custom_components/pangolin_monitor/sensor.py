import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Создание сенсоров при загрузке интеграции."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []
    sites = coordinator.data.get("sites", []) if coordinator.data else []

    for site in sites:
        site_id = site["id"]
        site_name = site["name"]

        entities.append(SiteTrafficInSensor(coordinator, site_id, site_name))
        entities.append(SiteTrafficOutSensor(coordinator, site_id, site_name))
        entities.append(SiteOnlineSensor(coordinator, site_id, site_name))

    async_add_entities(entities)


class BasePangolinSensor(CoordinatorEntity, SensorEntity):
    """Базовый класс сенсора Pangolin."""

    def __init__(self, coordinator, site_id, site_name):
        super().__init__(coordinator)
        self.site_id = site_id
        self.site_name = site_name

    def _get_site(self):
        sites = self.coordinator.data.get("sites", []) if self.coordinator.data else []
        for site in sites:
            if site["id"] == self.site_id:
                return site
        return None


class SiteTrafficInSensor(BasePangolinSensor):
    @property
    def name(self):
        return f"{self.site_name} Traffic In"

    @property
    def unique_id(self):
        return f"pangolin_{self.site_id}_traffic_in"

    @property
    def native_unit_of_measurement(self):
        return "MB"

    @property
    def native_value(self):
        site = self._get_site()
        return site.get("in_mb") if site else None


class SiteTrafficOutSensor(BasePangolinSensor):
    @property
    def name(self):
        return f"{self.site_name} Traffic Out"

    @property
    def unique_id(self):
        return f"pangolin_{self.site_id}_traffic_out"

    @property
    def native_unit_of_measurement(self):
        return "MB"

    @property
    def native_value(self):
        site = self._get_site()
        return site.get("out_mb") if site else None


class SiteOnlineSensor(BasePangolinSensor):
    @property
    def name(self):
        return f"{self.site_name} Online"

    @property
    def unique_id(self):
        return f"pangolin_{self.site_id}_online"

    @property
    def device_class(self):
        return "connectivity"

    @property
    def native_value(self):
        site = self._get_site()
        return "online" if site and site.get("online") else "offline"
