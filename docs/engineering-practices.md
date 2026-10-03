# Engineering Practices

This document defines how this repository should be maintained. Treat it as a working agreement for future implementation.

## Environment management

### Python

- Use `uv` for all Python dependency and virtual environment management.
- Do not use `pip` for this project.
- Do not install project packages globally.
- Do not activate `.venv` for normal development commands.
- The project environment is `.venv`, created and managed by:

```powershell
uv sync
```

- Run Python tools through `uv run`, for example:

```powershell
uv run pytest
uv run ruff check .
uv run oss-my detect "https://shopee.com.my/Good-Product-i.12345.67890"
```

- Keep dependencies in `pyproject.toml`.
- Commit `uv.lock`.
- Do not restore `requirements.txt` unless there is a specific deployment need.

If `uv` is not found because the shell PATH has not refreshed, use the installed executable directly:

```powershell
& "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_8wekyb3d8bbwe\uv.exe" sync
```

### Rust

- Rust is used for the native desktop UI.
- The Rust workspace is rooted at `Cargo.toml`.
- The desktop app package is `oss-my-desktop`.
- Run the app with:

```powershell
cargo run -p oss-my-desktop
```

- If the shell has not picked up Rust PATH yet, use:

```powershell
& "$env:USERPROFILE\.cargo\bin\cargo.exe" run -p oss-my-desktop
```

- Commit `Cargo.lock`.
- Do not commit `target/`.

### Playwright

Install browser binaries through uv:

```powershell
uv run playwright install chromium
```

## Required validation before commits

Run these checks before committing code changes:

```powershell
uv run ruff check .
uv run pytest
cargo fmt
cargo check -p oss-my-desktop
```

If a change only touches documentation, tests/build checks are optional but still preferred when fast.

## Documentation rules

Update docs in the same commit when behavior, architecture, setup, or commands change.

Important docs:

- `README.md`: user-facing setup and current run commands.
- `docs/architecture.md`: major system structure and boundaries.
- `docs/feature-status.md`: what exists now versus what is still pending.
- `docs/ui-spec.md`: UI direction and layout rules.
- `docs/platform-automation.md`: marketplace automation strategy.
- `docs/development-learning-path.md`: teaching path for learning the system.
- `docs/engineering-practices.md`: repository workflow and maintenance rules.

When adding a feature:

1. Update or add the relevant spec.
2. Add the implementation.
3. Add tests where practical.
4. Run validation.
5. Commit and push.

## Architecture practices

- Keep the Rust UI and Python core separated.
- The Rust UI should call stable backend commands/API boundaries.
- Do not put Shopee/TikTok automation logic directly inside Rust UI code.
- Python core should remain testable without launching the desktop UI.
- Platform-specific logic belongs under `src/oss_my/platforms/`.
- Shared concepts belong under `src/oss_my/domain/`.

## UI practices

- Do not use Gradio or Streamlit for the application UI.
- Prefer fast native desktop UI behavior.
- Keep the layout calm, compact, and readable.
- Avoid infinite scroll and manipulative shopping patterns.
- Show risk and negative buying signals clearly.
- Keep the product comparison view central.

## Marketplace automation practices

- Start with Shopee.
- Keep TikTok in MVP scope, using physical-phone app automation later.
- Keep Lazada deferred until Shopee and TikTok are stable.
- Never automate final payment confirmation.
- Do not bypass CAPTCHA, OTP, fraud checks, or marketplace security controls.
- Treat login, OTP, CAPTCHA, and payment as user-supervised checkpoints.

## Git practices

- Keep commits focused.
- Do not commit generated local environment folders:
  - `.venv/`
  - `target/`
  - `data/`
  - logs, cookies, sessions, secrets
- Push completed work to the private GitHub repo after validation.
- Before editing, check status:

```powershell
git status --short --branch
```

## Current core commands

Setup:

```powershell
cd "C:\Users\jrom\VS code\Project\onlineShoppingSystem"
uv sync
uv run playwright install chromium
```

Backend smoke test:

```powershell
uv run oss-my detect "https://shopee.com.my/Good-Product-i.12345.67890"
```

Desktop app:

```powershell
cargo run -p oss-my-desktop
```

Full validation:

```powershell
uv run ruff check .
uv run pytest
cargo fmt --check
cargo check -p oss-my-desktop
```
