from bs4 import BeautifulSoup
from web_crawler.core.http_client import HttpClient
from logging import getLogger, Logger
from urllib.parse import urljoin

from asyncio import Queue


class Crawler:
    def __init__(
        self, http_client: HttpClient, logger: Logger | None = getLogger(__name__)
    ) -> None:
        self.http_client = http_client
        self.logger = logger
        self.queue = Queue()

    async def crawl(self, base_url: str, max_depth: int = 3) -> set[str]:
        try:
            return await self._run(base_url, max_depth)
        except Exception as e:
            self.logger.error(f"Error while crawling links – {str(e)}")
            raise e
        finally:
            await self.http_client.close_connections()

    async def _run(self, base_url: str, max_depth: int = 3) -> set[str]:
        await self.queue.put(base_url)

        visited = {base_url}
        depth = 0

        # Perform BFS to obtain all links with respect to max depth
        while not self.queue.empty() and depth <= max_depth:
            base_url = await self.queue.get()
            page_response = await self.get_page(base_url)
            page_links = self.get_links_on_page(base_url, page_response)

            for link in page_links:
                if link not in visited:
                    visited.add(link)
                    await self.queue.put(link)
            depth += 1

        return visited

    async def get_page(self, url: str) -> str | None:
        response = await self.http_client.get(url)
        if response.status == 200:
            return await response.text()

    def get_links_on_page(self, url: str, response: str | None) -> list[str]:
        if not response:
            return []

        bs = BeautifulSoup(response, "lxml")
        a_tags = bs.find_all("a", href=True)

        links = []

        for link in a_tags:
            links.append(self.process_link(url, link["href"]))

        return links

    @staticmethod
    def process_link(base_url: str, href: str) -> str:
        """
        Basic url processing
        TODO: probably would be a good idea to move this logic to a dedicated class
        Link processing might be used to validate file extensions of links
        or filter out undesirable urls
        """

        href_first_char = href[0]
        match href_first_char:
            case "/":
                return urljoin(base_url, href)
            case "#":
                return base_url
            case _:
                return href
