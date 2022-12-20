import asyncio

from django.views.generic import FormView

from crawler.forms import CrawlerUrlForm
from crawler.crawler import Crawler
from web_crawler.core.http_client import HttpClient


class CrawlerView(FormView):
    template_name = "index.html"
    form_class = CrawlerUrlForm

    def form_valid(self, form):
        data = self.get_crawler_data(form.cleaned_data['url'])
        return self.render_to_response(
            self.get_context_data(
                urls=data["urls"], error_msg=data["error_msg"]
            )
        )

    def get_crawler_data(self, url):
        crawler = Crawler(http_client=HttpClient())

        urls = []
        error = None
        try:
            urls = asyncio.run(crawler.crawl(base_url=url))
        except Exception as e:
            error = str(e)

        return {"urls": urls, "error_msg": error}
