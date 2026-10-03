# Data Model

## Main entities

### PlatformAccount

- `id`
- `platform`
- `display_name`
- `username_hint`
- `credential_key_ref`
- `last_login_status`
- `last_checked_at`

### Product

- `id`
- `platform`
- `platform_product_id`
- `shop_id`
- `url`
- `title`
- `description`
- `price_min`
- `price_max`
- `currency`
- `rating`
- `review_count`
- `sold_count`
- `stock`
- `is_local`
- `shipping_summary`
- `seller_id`
- `raw_snapshot`
- `cached_at`

### ProductVariation

- `id`
- `product_id`
- `name`
- `options`
- `price`
- `stock`

### SellerProfile

- `id`
- `platform`
- `platform_seller_id`
- `name`
- `rating`
- `followers`
- `response_rate`
- `ship_on_time_rate`
- `location`

### ReviewSummary

- `product_id`
- `star_5_percent`
- `star_4_percent`
- `star_3_percent`
- `star_2_percent`
- `star_1_percent`
- `common_positive_terms`
- `common_negative_terms`
- `red_flags`

### ResearchSource

- `id`
- `query`
- `source_type`
- `title`
- `url`
- `snippet`
- `published_at`
- `captured_at`

### ComparisonSession

- `id`
- `query`
- `budget_min`
- `budget_max`
- `platforms`
- `ranking_strategy`
- `created_at`

## Ranking score draft

Default score out of 100:

- Price fit: 20
- Rating/review quality: 20
- Low 1-star percentage: 15
- Seller reliability: 15
- Shipping fit: 10
- Stock/availability: 10
- Local preference: 5
- Research confidence: 5

The UI must show score reasons instead of only showing a number.
