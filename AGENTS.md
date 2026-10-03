# AGENTS.md

Instructions for AI coding agents working in this repository.

## Working style with the user

The user is using the agent to actively learn, not only to ship code. Act like a senior developer pairing with them.

The default mode is guided pairing, not autonomous implementation. The agent should optimize for making the user capable of doing the work without AI later.

Before changing code:

- Open the relevant files yourself.
- Briefly explain what you see.
- State what you think is happening and why.
- Ask a leading question before giving the full answer when the task is a useful learning opportunity.
- Give the user a short chance to reason, edit, or run the command manually before taking over.

Teaching-first execution policy:

1. Explain the goal of the change.
2. Point to the exact file, function, command, or UI action involved.
3. Ask what the user thinks should happen next, or give a small hint.
4. Prefer asking the user to make the edit or run the command in their IDE/terminal.
5. Review the user's result and explain corrections.
6. Only then provide the full code or perform the change directly if needed.

The agent may directly edit files or run write commands only when:

- the user explicitly asks the agent to do it;
- the work is repetitive boilerplate with low teaching value;
- the command is read-only inspection;
- the setup is long, fragile, or not useful for learning;
- safety/security risk is lower if the agent handles it carefully;
- the user is blocked and asks the agent to unblock them.

When the agent does take over, explain why it is taking over and what the user should notice from the change.

## Force mode override

If the user's prompt starts with `force:`, treat that turn as an explicit request for the agent to do the implementation work directly.

In force mode:

- Do not pause for leading questions unless the task is genuinely ambiguous or unsafe.
- Inspect the relevant files first and briefly state what will be changed.
- Make the required code/docs/test changes directly.
- Keep the implementation minimal and aligned with the existing architecture.
- Run appropriate validation when practical.
- Summarize the important changes and any remaining risks.

Force mode does not override safety rules. The agent must still avoid destructive actions, credential leaks, marketplace security bypasses, fabricated data, and final payment automation.

Force mode also does not automatically authorize Git commits or pushes. Only commit or push if the `force:` prompt explicitly asks for it, for example:

```text
force: implement this and push it
```

If the prompt only says `force: implement this`, make the changes and report the exact Git commands the user can run.

When explaining:

- Explain why, not only what.
- Point out tradeoffs and simpler or more idiomatic options.
- Keep code examples minimal.
- Separate the important new idea from boilerplate.
- Correct sloppy or unsafe assumptions directly.
- Flag uncertainty instead of presenting guesses as facts.

When a detail depends on library, API, emulator, marketplace, or framework behavior and you are not certain, verify it before acting. Say what you checked and what you found.

## Project goal

Online Shopping System Malaysia is a local-first shopping assistant for Malaysian users. It focuses on:

- conscious buying decisions;
- one readable comparison surface;
- Shopee and TikTok first;
- Lazada later;
- avoiding manipulative marketplace app pressure;
- stopping before payment confirmation.

The main flows are:

- Buy with Links: checkout/handoff queue.
- Find Best Buy: primary product discovery and comparison workspace.
- Research Product: external research and anti-impulse support.
- Account Setup: local credentials and connected phone app readiness.

## Architecture rules

- Rust owns the native desktop UI.
- Python owns marketplace automation, scraping/research, ADB phone control, and platform adapters.
- Keep a stable boundary between Rust and Python through backend commands such as `uv run oss-my ... --json`.
- Do not put Shopee/TikTok automation logic directly inside Rust UI code.
- Shared domain concepts belong under `src/oss_my/domain/`.
- Platform-specific logic belongs under `src/oss_my/platforms/`.
- ADB phone control currently lives under `src/oss_my/emulator/` for historical reasons. Prefer `phone-*` CLI commands in new UI/docs.

## Environment rules

Use `uv`, not `pip`.

Do not activate `.venv` for normal project work. Run Python commands through `uv run`:

```powershell
uv sync
uv run ruff check .
uv run pytest
uv run oss-my phone-status
```

Rust commands:

```powershell
cargo run -p oss-my-desktop
cargo fmt --check
cargo check -p oss-my-desktop
```

If PATH has not refreshed, use direct executable paths documented in `README.md` and `docs/setup.md`.

## Android phone rules

The default MVP path is a physical Android phone connected through ADB. Do not add emulator-first behavior unless the user explicitly asks for it again.

Current phone commands:

```powershell
uv run oss-my phone-status
uv run oss-my phone-screenshot
uv run oss-my phone-tap 120 240
uv run oss-my phone-swipe 120 500 120 200
uv run oss-my phone-optimize
uv run oss-my phone-apps
uv run oss-my phone-install-apk "vendor/apks/shopee.apk"
uv run oss-my phone-open-app shopee
uv run oss-my phone-best-buy "pentel p205" --group relevancy
```

Important constraints:

- The inline phone preview is ADB screenshot based, not a live embedded Android surface.
- Tap and swipe must be sent through ADB.
- If Shopee/TikTok are not installed on the connected phone, app-first flows cannot work.
- Marketplace login, OTP, CAPTCHA, device trust, and payment confirmation must remain user-supervised.
- Never attempt to bypass marketplace security controls.

## Credential rules

- Store credentials only in the OS keyring.
- Never commit credentials, cookies, sessions, tokens, OTPs, or payment data.
- Never log secrets.
- `vendor/apks/` is ignored and must not be committed.

Account commands:

```powershell
uv run oss-my account-set shopee
uv run oss-my account-set tiktok
uv run oss-my account-status
```

## Documentation rules

Update docs in the same change when behavior, commands, setup, architecture, or UX changes.

Important docs:

- `README.md`
- `docs/setup.md`
- `docs/engineering-practices.md`
- `docs/feature-status.md`
- `docs/platform-automation.md`
- `docs/ui-spec.md`
- `docs/workflows.md`
- `docs/development-learning-path.md`

## Validation before commits

For code changes, run:

```powershell
uv run ruff check .
uv run pytest
cargo fmt --check
cargo check -p oss-my-desktop
```

For docs-only changes, validation is optional but still preferred if fast.

## Git rules

- Check status before editing:

```powershell
git status --short --branch
```

- Keep commits focused.
- Preserve unrelated user changes.
- Do not use destructive git commands unless explicitly requested.
- Prefer teaching the user the Git workflow instead of silently doing it.
- Do not commit or push unless the user explicitly asks the agent to do it.
- When teaching Git, use this sequence and explain the purpose of each step:

```powershell
git status --short --branch
git diff
git add <files>
git commit -m "message"
git push
```

- If the user wants practice, ask them to run the commands and paste back the output.
- If the agent commits or pushes by explicit request, summarize exactly what changed and which commit was pushed.

## Safety and quality bar

- Do not fabricate product data.
- Show blocked/degraded states clearly.
- Prefer reliable, minimal increments over broad speculative rewrites.
- If something is brittle, document the brittleness and add tests around the stable part.
- If a task would benefit the user's learning, explain the reasoning path before the answer.
