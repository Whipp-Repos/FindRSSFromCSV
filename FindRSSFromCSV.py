#!/usr/bin/env python3

import requests as req
import feedparser as fp
import sys
import csv
import os.path
from os import path
from bs4 import BeautifulSoup as bs
from pprint import pprint as pp
from urllib.parse import urlparse
from urllib.parse import urljoin

rssApplicationTypes = ['application/rss+xml', 'application/atom+xml',
                       'application/xml', 'text/xml']

if len(sys.argv) < 3:
    message = ('FindRssFromCSV.py <path-to-csv> '
               '<URL-column-index>, FindRssFromCSV.py URL.csv 2')
    print(message)
    exit()

cssPath = sys.argv[1]
cssUrlColumn = sys.argv[2]

if not path.exists(cssPath):
    message = ('Cannot find {0}, please check that'
               ' you have the correct path.').format(cssPath)
    print(message)
    exit()

if not os.access(cssPath, os.R_OK):
    message = ('Cannot read {0}, please check that'
               ' you have the right permissions.').format(cssPath)
    print(message)
    exit()

try:
    cssUrlColumn = int(cssUrlColumn)
except ValueError:
    message = ('Please pass an integer for the column'
               ' index')
    print(message)
    exit()

urlList = []
with open(cssPath, newline='') as csvFile:
    csvReader = csv.reader(csvFile)
    try:
        urlList = [row[cssUrlColumn] for row in csvReader]
    except KeyError:
        message = ('Index {0} is not a valid index, please'
                   ' double check your csv').format(str(cssUrlColumn))
        print(message)
        exit()

foundRSSFeeds = []
for url in urlList:
    print(('Checking {0}...').format(url))
    urlParsed = urlparse(url)
    if urlParsed.netloc == '':
        print('No domain name, skipping...')
        continue
    resp = req.get(url)
    soup = bs(resp.text, 'html.parser')

    # Look for links on page that are called out as RSS Feeds
    links = soup.find_all('link')
    for link in links:
        try:
            linkType = link['type']
        except KeyError:
            continue

        try:
            linkHref = link['href']
        except KeyError:
            continue

        if linkType in rssApplicationTypes:
            linkHrefParsed = urlparse(linkHref)
            if linkHrefParsed.netloc == '':
                linkHref = urljoin(url, linkHref)
            foundRSSFeeds.append([url, linkHref])

    # Follow local links on page to see if they return a valid application Type
    alinks = soup.find_all('a')
    localLinks = []
    alinks = []
    for alink in alinks:
        try:
            href = alink['href']
        except KeyError:
            continue

        hrefParsed = urlparse(href)

        # Skip inpage links.
        if hrefParsed.path == '':
            continue

        # Skip non http hrefs
        if (hrefParsed.scheme != 'https'
                and hrefParsed.scheme != 'http'):
            continue

        # Relative Local link
        if hrefParsed.netloc == '':
            href = urljoin(url, href)
            if href not in localLinks:
                localLinks.append(href)
            continue

        # Absolute local link
        if hrefParsed.netloc == urlParsed.netloc:
            if href not in localLinks:
                localLinks.append(href)
    for link in localLinks:
        linkResp = req.get(link)
        try:
            linkRespContentType = linkResp.headers['content-type']
        except KeyError:
            continue
        applicationType = linkRespContentType.split(';')[0]
        if applicationType in rssApplicationTypes:
            foundRSSFeeds.append([url, link])

validatedRssFeeds = []
for rssFeed in foundRSSFeeds:
    feed = fp.parse(rssFeed[1])
    try:
        title = feed['feed']['title']
    except KeyError:
        continue
    validatedRssFeeds.append([rssFeed[0], rssFeed[1], title])

with open('FindRSSFromCSV.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerows(validatedRssFeeds)
