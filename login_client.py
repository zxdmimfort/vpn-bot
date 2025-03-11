import json
from uuid import uuid4
import aiohttp
import random
import string


class APIClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.username = username
        self.password = password
        self.base_url = base_url
        self.login_url = base_url + "login"
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
            if response.status == 401 or "text/html" in content_type:
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

    async def get_all_clients_of_inbound(self, inbound: int) -> dict:
        return await self.request(
            "GET", f"{self.base_url}/panel/api/inbounds/get/{inbound}"
        )

    async def add_connection(self, inbound: int, username: str) -> dict:
        uuid = str(uuid4())
        email_id: str = uuid.replace("-", "")[:10]
        email = f"{username}-{email_id}"

        sub_id_random = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=18)
        )
        form_data = aiohttp.FormData(
            {
                "id": inbound,
                "settings": json.dumps(
                    {
                        "clients": [
                            {
                                "id": uuid,
                                "flow": "xtls-rprx-vision",
                                "email": email,
                                "limitIp": 5,
                                "totalGB": 0,
                                "expiryTime": 0,
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

        return await self.request(
            "POST",
            f"{self.base_url}/panel/inbound/addClient",
            data=form_data,
        )

    async def close(self) -> None:
        await self.session.close()
