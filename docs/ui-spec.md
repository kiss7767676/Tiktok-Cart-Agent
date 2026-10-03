# UI Specification

## Design goals

- Native-feeling desktop app.
- Fast startup and fast interactions.
- Clean visual hierarchy similar in spirit to Zed: focused, compact, readable.
- No infinite scrolling.
- No gamified discount pressure.
- Show negative signals clearly.
- No Gradio or Streamlit.

## UI technology direction

Target a Rust / Dioxus desktop shell. The UI should call the Python core through a stable command/API boundary.

The first backend APIs should be designed as if the UI will call:

- `detect_links(urls)`
- `resolve_product(platform, product_ref)`
- `search_products(platforms, query, budget)`
- `compare_products(products)`
- `prepare_checkout(platform, selected_products)`

This prevents the backend from depending on a specific frontend framework.

## Home screen

Actions:

1. Buy with Links
2. Find Best Buy
3. Research Product
4. Account Setup

## Interaction model

The UI should let users move between buying and researching without losing context.

Important shared state:

- A global added-link queue.
- A sidebar indicator showing how many links are queued.
- Find Best Buy is the main workspace for product comparison and details.
- Find Best Buy starts with phone controls: device selector, device status, screenshot refresh, query, platform filters, and sort toggle.
- The phone preview is inline inside the Rust app using ADB screenshots. It should not open a separate window for the normal user flow.
- Phone interaction is supervised through explicit tap/swipe controls sent through ADB.
- Search results render as plain readable rows/table below the phone controls, not cards.
- Product rows from Find Best Buy can be added to the Buy with Links checkout queue.
- Buy with Links only manages checkout queue/handoff.
- Research can be launched from a Best Buy product row or used directly.

## Suggested layout

```text
+----------------------+----------------------------------+--------------------------+
| Actions              | Phone + Product Table            | Details / Research       |
|----------------------|----------------------------------|--------------------------|
| Buy with Links       | Title | RM | Ship | Risk | Rank  | Selected product         |
| Find Best Buy        | Phone preview + rows             | Reasons to buy           |
| Research Product     | ...                              | Reasons to avoid         |
| Account Setup        | ...                              | Sources                  |
+----------------------+----------------------------------+--------------------------+
```

## Product comparison table

Each product row should include:

- Image thumbnail
- Product title
- Platform
- Price
- Shipping
- Local/international
- Rating
- 1-star review percentage
- 4/5-star review percentage
- Sold count
- Stock
- Seller score
- Why this rank
- Open research
- Add to checkout flow

The table should prioritize readable text density over visual cards. The user should be able to compare product title, price, shipping/location, sold count, and risk notes without opening Shopee unless they are ready to verify or checkout.

## Product details pane

Find Best Buy should support a single-pane product detail view after links are queued or pasted for comparison.

For Shopee, show:

- Product title
- Price
- Rating
- Sold count
- Stock
- Seller/shop
- Location
- Description
- Options/variations when available
- Warnings when live details are blocked or incomplete
- Open in Shopee action

Buy with Links should not show product detail widgets. It should stay focused on checkout queue and checkout handoff.

## Anti-impulse elements

- Show "Reasons to wait/avoid" next to "Reasons to buy".
- Show total estimated cost, not only item price.
- Group vouchers/promos under final cost instead of making them visually dominant.
- Show review risk before checkout action.
- Keep research one click away from Best Buy results.
- Make checkout handoff warnings visible before opening the platform.
