import scrapy
import get_links

class TestSpider(scrapy.Spider):
    name = "test"

    start_urls = get_links.get_query_links()

    def parse(self, response):
        filename = response.url.split("/")[-1] + '.html'
        with open(filename, 'wb') as f:
            f.write(response.body)