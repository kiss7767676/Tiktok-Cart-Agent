# Requirements

## Functional requirements

### Account setup

- Allow user to configure Shopee and TikTok credentials for the MVP.
- Keep Lazada credential support out of the active MVP until the Shopee and TikTok flows are stable.
- Store secrets locally using OS credential storage where possible.
- Store only non-secret metadata in local config/database.
- Re-login automatically when a platform signs the user out.
- Require user intervention for OTP, CAPTCHA, biometric, suspicious-login, or payment confirmation.

### Buy with Links

- Accept multiple URLs.
- Normalize shortened and redirected URLs.
- Detect platform:
  - TikTok Shop
  - Shopee
  - Lazada as deferred/unsupported for now
- Extract product ID, shop ID, variant hints, quantity hints, and campaign parameters where possible.
- Show a pre-checkout summary before automation starts.
- Add each item to cart.
- Bring user to checkout page or checkout screen.
- Stop before irreversible payment action.

### Find Best Buy

- Accept keyword or product description.
- Optional chatbot expansion using user-provided API key.
- User can select one or more platforms.
- MVP platform choices are Shopee and TikTok only.
- Budget filter:
  - RM minimum to maximum
  - No preference
- Display:
  - Product name
  - Platform
  - Price
  - Variation/options
  - Local/international shipping
  - Shipping cost or estimate
  - Rating
  - 4/5-star review percentage if available
  - 1-star review percentage if available
  - Sold count
  - Stock
  - Seller profile summary
  - Product link
- Rank products using transparent scoring.

### Research page

- Pull general web research for product intent.
- Include Google result snippets where available.
- Include YouTube review links.
- Include article links.
- Summarize pros, cons, common defects, and buying warnings.
- Keep source links visible.

## Non-functional requirements

- Lightweight local-first system.
- Native-feeling, minimal, fast desktop UI.
- Do not use Gradio or Streamlit for the application UI.
- Fast startup.
- Avoid unnecessary background services.
- Work with unstable marketplace pages by isolating platform adapters.
- Keep credentials and sessions local.
- Log automation steps without logging passwords, cookies, tokens, or payment data.

## Compliance and platform limits

Marketplace automation may be restricted by terms of service, anti-bot systems, CAPTCHA, login risk controls, and changing UI layouts. The system must support user-supervised automation and should not attempt to bypass security barriers.
