import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class PangolinApiClient:
    def __init__(self, email, password, base_url):
        self._email = email
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._session = aiohttp.ClientSession()
        self._cookies = None

    async def close(self):
        await self._session.close()

    async def authenticate(self):
        url = f"{self._base_url}/api/v1/auth/login"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-Pangolin",
            "x-csrf-token": "x-csrf-protection"
        }
        payload = {
            "email": self._email,
            "password": self._password,
            "code": ""
        }

        async with self._session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                _LOGGER.error("Failed to authenticate with Pangolin: %s", await resp.text())
                raise Exception("Authentication failed")
            self._cookies = resp.cookies

    async def get_sites(self):
        if not self._cookies:
            await self.authenticate()

        url = f"{self._base_url}/api/v1/org/home/sites"

        async with self._session.get(url, cookies=self._cookies) as resp:
            if resp.status == 401:
                _LOGGER.warning("Session expired. Re-authenticating.")
                await self.authenticate()
                # Retry after re-authentication
                async with self._session.get(url, cookies=self._cookies) as retry_resp:
                    if retry_resp.status != 200:
                        _LOGGER.error("Failed to get sites after re-authentication: %s", await retry_resp.text())
                        raise Exception("Fetching sites failed after re-authentication")
                    return await retry_resp.json()
            elif resp.status != 200:
                _LOGGER.error("Failed to get sites: %s", await resp.text())
                raise Exception("Fetching sites failed")
            return await resp.json()
