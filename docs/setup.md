# Setup and Run Commands

This project uses:

- `uv` for Python dependency and virtual environment management.
- Rust/Cargo for the native desktop UI.
- Playwright Chromium for Shopee web automation.
- Android Platform Tools / ADB for physical phone control.
- Optional scrcpy for manual debugging. The app's main Find Best Buy phone preview uses inline ADB screenshots.

## Normal setup

Open a fresh PowerShell window. Do not activate `.venv`.

```powershell
cd "C:\Users\jrom\VS code\Project\onlineShoppingSystem"
uv sync
uv run playwright install chromium
```

## Start the desktop app

```powershell
cargo run -p oss-my-desktop
```

## Physical phone setup for Best Buy

Shopee Best Buy now uses a connected Android phone first because web scraping is blocked in the current environment.

ADB is required so the app can open marketplace apps, capture screenshots, read visible UI text, and send supervised tap/swipe commands:

```powershell
winget install Google.PlatformTools
```

Phone preparation:

1. Enable Developer Options on the Android phone.
2. Enable USB debugging.
3. Connect the phone by USB.
4. Accept the computer authorization prompt on the phone.
5. Install Shopee and TikTok from Play Store on the phone.

Check status:

```powershell
uv run oss-my phone-status
uv run oss-my phone-apps
```

If more than one phone is connected, select the target serial in the desktop app or pass it explicitly:

```powershell
uv run oss-my phone-status --device R58R34FSP2L
uv run oss-my phone-best-buy "pentel p205" --group relevancy --device R58R34FSP2L
```

Click `Prepare phone` in Find Best Buy or run this to disable Android animations where the phone allows it:

```powershell
uv run oss-my phone-optimize
```

Capture the inline phone preview screenshot:

```powershell
uv run oss-my phone-screenshot
```

The inline phone preview is screenshot-based. Current UI controls provide tap-center and swipe buttons that send ADB input commands. This is intentionally supervised, not hidden automation.

## Preinstall marketplace apps

The app can check whether Shopee/TikTok packages are installed:

```powershell
uv run oss-my phone-apps
```

For a standalone local setup, keep APK files outside git under `vendor/apks/` and install them through ADB:

```powershell
uv run oss-my phone-install-apk "vendor/apks/shopee.apk"
uv run oss-my phone-install-apk "vendor/apks/tiktok.apk"
```

`vendor/apks/` is ignored by git. Do not commit downloaded marketplace APKs.

If Shopee is not installed, Best Buy search falls back to the Shopee website URL. Once Shopee is installed on the phone, search attempts app deep links first.

## Account credentials

Credentials are stored in the OS keyring:

```powershell
uv run oss-my account-set shopee
uv run oss-my account-set tiktok
uv run oss-my account-status
```

Login automation must remain user-supervised. The app can open the installed marketplace app, but OTP, CAPTCHA, device trust prompts, and payment authorization must be completed by the user.

The Account Setup page includes credential fields and save buttons. Saved passwords are written to the OS keyring and the password box is cleared after saving.

Run a Shopee search through the phone:

```powershell
uv run oss-my phone-best-buy "pentel p205" --group relevancy
uv run oss-my phone-best-buy "pentel p205" --group top_sales
```

In the desktop app, open `Find Best Buy`, click `Check device`, then search. The app renders the phone preview inline on the left and extracted item rows on the right.

If no phone is connected or authorized, the app shows the ADB status and does not fabricate product data.

## If commands are not found

If `uv` is not found:

```powershell
& "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe" sync
```

If `cargo` is not found:

```powershell
& "$env:USERPROFILE\.cargo\bin\cargo.exe" run -p oss-my-desktop
```

## Backend smoke test

```powershell
uv run oss-my detect "https://shopee.com.my/Good-Product-i.12345.67890"
uv run oss-my product-details "https://shopee.com.my/Good-Product-i.12345.67890"
uv run oss-my phone-status
```

Expected result:

- platform: `shopee`
- MVP: `yes`
- shop ID: `12345`
- item ID: `67890`

## Validation before committing

```powershell
uv run ruff check .
uv run pytest
cargo fmt --check
cargo check -p oss-my-desktop
```

## Important environment rule

Do not activate `.venv` for normal project work.

Use `uv run ...` instead. `uv` is a user/system tool that manages `.venv`; it is not installed inside `.venv`.
