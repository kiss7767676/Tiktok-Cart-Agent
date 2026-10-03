# Architecture

## Optimized architecture

The optimized architecture is intentionally split by what each language is good at.

- Rust owns the desktop UI and presentation layer.
- Python owns marketplace automation and rapid integration work.
- The boundary between them is stable command/API calls, not shared internal code.

This avoids two bad outcomes:

- a slow prototype UI that does not match the product goal;
- overusing Rust for automation work where Python libraries are stronger and faster to iterate.

```text
Native Desktop UI
    |-- Rust / Dioxus desktop shell
    |-- clean command palette / split-pane layout
    |-- no Gradio / no Streamlit
    |
Local IPC / API Boundary
    |-- current: uv run oss-my ... --json
    |-- later: local HTTP or structured IPC if needed
    |
Python Core / Orchestrator
    |-- Buy with Links
    |-- Find Best Buy
    |-- Research Page
    |
Platform Adapters
    |-- Shopee Phone/Web Adapter
    |-- TikTok Android Adapter
    |-- Lazada Adapter later
    |
Automation Layer
    |-- ADB for supervised physical Android phone flows
    |-- Playwright for web details/handoff experiments
    |-- Appium/uiautomator2 later if interaction complexity requires it
    |
Local Data Layer
    |-- SQLite cache
    |-- OS keyring secrets
    |-- Local config
```

## Components

### UI

The UI is a product-critical part of the system. It should be a fast desktop application, not a Streamlit/Gradio prototype.

Target traits:

- Rust-native desktop shell.
- Zed-like feel: dense but readable, fast keyboard navigation, calm visual hierarchy.
- Side panel for actions, main panel for product comparison, right panel for product/research details.
- No infinite scroll.
- No gamified discount pressure.

Minimal interface with three main areas:

- Action launcher: Buy with Links, Find Best Buy, Research Product, Account Setup.
- Product comparison table.
- Research and checkout preparation panel.

### Orchestrator

Coordinates workflows:

- Link parsing.
- Platform detection.
- Adapter selection.
- Product comparison scoring.
- Research aggregation.
- Checkout handoff.

### Platform adapters

Each marketplace gets its own adapter so UI changes or automation breakage stay isolated.

Common adapter interface:

- `detect_link(url)`
- `resolve_product(url)`
- `search_products(query, filters)`
- `get_product_details(product_id)`
- `add_to_cart(product, options)`
- `open_checkout(cart_context)`

### Automation layer

Use physical-phone automation where web search/checkout/payment is unavailable or blocked. Use web automation only where it remains reliable.

Initial recommendation:

- Shopee: physical phone first for Best Buy search; web/API details are best-effort fallback.
- TikTok Shop: physical phone first.
- Lazada: later.

### Data layer

SQLite stores:

- Product cache.
- Search results.
- Comparison sessions.
- Platform account metadata.
- Automation logs.

Secrets are not stored in SQLite unless encrypted with a user-controlled key.

## Efficiency choices

- Python is sufficient for I/O-heavy automation.
- Use async I/O for search and research aggregation.
- Cache platform search/product results with short TTL.
- Use Rust for the desktop UI because UI responsiveness and product feel are explicit requirements.
- Keep the Python core usable from CLI/headless tests so marketplace logic can be built and verified before the full UI is ready.

## What should use Rust

Use Rust for:

- native desktop UI;
- local app state and UI responsiveness;
- future high-volume product ranking only if profiling proves Python is too slow;
- future local indexing/cache services only if needed.

Do not use Rust initially for:

- Shopee marketplace automation;
- TikTok phone automation;
- Appium/uiautomator2 control;
- AI/search integrations;
- unstable marketplace scraping experiments.

Those should stay in Python until there is a concrete performance or packaging reason to move them.
