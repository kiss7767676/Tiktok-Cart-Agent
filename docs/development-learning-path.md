# Development Learning Path

This project should be built in layers so each part is understandable.

## Layer 1: Domain models

Domain models describe the shopping system without caring about UI, Shopee, TikTok, or browsers.

Examples:

- `Platform`
- `ProductIdentity`
- `DetectedLink`
- `ProductSummary`

If these models are clear, every later feature becomes easier to reason about.

## Layer 2: Platform detection

Before the app can automate anything, it must answer:

> What platform does this URL belong to?

This is why the first implementation starts with URL detection.

## Layer 3: Shopee product identity parsing

Shopee links often contain shop ID and item ID. Extracting those IDs gives us a stable product reference even if the title slug changes.

Example:

```text
https://shopee.com.my/Product-Name-i.123.456
```

Means:

- shop ID: `123`
- item ID: `456`

## Layer 4: Product metadata

After the system can identify a product, it can fetch details:

- title
- price
- variations
- shipping
- stock
- seller profile
- reviews

This will be added after the identity parser is tested.

## Layer 5: UI boundary

The future Rust UI should not know Shopee internals. It should call simple backend commands such as:

```text
detect_links(urls)
resolve_product(platform, product_ref)
search_products(platforms, query, budget)
```

That separation keeps the system maintainable.

## Layer 6: Engineering workflow

Use the project practices in `docs/engineering-practices.md` while building each layer.

The important rule is that code, tests, and docs should move together. If the behavior changes, the documentation and validation commands should change in the same work cycle.
