import datetime
import json
import logging
from uuid import uuid4
import aiohttp
import random
import string

from app.db.config import BASE_URL, DEFAULT_INBOUND, VPN_PASSWORD, VPN_USERNAME
from app.schemas import ClientStats, Response, SClient, SInbound


logger = logging.getLogger(__name__)


class APIClient:
    def __init__(
        self, base_url: str, username: str, password: str, inbound_id: int
    ) -> None:
        self.payload = {"username": username, "password": password}
        self.username = username
        self.password = password
        self.base_url = base_url
        self.inbound_id = inbound_id
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self):
        if self.session is None:
            session = aiohttp.ClientSession(base_url=self.base_url)
            self.session = session
            await self.login()
        return self.session

    async def __aenter__(self):
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self) -> None:
        if self.session:
            await self.session.close()
            self.session = None

    async def login(self) -> dict:
        if self.session is None:
            self.session = await self._get_session()
        async with self.session.post("login", json=self.payload) as response:
            response.raise_for_status()
            data = await response.json()
            # Cookies from the response are automatically stored in self.session.cookie_jar.
            return data

    async def _get(self, url: str, **kwargs) -> dict:
        if self.session is None:
            async with self:
                response = await self._request("GET", url, **kwargs)
                return response
        else:
            response = await self._request("GET", url, **kwargs)
            return response

    async def _post(self, url: str, **kwargs) -> dict:
        if self.session is None:
            async with self:
                response = await self._request("POST", url, **kwargs)
                return response
        else:
            response = await self._request("POST", url, **kwargs)
            return response

    async def request(self, method: str, url: str, **kwargs) -> dict:
        """Deprecated
        -----
        Use _get or _post instead."""
        if self.session is None:
            async with self:
                response = await self._request(method, url, **kwargs)
                return response
        else:
            response = await self._request(method, url, **kwargs)
            return response

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        if self.session is None:
            raise RuntimeError("Session is not initialized")

        request = self.session.get if method == "GET" else self.session.post

        async with request(url, **kwargs) as response:
            content_type = response.headers.get("Content-Type", "")
            # If the response status is 401 or returns HTML (expired cookies), refresh cookies.
            if response.status == 401 or "text" in content_type:
                logger.info(
                    "Cookies expired or received unexpected HTML, refreshing cookies."
                )
                await self.login()  # refresh cookies
                async with request(url, **kwargs) as retry_response:
                    retry_response.raise_for_status()
                    return await retry_response.json()
            response.raise_for_status()
            return await response.json()

    async def get_inbound_list(self) -> list[SInbound]:
        if self.session is None:
            async with self:
                response = await self._get("panel/api/inbounds/list")
        else:
            response = await self._get("panel/api/inbounds/list")

        try:
            resp = Response.model_validate(response)
        except Exception as e:
            logger.exception(f"Error parsing response: {e}")
            logger.exception(f"Response content: {response}")
            return []
        return resp.obj

    async def get_inbound(self) -> SInbound | None:
        """
        Get inbound by id.
        """
        inbounds = await self.get_inbound_list()
        inbound = next((i for i in inbounds if i.id == self.inbound_id), None)
        if not inbound:
            return None
        return inbound

    async def get_clients_stats(self) -> dict[str, ClientStats]:
        """
        Get users stats from the inbound.
        """
        inbound = await self.get_inbound()
        if not inbound:
            return {}
        stats = {}
        for client in inbound.clientStats:
            stats[client.email] = client
        return stats

    @staticmethod
    def create_link(client: SClient, inbound: SInbound) -> str | None:
        if not inbound:
            return None
        return (
            f"{inbound.protocol}://{client.id}@scvnotready.online:{inbound.port}"
            f"?type={inbound.streamSettings.network}"
            f"&security={inbound.streamSettings.security}"
            f"&pbk={inbound.streamSettings.realitySettings.settings.publicKey}"
            f"&fp={inbound.streamSettings.realitySettings.settings.fingerprint}"
            f"&sni={inbound.streamSettings.realitySettings.serverNames[0]}"
            f"&sid={inbound.streamSettings.realitySettings.shortIds[0]}"
            "&spx=%2F"
            f"&flow={client.flow}"
            f"#{inbound.remark}-{client.email}"
        )

    async def get_link_connection_by_email(self, email: str) -> str | None:
        inbound = await self.get_inbound()
        if not inbound:
            return None
        for client in inbound.settings.clients:
            if email == client.email:
                return self.create_link(client, inbound)
        return None

    async def get_connection(
        self,
        inbound: SInbound | None = None,
        uuid: str | None = None,
        email: str | None = None,
    ) -> SClient | None:
        if uuid is None and email is None:
            return None
        if inbound is None:
            inbound = await self.get_inbound()
        if not inbound:
            return None
        for client in inbound.settings.clients:
            if uuid and uuid == client.id or email and email == client.email:
                return client
        return None

    async def add_connection(
        self,
        username: str,
        tg_id: int | None = None,
        limit_ip: int = 0,
        expiry_time_days: int = 0,
    ) -> str | None:
        """
        Add a new connection to the inbound and return email string or None if failed.
        """
        uuid = str(uuid4())
        email_id: str = uuid.replace("-", "")[:10]
        email = f"{username}-{email_id}"

        sub_id_random = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=18)
        )
        expired_time = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=expiry_time_days
        )
        timestamp_time = int(expired_time.timestamp() * 1000)

        form_data = aiohttp.FormData(
            {
                "id": self.inbound_id,
                "settings": json.dumps(
                    {
                        "clients": [
                            {
                                "id": uuid,
                                "flow": "xtls-rprx-vision",
                                "email": email,
                                "limitIp": limit_ip,
                                "totalGB": 0,
                                "expiryTime": timestamp_time,
                                "enable": True,
                                "tgId": tg_id,
                                "subId": sub_id_random,
                                "comment": "",
                                "reset": 0,
                            }
                        ]
                    }
                ),
            }
        )

        response = await self._post(
            "panel/inbound/addClient",
            data=form_data,
        )
        if response.get("success"):
            return email
        return None

    async def delete_connection(self, uuid: str) -> bool:
        """
        Delete a connection by its UUID and return True if successful, False otherwise.
        """
        link = f"panel/inbound/{self.inbound_id}/delClient/{uuid}"
        response = await self._post(link)
        if response.get("success"):
            return True
        return False


def get_async_client() -> APIClient:
    return APIClient(BASE_URL, VPN_USERNAME, VPN_PASSWORD, int(DEFAULT_INBOUND))
