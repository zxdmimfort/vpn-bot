import datetime
import json
from uuid import uuid4
import aiohttp
import random
import string

from schemas import Response, SClient, SInbound


class APIClient:
    def __init__(
        self, base_url: str, username: str, password: str, inbound_id: int
    ) -> None:
        self.username = username
        self.password = password
        self.base_url = base_url
        self.inbound_id = inbound_id
        self.session = aiohttp.ClientSession()

    async def login(self) -> dict:
        payload = {"username": self.username, "password": self.password}
        async with self.session.post(
            f"{self.base_url}/login", json=payload
        ) as response:
            response.raise_for_status()
            data = await response.json()
            # Cookies from the response are automatically stored in self.session.cookie_jar.
            return data

    async def request(self, method: str, url: str, **kwargs):
        async with self.session.request(method, url, **kwargs) as response:
            content_type = response.headers.get("Content-Type", "")
            # If the response status is 401 or returns HTML (expired cookies), refresh cookies.
            if response.status == 401 or "text" in content_type:
                print(
                    "Cookies expired or received unexpected HTML, refreshing cookies."
                )
                await self.login()  # refresh cookies
                async with self.session.request(
                    method, url, **kwargs
                ) as retry_response:
                    retry_response.raise_for_status()
                    return await retry_response.json()
            response.raise_for_status()
            return await response.json()

    async def get_inbound(self) -> SInbound | None:
        response = await self.request(
            "GET", f"{self.base_url}/panel/api/inbounds/get/{self.inbound_id}"
        )
        resp = Response.model_validate(response)
        return resp.obj  # now always returns a value

    def create_link(self, client: SClient, inbound: SInbound) -> str | None:
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

    async def get_connection_by_email(self, email: str) -> str | None:
        inbound = await self.get_inbound()
        if not inbound:
            return None
        for client in inbound.settings.clients:
            if email == client.email:
                return self.create_link(client, inbound)
        return None

    async def add_connection(
        self,
        username: str,
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
                                "tgId": "",
                                "subId": sub_id_random,
                                "comment": "",
                                "reset": 0,
                            }
                        ]
                    }
                ),
            }
        )

        response = await self.request(
            "POST",
            f"{self.base_url}/panel/inbound/addClient",
            data=form_data,
        )
        if response.get("success"):
            return email
        return None

    async def close(self) -> None:
        await self.session.close()
