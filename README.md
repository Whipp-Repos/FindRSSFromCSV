# FindRSSFromCSV
Quick Python to crawl sites for possible RSS Feeds from a CSV of URLs

# Usage
python3 FindRSSFromCSV.py [path-to-csv] [index-of-url-column]

# How it works
Iterates througuh &lt;link&gt; tags on the page for ones with a type that is one of the possible RSS XML feed content types

* 'application/rss+xml'
* 'application/atom+xml'
* 'application/xml'
* 'text/xml'

Iterates through &lt;a&gt; tags on the page for local links, either relative paths or absolute paths with the same domain.
Makes a request to each local url, and checks to see if the content-type returned matches any of the above possibles
RSS content types.

Iterates through any URLs that were found via the content type and visits them using [feedparser](https://pypi.org/project/feedparser/).
Extracts the title from the response and associates it with the other original URL and Feed URL, and considers it validated.

Writes all validated results to a FeindRSSFromCSV.csv

