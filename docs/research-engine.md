# Research Engine

## Purpose

The research page exists to slow down impulsive purchases and add external context.

## Inputs

- Product title
- Product category
- Brand/model
- User concerns
- Marketplace product details

## Sources

- General search results
- Google AI Overview where accessible in scraped HTML
- YouTube review video links
- Articles and buying guides
- Public forum discussions where relevant

## Output

The page should show:

- Product/category summary
- What to check before buying
- Common defects or complaints
- Alternatives
- Source links
- Confidence level
- Reasons to buy
- Reasons to wait or skip

## Important behavior

The system should avoid generating fake certainty. If research is weak or sources are thin, it should say so and recommend manual checking.

## Current scraper behavior

The project includes an own Google scraper that:

- Requests Google search HTML.
- Attempts to identify AI Overview-like text when it is present in the HTML.
- Extracts organic result titles, URLs, and snippets where parseable.
- Searches YouTube for product review queries and extracts real video IDs instead of returning YouTube search-result pages.
- Reports scrape status when Google blocks the request or does not render AI Overview server-side.

It must not fabricate AI Overview content. If the scraper cannot find it, the UI should say that clearly.
It must not fabricate YouTube video IDs. If YouTube search does not return suitable videos, the UI should keep the Google/search fallback links.
