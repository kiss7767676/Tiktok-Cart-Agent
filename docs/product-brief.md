# Product Brief

## Title

Online Shopping System Malaysia

## Target users

Malaysian shoppers who:

- Receive TikTok/Shopee links but do not want to install or open the marketplace app.
- Know what they want but do not know which marketplace or seller is the best option.
- Want a calmer, more objective buying process with fewer manipulative app patterns.

## Problem cases

### Case 1: User has shopping links

The user already has one or more product links. They want the system to:

- Detect the platform from each link.
- Open the correct automation path.
- Add products to cart.
- Bring them to checkout.
- Let the user manually decide payment, address, vouchers, and final confirmation.

### Case 2: User knows what they want

The user enters a keyword or product intent. The system should:

- Search across selected platforms.
- Return popular or best-value products.
- Summarize product details in a comparable format.
- Provide research context before purchase.

## Product philosophy

The system should help the user make conscious purchases. It should not copy addictive marketplace UI patterns such as endless scroll, fake urgency, or attention-heavy discount widgets.

Default behavior should favor:

- Short comparison tables.
- Clear tradeoffs.
- Shipping and seller reliability.
- Negative review visibility.
- Research before checkout.
- Explicit confirmation before purchase-critical steps.

## Active platform scope

MVP:

- Shopee
- TikTok Shop

Deferred:

- Lazada

Lazada should not drive early architecture decisions beyond keeping platform adapters extensible.

## Non-goals

- Fully automated payment submission.
- Bypassing marketplace security controls.
- Scraping private data outside the user's account/session.
- Competing with the marketplaces as a full storefront.
