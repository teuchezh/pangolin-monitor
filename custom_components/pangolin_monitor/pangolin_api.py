import aiohttp
import logging
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


class PangolinAuthError(HomeAssistantError):
    """Ошибка аутентификации Pangolin."""


class PangolinConnectionError(HomeAssistantError):
    """Ошибка соединения с Pangolin."""


class PangolinAPIError(HomeAssistantError):
    """Ошибка API Pangolin."""


class PangolinApiClient:
    def __init__(self, email: str, password: str, base_url: str, org: str) -> None:
        """
        Initialize the Pangolin API client with credentials, base URL, and organization.
        
        Parameters:
            email (str): Account email used for authentication.
            password (str): Account password used for authentication.
            base_url (str): Base URL of the Pangolin API; trailing slash will be removed.
            org (str): Organization identifier used to scope API requests.
        
        """
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.org = org
        self.session: aiohttp.ClientSession | None = None
        self.token: str | None = None

    async def authenticate(self) -> None:
        """Аутентификация и получение токена."""
        _LOGGER.info("Starting authentication for email: %s", self.email)
        _LOGGER.info("Base URL: %s", self.base_url)
        
        if self.session is None:
            self.session = aiohttp.ClientSession()
            _LOGGER.info("Created new HTTP session")

        # Выполняем логин с фиксированным CSRF токеном
        login_url = f"{self.base_url}/api/v1/auth/login"
        headers = {
            "Content-Type": "application/json",
            "X-CSRF-Token": "x-csrf-protection"
        }
        payload = {"email": self.email, "password": self.password}
        _LOGGER.info("Login URL: %s", login_url)
        _LOGGER.info("Using fixed CSRF token: x-csrf-protection")

        try:
            async with self.session.post(login_url, json=payload, headers=headers) as resp:
                _LOGGER.info("Login response status: %s", resp.status)
                
                if resp.status == 401:
                    _LOGGER.error("Authentication failed: Invalid credentials")
                    raise PangolinAuthError("Invalid credentials")
                elif resp.status >= 400:
                    text = await resp.text()
                    _LOGGER.error("Auth failed with status %s: %s", resp.status, text)
                    raise PangolinAPIError(f"Authentication failed: {resp.status}")
                
                try:
                    data = await resp.json()
                    _LOGGER.info("Login response data keys: %s", list(data.keys()) if isinstance(data, dict) else "Not a dict")
                    _LOGGER.info("Full login response: %s", data)
                except Exception as json_err:
                    _LOGGER.error("Failed to parse login response as JSON: %s", json_err)
                    raise PangolinAPIError("Invalid JSON response from server")
                
                # Проверяем успешность логина
                if isinstance(data, dict) and data.get("success") and not data.get("error"):
                    _LOGGER.info("Login successful according to response")
                    # Токен передается через cookie, не через JSON
                    self.token = "cookie_based_auth"
                    _LOGGER.info("Using cookie-based authentication")
                else:
                    _LOGGER.error("Login failed according to response: %s", data)
                    raise PangolinAuthError("Login failed according to server response")
                
            _LOGGER.info("Authentication successful")
            
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error during authentication: %s", err)
            raise PangolinConnectionError(f"Connection error: {err}")

    async def get_sites(self) -> dict:
        """
        Retrieve and normalize site information for the configured organization.
        
        Requests the organization-scoped sites endpoint, parses the JSON payload, and returns a list of sites with selected fields (id, name, type, in_mb, out_mb, online, subnet, address, version, update).
        
        Returns:
            dict: A dictionary with a single key "sites" whose value is a list of site dictionaries. Each site dictionary contains:
                - id: site identifier (from `siteId`)
                - name: site name (from `name`)
                - type: site type (from `type`)
                - in_mb: incoming traffic in megabytes (from `megabytesIn`)
                - out_mb: outgoing traffic in megabytes (from `megabytesOut`)
                - online: online status (from `online`)
                - subnet: subnet information (from `subnet`)
                - address: site address (from `address`)
                - version: software/version string (from `newtVersion`)
                - update: whether an update is available (from `newtUpdateAvailable`)
        
        Raises:
            PangolinAuthError: If authentication is invalid or expired (HTTP 401) or the server indicates login problems.
            PangolinAPIError: If the API returns a 4xx/5xx status (other than 401) or the response is not valid JSON.
            PangolinConnectionError: If an underlying network/client error occurs while making the request.
        """
        _LOGGER.info("Getting sites data")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
            _LOGGER.info("Created new HTTP session for get_sites")

        url = f"{self.base_url}/api/v1/org/{self.org}/sites"
        headers = {}
        _LOGGER.info("Sites URL: %s", url)
        _LOGGER.info("Using cookie-based authentication: %s", "Yes" if self.token == "cookie_based_auth" else "No")

        try:
            async with self.session.get(url, headers=headers) as resp:
                _LOGGER.info("Sites response status: %s", resp.status)
                
                if resp.status == 401:
                    _LOGGER.error("Authentication failed when getting sites - token expired or invalid")
                    raise PangolinAuthError("Token expired or invalid")
                elif resp.status >= 400:
                    text = await resp.text()
                    _LOGGER.error("Failed to get sites with status %s: %s", resp.status, text)
                    raise PangolinAPIError(f"Get sites failed: {resp.status}")
                
                try:
                    payload = await resp.json()
                    _LOGGER.info("Sites response data keys: %s", list(payload.keys()) if isinstance(payload, dict) else "Not a dict")
                except Exception as json_err:
                    _LOGGER.error("Failed to parse sites response as JSON: %s", json_err)
                    raise PangolinAPIError("Invalid JSON response from sites endpoint")
                    
        except aiohttp.ClientError as err:
            _LOGGER.error("Connection error when getting sites: %s", err)
            raise PangolinConnectionError(f"Connection error: {err}")

        sites = payload.get("data", {}).get("sites", [])
        _LOGGER.info("Found %d sites in response", len(sites))
        
        result = []
        for site in sites:
            site_data = {
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
            }
            result.append(site_data)
            _LOGGER.info("Processed site: %s (ID: %s, Online: %s)", 
                        site_data.get("name"), site_data.get("id"), site_data.get("online"))

        _LOGGER.info("Returning %d processed sites", len(result))
        return {"sites": result}

    async def close(self) -> None:
        """Закрыть HTTP-сессию."""
        if self.session:
            await self.session.close()
            self.session = None