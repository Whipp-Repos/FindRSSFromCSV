#!/usr/bin/env python3

import urllib
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

rssSubDomainOptions = ['feeds']

rssDefaultPathPossibilities = ['/feed', '/rss.xml',
                               '/xml/rss/all.xml', '/rss', '.rss',
                               '/xml/rss.xml',
                               '/xml/rss/rss.xml']

rssDomainSpecificPathPossibilities = [
    {
        "Domain": "tumblr.com",
        "Path": "{domain}/rss"
    },
    {
        "Domain": "blogspot.com",
        "Path": "{domain}/feeds/posts/default"
    },
    {
        "Domain": "medium.com",
        "Path": "{domain}/feed/{path_0}"
    }
]

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

    # Check if it is a known pattern and skip the rest of the checks.
    domainName = '.'.join(urlParsed.netloc.split('.')[::-1][:2][::-1])
    domainNamePossibility = [item for item
                             in rssDomainSpecificPathPossibilities
                             if item["Domain"] == domainName]

    if domainNamePossibility:
        for item in domainNamePossibility:
            path_0 = urlParsed.path.lstrip('/').split('/')[0]
            domain = "{scheme}://{netloc}".format(
                scheme=urlParsed.scheme,
                netloc=urlParsed.netloc)
            pathParsed = item["Path"]
            defaultPath = pathParsed.format(
                domain="https://" + urlParsed.netloc,
                path_0=path_0)
            foundRSSFeeds.append([url, defaultPath])
        continue

    # Build Possible Default values
    domainNamesForDefaults = [domainName]
    for subDomain in rssSubDomainOptions:
        domainNamesForDefaults.append(
            '{subDomain}.{domainName}'.format(
                subDomain=subDomain, domainName=domainName))

    defaultPossibilities = []
    for domainNameForDefaults in domainNamesForDefaults:
        for defaultPath in rssDefaultPathPossibilities:
            fullDomainName = "{scheme}://{domain}".format(
                scheme=urlParsed.scheme,
                domain=domainNameForDefaults)

            basePath = urlParsed.path.rstrip('/')

            rssPathPossibility = urljoin(
                fullDomainName,
                defaultPath)

            defaultPossibilities.append(rssPathPossibility)

            if urlParsed.path != '' and urlParsed.path != '/':
                defaultPath = defaultPath.lstrip('/')
                rssFullpathPossibility = urljoin(
                    fullDomainName,
                    basePath)
                rssFullpathPossibility = urljoin(
                    rssFullpathPossibility,
                    defaultPath)
                defaultPossibilities.append(rssFullpathPossibility)

    defaultPossibilities = list(set(defaultPossibilities))

    print(('Built {0} Default Link'
           ' Possibilities').format(len(defaultPossibilities)))

    defaultPossibilities = [[url, item] for item in defaultPossibilities]
    foundRSSFeeds = foundRSSFeeds + defaultPossibilities

    print(('{0} RSS Link'
           ' Possibilities').format(len(foundRSSFeeds)))

    print(('Requesting {0}'.format(url)))
    resp = req.get(url)

    baseDomain = "{scheme}://{domain}".format(
        scheme=urlParsed.scheme,
        domain=domainName)

    print(('Requesting {0}'.format(baseDomain)))
    respDomain = req.get(baseDomain)

    soupPath = bs(resp.text, 'html.parser')
    print(('Parsed {0}'.format(url)))
    soupDomain = bs(respDomain.text, "html.parser")
    print(('Parsed {0}'.format(baseDomain)))

    # Look for links on page that are called out as RSS Feeds
    linksPath = soupPath.find_all('link')
    linksDomain = soupDomain.find_all('link')
    links = linksPath + linksDomain
    print(('Found {0} links').format(len(links)))
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

    print(('{0} RSS Link'
           ' Possibilities').format(len(foundRSSFeeds)))

    # Follow local links on page to see if they return a valid application Type
    alinksPath = soupPath.find_all('a')
    alinksDomain = soupDomain.find_all('a')
    alinks = alinksPath + alinksDomain

    print(('Found {0} anchor links').format(len(alinks)))
    localLinks = []
    for alink in alinks:
        try:
            href = alink['href']
        except KeyError:
            continue

        hrefParsed = urlparse(href)

        # Skip inpage links.
        if hrefParsed.path == '':
            continue

        # Skip non http(s) hrefs
        if hrefParsed.scheme[:4] != 'http':
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

    localLinks = list(set(localLinks))

    print(('Found {0} local links').format(len(localLinks)))

    for link in localLinks:
        print(('Visiting {0}').format(link))
        linkResp = req.head(link)

        try:
            linkRespContentType = linkResp.headers['content-type']
        except KeyError:
            continue

        applicationType = linkRespContentType.split(';')[0]
        if applicationType in rssApplicationTypes:
            foundRSSFeeds.append([url, link])

    print(('{0} RSS Link'
           ' Possibilities for {1}').format(len(foundRSSFeeds), url))

validatedRssFeeds = []
for rssFeed in foundRSSFeeds:
    print(('Checking {0} for actual Feed').format(rssFeed[1]))
    try:
        feed = fp.parse(rssFeed[1])
    except ConnectionRefusedError:
        print("Rejected")
        continue
    except urllib.error.URLError:
        print("Rejected")
        continue

    try:
        title = feed['feed']['title']
    except KeyError:
        continue

    validatedRssFeeds.append([rssFeed[0], rssFeed[1], title])

with open('FindRSSFromCSV.csv', 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerows(validatedRssFeeds)
