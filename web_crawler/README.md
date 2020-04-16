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
```

## Data Storage

Currently using local DynamoDB instance, but can easily be integrated with AWS remote DynamoDB by changing the ```endpoint_url``` argument when accessing database.