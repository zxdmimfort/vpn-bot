from typing import Any, Awaitable, Callable
from aiogram.types import TelegramObject
from app.login_client import APIClient


class ApiClientMiddleware:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        data["api_client"] = self.api_client
        return await handler(event, data)
