# FindRSSFromCSV
Quick Python to crawl sites for possible RSS Feeds from a CSV of URLs

# Usage
python3 FindRSSFromCSV.py [path-to-csv] [index-of-url-column]

# How it works

Checks domain name against a few known patterns for Blogspot, tumblr, and Medium, since those don't need any parsing, so skips the rest of the process.

Builds possible subdomains, just 'feed' right now.

Adds possible paths both to the base domain name and the path if the passed URL isn't just the base domain name.

* '/feed'
* '/rss.xml'
* '/xml/rss/all.xml'
* '/rss'
* '/.rss'
* '/xml/rss.xml'
* '/xml/rss/rss.xml'

Iterates through &lt;link&gt; tags on the page for ones with a type that is one of the possible RSS XML feed content types.

* 'application/rss+xml'
* 'application/atom+xml'
* 'application/xml'
* 'text/xml'

Iterates through &lt;a&gt; tags on the page for local links, either relative paths or absolute paths with the same domain.
Makes a request to each local url, and checks to see if the content-type returned matches any of the above possibles
RSS content types.

Iterates through any URLs that were found via the content type and visits them using [feedparser](https://pypi.org/project/feedparser/).
Extracts the title from the response and associates it with the other original URL and Feed URL, and considers it validated.

Writes all validated results to a FindRSSFromCSV.csv

