# Online Shopping System Malaysia

Fast local-first shopping assistant for Malaysian users who want to buy from TikTok Shop and Shopee without being pushed into each platform's full app experience. Lazada is intentionally deferred until the first two platforms are reliable.

The system focuses on two flows:

1. **Buy with Links**: user pastes product links, the system detects the marketplace, opens/automates the platform, adds items to cart, and brings the user to checkout.
2. **Find Best Buy**: user describes what they want, optionally sets budget, and compares relevant products across supported platforms in one readable view.

The core product goal is not only convenience. It should reduce impulsive buying by showing product quality, price, shipping, reviews, stock, seller reliability, and external research before checkout.

## Current repository purpose

This repository currently contains the file structure and technical specification for the system. It is intentionally docs-first so implementation can stay efficient and avoid premature complexity.

## Optimized architecture

- **Rust / Dioxus desktop UI** for the application shell. Rust is used where responsiveness and native feel matter: layout, interaction, keyboard-friendly flows, and presentation. Dioxus gives us a clean Rust app with HTML/CSS-style UI instead of Gradio/Streamlit.
- **Python automation core** for marketplace work. Python stays responsible for Shopee/TikTok automation, parsing, search/research aggregation, Playwright, Appium, and ADB phone control.
- **Stable command/API boundary** between Rust and Python. The UI calls backend commands such as `uv run oss-my detect --json`; it should not contain marketplace automation logic.
- **uv-managed `.venv`** for all Python dependencies. Do not activate the environment for normal use; run Python commands through `uv run`.
- **ADB physical-phone path** for app-backed marketplace flows. This is now the primary path for Shopee Best Buy because Shopee blocks anonymous/headless web search in this environment. The desktop app captures phone screenshots through ADB and renders the phone preview inline.
- **No emulator-first dependency for MVP usage.** A physical Android phone is the standalone target for now. Emulator support can be revisited later, but the app should not depend on Android Studio or closed-source emulator vendors.
- **Playwright** remains available for Shopee product detail and browser handoff experiments, but it is not the primary Best Buy search path.
- **Redroid/Appium/uiautomator2** can be added later if a Linux/WSL environment is prepared. On Windows, a connected Android phone is the practical first target.
- **SQLite** for local product cache, comparison history, and non-secret account metadata.
- **Keyring / OS credential store** for sensitive credential secrets.

## Repo map

```text
.
├── README.md
├── docs/
│   ├── product-brief.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── workflows.md
│   ├── platform-automation.md
│   ├── data-model.md
│   ├── research-engine.md
│   ├── security-and-privacy.md
│   ├── ui-spec.md
│   ├── roadmap.md
│   └── adr/
│       └── 0001-python-first-emulator-capable.md
├── src/
│   └── oss_my/
│       ├── __init__.py
│       └── main.py
├── tests/
│   └── README.md
├── config/
│   └── settings.example.toml
├── scripts/
│   └── README.md
└── .gitignore
```

## Implementation principle

Start with one reliable flow end-to-end before adding more platforms:

1. Shopee link detection and product extraction.
2. Physical-phone-backed Shopee Best Buy search with extracted visible product rows.
3. Product comparison table and detail pane.
4. Physical-phone-backed TikTok Shop search/checkout assist.
5. Lazada integration.
6. Research page with search/Youtube/article aggregation.

Avoid building throwaway prototype UIs. The product value is in trustworthy product comparison, fast review of tradeoffs, and friction-aware checkout.

## Development setup

Use `uv`, not `pip`. Do not activate `.venv` for normal development.

Open a fresh PowerShell window, then run:

```powershell
cd "C:\Users\jrom\VS code\Project\onlineShoppingSystem"
uv sync
uv run playwright install chromium
cargo run -p oss-my-desktop
```

If `uv` is not found, shell PATH has not refreshed. Use:

```powershell
& "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe" sync
& "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe" run playwright install chromium
```

If `cargo` is not found, shell PATH has not refreshed. Use:

```powershell
& "$env:USERPROFILE\.cargo\bin\cargo.exe" run -p oss-my-desktop
```

`uv sync` creates and manages the local `.venv`. Do not install project packages globally.

Project workflow and maintenance rules are documented in
[docs/engineering-practices.md](docs/engineering-practices.md).

Current feature status is documented in
[docs/feature-status.md](docs/feature-status.md).

Rust is used for the native desktop UI. After installing Rust, restart the shell or ensure
`%USERPROFILE%\.cargo\bin` is on `PATH`, then run:

```powershell
cargo run -p oss-my-desktop
```

## Current buildable command

Run:

```powershell
uv run oss-my detect "https://shopee.com.my/example-i.123.456"
```

Other backend commands:

```powershell
uv run oss-my best-buy "wireless mouse" --platform shopee
uv run oss-my phone-status
uv run oss-my phone-status --device R58R34FSP2L
uv run oss-my phone-screenshot
uv run oss-my phone-swipe 120 500 120 200
uv run oss-my phone-optimize
uv run oss-my phone-apps
uv run oss-my phone-install-apk "vendor/apks/shopee.apk"
uv run oss-my account-set shopee
uv run oss-my phone-best-buy "pentel p205" --group relevancy
uv run oss-my phone-best-buy "pentel p205" --group top_sales --device R58R34FSP2L
uv run oss-my research "wireless mouse"
uv run oss-my product-details "https://shopee.com.my/Good-Product-i.12345.67890"
uv run oss-my checkout-plan "https://shopee.com.my/Good-Product-i.12345.67890"
uv run oss-my account-status
```

## Local Ollama research answers

The Research page asks a local Ollama model by default through the backend command:

```powershell
uv run oss-my research "wireless mouse" --json
```

Research sources include Google search fallbacks and, when YouTube search returns suitable results, individual YouTube video URLs such as `https://www.youtube.com/watch?v=VIDEO_ID`.

Install Ollama, start it, and pull a model first:

```powershell
ollama pull qwen3:4b
```

Optional environment variables:

```powershell
$env:OSS_MY_OLLAMA_MODEL = "qwen3:4b"
$env:OSS_MY_OLLAMA_URL = "http://127.0.0.1:11434"
```

To skip Ollama for one CLI run:

```powershell
uv run oss-my research "wireless mouse" --no-ollama
```

## Validation commands

Run before committing implementation changes:

```powershell
uv run ruff check .
uv run pytest
cargo fmt --check
cargo check -p oss-my-desktop
```
