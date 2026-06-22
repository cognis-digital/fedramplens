# Sources

## Catalog data feeds (edge / air-gap deployable)

Authoritative, keyless feeds consumed by `fedramplens feeds` and the `--enrich`
flag. Fetched over HTTPS, cached to disk (`COGNIS_FEEDS_CACHE`), and re-served
`--offline`. Catalog: [`fedramplens/data_feeds_2026.json`](fedramplens/data_feeds_2026.json);
fetcher: [`fedramplens/datafeeds.py`](fedramplens/datafeeds.py).

| Feed id | Source URL | Use |
|---|---|---|
| `oscal-800-53-rev5-catalog` | https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json | Resolve NIST SP 800-53 rev5 control ids → official titles in findings/SSP |

The NIST SP 800-53 rev5 catalog (and the FedRAMP/RMF baseline profiles) are
published by NIST as native OSCAL JSON at <https://github.com/usnistgov/oscal-content>.

<!-- cognis-2026-live-sources -->

## Live 2026 sources (auto-expanded)

_Always-current feeds, live web-search queries, and keyless APIs for real-time monitoring. Ingest at runtime with `livesearch.py`._

### Finance
- **feed** · https://feeds.a.dj.com/rss/RSSMarketsMain.xml
- **feed** · https://www.ft.com/rss/home
- **feed** · https://www.cnbc.com/id/100003114/device/rss/rss.html
- **feed** · https://feeds.bloomberg.com/markets/news.rss
- **live search** · `Federal Reserve rate decision 2026`
- **live search** · `equity market selloff macro`
- **live search** · `earnings surprise guidance 2026`
- **api** · https://fred.stlouisfed.org/docs/api/fred/ (FRED macro, free key)
- **api** · https://www.sec.gov/cgi-bin/browse-edgar (EDGAR filings, free)
- **api** · https://data.alpaca.markets (market data)

### Ai
- **feed** · https://huggingface.co/blog/feed.xml
- **feed** · https://openai.com/news/rss.xml
- **feed** · https://www.anthropic.com/rss.xml
- **feed** · https://export.arxiv.org/rss/cs.AI
- **feed** · https://export.arxiv.org/rss/cs.LG
- **live search** · `frontier AI model release 2026`
- **live search** · `AI agent benchmark state of the art`
- **live search** · `open-weight LLM release`
- **live search** · `AI policy regulation 2026`
- **api** · http://export.arxiv.org/api/query (arXiv, free)
- **api** · https://api.github.com/search/repositories?q=stars (trending repos, free)
- **api** · https://hn.algolia.com/api (Hacker News, free)

### Maritime
- **feed** · https://gcaptain.com/feed/
- **feed** · https://www.maritime-executive.com/rss
- **feed** · https://splash247.com/feed/
- **feed** · https://www.tradewindsnews.com/rss
- **feed** · https://lloydslist.com/rss
- **live search** · `shadow fleet sanctioned tanker AIS`
- **live search** · `ship-to-ship transfer sanctions evasion`
- **live search** · `dark vessel AIS spoofing`
- **live search** · `OFAC sanctioned vessel designation`
- **live search** · `port disruption maritime security`
- **api** · https://aisstream.io (free real-time AIS websocket, key required)
- **api** · https://globalfishingwatch.org/our-apis/ (IUU / dark activity, free API token)
- **api** · https://www.marinetraffic.com (consumer vessel tracking)
- **api** · https://sanctionssearch.ofac.treas.gov (OFAC SDN, free)

