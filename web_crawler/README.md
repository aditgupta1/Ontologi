# Web Crawler

Command to run web crawler:

```
scrapy crawl page_graph
```

Spider arguments:
- category: starting search query (default='tensorflow')
- nstart: number of starting links (default=10)
- save: save graphs as images in ```../test_results```

## Logging

https://docs.scrapy.org/en/latest/topics/logging.html#logging-settings

Only show error logs:

```
scrapy crawl page_graph -L ERROR
scrapy crawl page_graph -L ERROR -a save=True
```

## Data Storage

Currently using local DynamoDB instance, but can easily be integrated with AWS remote DynamoDB by changing the ```endpoint_url``` argument when accessing database.

## Deploy Scrapyd

https://www.youtube.com/watch?v=PZKH5S0C8EI

Install scrapyd:

```
pip install scrapyd-client
```

https://github.com/scrapy/scrapyd-client

```
cd web_crawler
# Start localhost
scrapyd
# Start project
scrapyd-deploy local

# Generic
curl http://localhost:6800/schedule.json -d project=myproject -d spider=somespider -d setting=DOWNLOAD_DELAY=2 -d arg1=val1
# Page Graph
curl http://localhost:6800/schedule.json -d project=web_crawler -d spider=page_graph -d url_path=urls/spider_1.txt -d save=True
```

Commands: https://scrapyd.readthedocs.io/en/latest/api.html

## Notes

BFO vs DFO
https://docs.scrapy.org/en/latest/faq.html#faq-bfo-dfo

Rotating proxies
https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/