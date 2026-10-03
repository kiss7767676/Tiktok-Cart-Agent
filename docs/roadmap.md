# Roadmap

## Phase 0: Specification

- Repository structure.
- Requirements.
- Architecture.
- Automation policy.

## Phase 1: Local MVP

- Backend CLI for teachable development and testing.
- Shopee/TikTok link parser.
- Shopee product identity extraction.
- Shopee product metadata extraction.
- SQLite cache.
- UI command contract for the future Rust desktop shell.

## Phase 2: Fast desktop UI foundation

- Rust toolchain installed.
- Create native desktop shell.
- Implement Zed-like layout:
  - left actions
  - middle comparison table
  - right research/details
- Connect UI to Python core through local commands/API.

## Phase 3: TikTok support

- Basic TikTok product resolver.
- Physical-phone automation proof of concept.
- Cross-platform ranking.

## Phase 4: Checkout assist

- Shopee add-to-cart automation.
- TikTok phone checkout handoff.

## Phase 5: Research engine

- Web source aggregation.
- YouTube link extraction.
- Buying-risk summary.
- Optional user-provided AI model/API integration.

## Phase 6: Lazada integration

- Lazada adapter.
- Lazada search/product details.
- Lazada checkout assist if stable.

## Phase 7: Hardening

- Better session handling.
- Adapter test fixtures.
- Layout-change detection.
- Exportable research reports.
