# Feature Status

This document tracks what the app currently does versus what still needs platform-specific implementation.

## Current UX flow

```text
Find Best Buy
    -> Check connected Android phone
    -> Select target device serial when a phone is connected
    -> Render inline phone preview from ADB screenshot
    -> Search Shopee inside the phone app context
    -> Extract visible product rows from Android UI hierarchy
    -> Toggle Most Relevant or Top Sales
    -> Add chosen products to checkout
    -> Link count appears in sidebar
    -> Buy with Links
    -> Prepare checkout handoff
    -> Open platform cart/search context

Research Product
    -> Run own Google scraper
    -> Render AI Overview when present in scraped HTML
    -> Render scraped Google sources/snippets
    -> Generate Google/search links and real YouTube video links when found
    -> Open Google/search sources externally
    -> Load YouTube video sources in the right-side player

Account Setup
    -> Stores credentials in OS keyring
    -> Shows connected phone app readiness
```

## Implemented now

### Rust / Dioxus desktop UI

- Four main views:
  - Buy with Links
  - Find Best Buy
  - Research Product
  - Account Setup
- Shared added-link queue.
- Sidebar indicator showing how many links are ready.
- Best Buy is the main comparison workspace.
- Best Buy has minimal controls: query, budget, sort, platform filter, search, refresh phone, check device.
- Best Buy has a phone selector so commands target the intended ADB serial.
- Best Buy renders an inline phone preview instead of opening a separate phone window.
- Phone controls send tap/swipe commands through ADB.
- Phone preparation command disables Android animations where allowed.
- Search results are rendered as readable table rows, not product cards.
- Search can toggle Shopee Most Relevant and Top Sales groups.
- Best Buy rows can be added into the checkout queue when a product URL is available.
- Buy with Links is checkout-oriented and no longer renders product details.
- Checkout handoff plan can be generated from queued links.
- Research source links and scraped sources are clickable; YouTube video sources load in the in-app player.

### Python backend commands

```powershell
uv run oss-my detect --json <links>
uv run oss-my best-buy "wireless mouse" --platform shopee --json
uv run oss-my phone-status --json
uv run oss-my phone-status --device R58R34FSP2L --json
uv run oss-my phone-screenshot --json
uv run oss-my phone-tap 120 240 --json
uv run oss-my phone-swipe 120 500 120 200 --json
uv run oss-my phone-optimize --json
uv run oss-my phone-apps --json
uv run oss-my phone-install-apk vendor/apks/shopee.apk --json
uv run oss-my phone-open-app shopee --json
uv run oss-my phone-best-buy "pentel p205" --group relevancy --json
uv run oss-my phone-best-buy "pentel p205" --group top_sales --device R58R34FSP2L --json
uv run oss-my product-details --json <links>
uv run oss-my research "wireless mouse" --json
uv run oss-my checkout-plan --json <links>
uv run oss-my account-status --json
```

### Shopee

- Shopee URL detection.
- Shopee `shop_id` and `item_id` parsing for common URL formats.
- Shopee product details command.
- Shopee product details pane in the Rust app.
- Shopee search adapter requests Most Relevant and Top Sales result groups.
- Shopee phone Best Buy command opens Shopee search on the connected Android phone and extracts visible UI text into product rows.
- Shopee phone commands accept `--device` and use `adb -s <serial>` so connected emulators or extra devices do not hijack the command.
- Shopee search uses UI-bound navigation when deep links do not land on search results.
- Top Sales search taps the visible `Top Sales` sort tab after searching.
- ADB path and device detection.
- Inline phone screenshot capture from the app.
- ADB tap/swipe controls from the app.
- App install/status commands for local APK preinstall.
- Product options render when Shopee returns option data.
- Shopee search handoff URL generation.
- Shopee cart page handoff URL generation.

Shopee live detail retrieval is best-effort. If Shopee blocks the unauthenticated request or changes its response shape, the adapter returns fallback detail data using the parsed URL identity and asks the user to open Shopee directly.

Shopee live web/API search retrieval is best-effort only. In the current environment Shopee returns `403 Forbidden` for anonymous search API requests and traffic-verification pages for headless browser attempts. The active Best Buy path is therefore physical-phone-first.

The first phone extraction reads the visible Android UI hierarchy. It can produce useful title/price/sold/location rows, but it is still heuristic and depends on what the Shopee app exposes on screen. The user should verify final price, vouchers, variations, seller, stock, and shipping inside Shopee before checkout.

### Research

- Own Google scraper attempts to fetch Google search HTML.
- AI Overview is rendered only when it appears in the scraped HTML.
- YouTube review discovery fetches real video results and returns individual `watch?v=` URLs when suitable videos are found.
- Organic Google result titles/snippets are rendered when parseable.
- If Google blocks or omits AI Overview, the UI shows scrape status instead of fabricated text.

## Not implemented yet

### Hardened phone product extraction

The app has a first Shopee phone search adapter, but it is not hardened enough to guarantee live rating, seller, shipping, stock, options, and all result rows. Android UI hierarchy extraction only sees visible text.

Next step:

- Add guided scrolling extraction to collect more rows.
- Add app-specific selectors and text grouping for Shopee result cells.
- Add a supervised Shopee app login setup flow.
- Add Top Sales tab/sort interaction where Shopee app UI exposes it reliably.
- Reuse the existing `product-details` command and Rust detail pane.
- Add adapter fixtures for stable parsing tests.

### Automatic add-to-cart

The app does not yet automatically add Shopee items to cart.

Next step:

- Use Playwright to open Shopee.
- Reuse detected `shop_id` and `item_id`.
- Handle login/CAPTCHA/OTP as user-supervised checkpoints.
- Stop before final payment.

### TikTok Shop phone automation

TikTok is in MVP scope, but phone automation is not implemented yet.

Next step:

- Reuse the same ADB phone control layer.
- Add TikTok login/session detection.
- Add TikTok product/search handoff and checkout handoff.

### Account credential setup

Credentials can be stored in the OS keyring through `account-set` or the Account Setup UI. The UI shows whether each platform is configured without exposing secret values.

Next step:

- Add app-specific login form selectors for Shopee/TikTok after the apps are installed and their current login screens are inspected.
- Use stored credentials only in a user-supervised login flow.
- Never log credentials, cookies, tokens, OTP, or payment data.

## Product safety rules

- Never automate final payment confirmation.
- Never bypass CAPTCHA, OTP, account risk checks, or marketplace security.
- Show warnings when the app is doing a handoff instead of full automation.
- Show negative research signals before checkout.
