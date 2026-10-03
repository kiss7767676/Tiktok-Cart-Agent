# Platform Automation Specification

## Automation policy

The system is user-supervised. It can navigate, fill forms, and add to cart, but it must stop before final payment confirmation.

It must not attempt to bypass:

- CAPTCHA
- OTP
- Device trust checks
- Payment authorization
- Marketplace fraud/risk controls

## Platform strategy

### TikTok Shop

TikTok Shop should use Android app automation because web payment/checkout may not support the required flow.

Recommended stack:

- Physical Android phone through ADB for the MVP.
- Redroid for containerized Android later where available.
- Appium or uiautomator2 for UI automation.
- ADB for device/session control.

### Shopee

Use physical-phone automation for Best Buy search. Direct Shopee web/API search is blocked in the current environment, so web automation should be treated as a fallback for details or handoff experiments, not the primary search path.

The default MVP target is a connected Android phone with USB debugging enabled. This avoids Android Studio and closed-source emulator dependencies while keeping the app standalone on the desktop side.

Current Shopee adapter behavior:

- Parses `shop_id` and `item_id` from common Shopee product URLs.
- Attempts live search for both Most Relevant and Top Sales groups.
- Attempts live product detail retrieval through Shopee's web API.
- Returns fallback product details when the request is blocked or response shape changes.
- Renders product details/options in the desktop app when data is available.
- Opens Shopee search in a connected Android phone through ADB.
- Captures phone screenshots through ADB so the user can see the phone UI inline.
- Sends phone controls as ADB tap/swipe commands.
- Extracts visible Android UI hierarchy text into Best Buy result rows.
- Checks whether marketplace app packages are installed.
- Installs user-provided local APK files into the connected phone when needed.

If a marketplace app is not installed, the adapter must report that clearly and may use browser/web URL fallback only as a degraded mode. App-first behavior requires the app package to be present on the phone.
- Lets the user open the product directly in Shopee.

Next Shopee automation steps:

- Add guided scroll extraction for more search result rows.
- Improve grouping of title/price/sold/location text from Shopee result cells.
- Add supervised app login detection and recovery when Shopee signs the user out.
- Add reliable Top Sales tab/sort interaction if the app UI exposes it.
- Add supervised add-to-cart automation inside the phone app.
- Stop before final payment confirmation.

### Lazada

Deferred until Shopee and TikTok are stable. Keep the adapter architecture ready for Lazada, but do not spend implementation effort on it during the MVP.

## Adapter contract

Each adapter should expose:

```python
class PlatformAdapter:
    platform_name: str

    def can_handle_url(self, url: str) -> bool: ...
    async def resolve_product(self, url: str) -> Product: ...
    async def search_products(self, query: SearchQuery) -> list[Product]: ...
    async def ensure_logged_in(self, account_id: str) -> LoginState: ...
    async def add_to_cart(self, product: Product, options: CartOptions) -> CartResult: ...
    async def open_checkout(self, cart_id: str) -> CheckoutState: ...
```

## Failure handling

Automation should return clear states:

- `success`
- `needs_user_login`
- `needs_otp`
- `needs_captcha`
- `variation_required`
- `out_of_stock`
- `platform_layout_changed`
- `network_error`
- `blocked_by_platform`

Each failure should include a user-readable recovery step.
