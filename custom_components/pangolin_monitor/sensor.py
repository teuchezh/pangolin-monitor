from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .pangolin_api import PangolinApiClient

async def async_setup_entry(hass, entry, async_add_entities):
    api: PangolinApiClient = hass.data[DOMAIN][entry.entry_id]
    data = await api.get_sites()

    sensors = []
    for site in data.get("data", {}).get("sites", []):
        sensors.append(PangolinTunnelSensor(site))

    async_add_entities(sensors, update_before_add=True)

class PangolinTunnelSensor(SensorEntity):
    def __init__(self, site):
        self._attr_name = f"Pangolin Tunnel {site['name']}"
        self._attr_unique_id = f"pangolin_tunnel_{site['siteId']}"
        self._site = site

    @property
    def state(self):
        return "online" if self._site.get("online") else "offline"

    @property
    def extra_state_attributes(self):
        return {
            "name": self._site.get("name"),
            "site_id": self._site.get("siteId"),
            "nice_id": self._site.get("niceId"),
            "subnet": self._site.get("subnet"),
            "megabytes_in": self._site.get("megabytesIn"),
            "megabytes_out": self._site.get("megabytesOut"),
            "type": self._site.get("type")
        }
