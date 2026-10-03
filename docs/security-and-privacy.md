# Security and Privacy

## Credential handling

- Store passwords/tokens in OS keyring where possible.
- Do not commit `.env`, local config, cookies, phone screenshots, emulator images, or session tokens.
- Encrypt any exported backup containing credentials.
- Mask secrets in logs.

## User payment safety

- Never auto-click final pay/confirm payment.
- Never store card/CVV/payment authorization data.
- Require user interaction for payment method and final confirmation.

## Local-first design

The system should run locally by default. External AI APIs are optional and user-provided.

## Logging policy

Allowed:

- Platform name
- Automation step
- Product ID/title
- Error category
- Timestamp

Not allowed:

- Passwords
- Cookies
- Access tokens
- OTP codes
- Full payment data
- Personal addresses unless explicitly needed and encrypted

## Risk notes

Marketplace automation is brittle. UI changes, account risk systems, and anti-bot protections may interrupt flows. The product should treat those interruptions as normal user-supervised checkpoints.
