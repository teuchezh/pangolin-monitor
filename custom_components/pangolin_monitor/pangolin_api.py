import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)


class PangolinApiClient:
    def __init__(self, email: str, password: str, base_url: str) -> None:
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.session: aiohttp.ClientSession | None = None
        self.token: str | None = None

    async def authenticate(self) -> None:
        """Аутентификация и получение токена."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/api/v1/auth/login"
        payload = {"email": self.email, "password": self.password}

        async with self.session.post(url, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("Auth failed: %s", text)
                raise Exception(f"Authentication failed: {resp.status}")
            data = await resp.json()
            self.token = data.get("token")

        if not self.token:
            raise Exception("No token received during authentication")

    async def get_sites(self) -> dict:
        """Получение информации о сайтах (туннелях, трафике, статусах)."""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/api/v1/org/home/sites"
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                _LOGGER.error("Failed to get sites: %s", text)
                raise Exception(f"Get sites failed: {resp.status}")
            payload = await resp.json()

        sites = payload.get("data", {}).get("sites", [])
        result = []
        for site in sites:
            result.append({
                "id": site.get("siteId"),
                "name": site.get("name"),
                "type": site.get("type"),
                "in_mb": site.get("megabytesIn"),
                "out_mb": site.get("megabytesOut"),
                "online": site.get("online"),
                "subnet": site.get("subnet"),
                "address": site.get("address"),
                "version": site.get("newtVersion"),
                "update": site.get("newtUpdateAvailable"),
            })

        return {"sites": result}

    async def close(self) -> None:
        """Закрыть HTTP-сессию."""
        if self.session:
            await self.session.close()
            self.session = None
