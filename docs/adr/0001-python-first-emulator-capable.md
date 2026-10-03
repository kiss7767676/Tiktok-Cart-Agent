# ADR 0001: Python-first, emulator-capable architecture

## Status

Accepted

## Context

The system needs marketplace automation, product search, product comparison, and research aggregation. Most work is network, browser, and device automation rather than CPU-heavy processing.

TikTok Shop may require Android app automation because web checkout/payment may not be sufficient.

## Decision

Use Python as the default implementation language. Use Rust only if profiling identifies a specific CPU-bound bottleneck.

Use platform adapters so each marketplace can choose the best automation backend:

- Playwright for web-capable flows.
- Redroid/Appium/uiautomator2 for app-only flows.

## Consequences

Benefits:

- Faster development.
- Strong automation ecosystem.
- Easier integration with AI APIs and search tooling.
- Good enough performance for I/O-heavy tasks.

Tradeoffs:

- Emulator automation can be brittle.
- Strong test fixtures are required for platform adapters.
- Some low-level device operations may need OS-specific setup.
