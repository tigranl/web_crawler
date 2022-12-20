import asyncio
from urllib.parse import urlparse
from typing import Dict, Optional, Any

import aiohttp

http_client_pool: Dict[str, aiohttp.ClientSession] = {}


class MaxRetries(Exception):
    ...


class HttpClient:
    def __init__(
        self,
        headers=None,
        verify_ssl=False,
        timeout=5.0,
        max_retry=1,
        sleep=0.1,
        max_connections=10,
    ):

        self.headers: Optional[Dict[str, Any]] = headers
        self.verify_ssl: bool = verify_ssl
        self.timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=timeout)

        self.max_connections: int = max_connections
        self.max_retry: int = max_retry

        self.sleep: float = sleep

    def _get_client(self, url: str):
        base_url = self._get_base_url(url)

        kwargs = {
            "timeout": self.timeout,
            "connector": aiohttp.TCPConnector(
                verify_ssl=self.verify_ssl,
                limit=self.max_connections,
            ),
        }

        if self.headers:
            kwargs["headers"] = self.headers

        client = http_client_pool.get(base_url)

        if not client:
            client = aiohttp.ClientSession(**kwargs)
            http_client_pool[base_url] = client

        return client

    async def request(self, method: str, url: str, **kwargs):

        client = self._get_client(url)

        for _ in range(self.max_retry):
            try:
                response = await client.request(method, url, **kwargs)
                return response
            except aiohttp.ClientResponseError as e:
                if not self.is_server_error(e.status):
                    raise e
                await asyncio.sleep(self.sleep)

        raise MaxRetries("Maximum number of attempts tried")

    async def get(self, url: str, **kwargs: Any):
        return await self.request('GET', url, **kwargs)

    async def post(self, url: str, **kwargs: Any):
        return await self.request('POST', url, **kwargs)

    @staticmethod
    async def close_connections():
        for connection in http_client_pool.values():
            await connection.close()
        http_client_pool.clear()

    @staticmethod
    def is_server_error(status: int):
        return 500 <= status <= 599

    @staticmethod
    def _get_base_url(url: str):
        parse = urlparse(url)
        return f'{parse.scheme}://{parse.netloc}'

