# Workflows

## Startup

1. Load local settings.
2. Check platform login/session status.
3. Show actions:
   - Buy with Links
   - Find Best Buy
   - Account Setup
   - View Previous Research

## Buy with Links

1. User adds links from Find Best Buy or pastes checkout links directly.
2. Sidebar shows the number of links queued.
3. System normalizes URLs and detects platform.
4. User prepares checkout handoff.
5. System selects automation adapter when available.
6. System logs in if necessary.
7. System adds items to cart when platform automation is implemented.
8. System navigates to checkout/cart handoff.
9. User manually chooses payment method and confirms purchase.

## Find Best Buy

1. User enters keyword or product description.
2. Optional AI expansion converts intent into search terms and must-have filters.
3. User selects platforms and budget. Shopee is implemented first.
4. User chooses Most Relevant or Top Sales.
5. App checks the connected Android phone through ADB.
6. User checks installed app status in Account Setup.
7. User checks phone status and uses the inline phone preview.
8. System opens Shopee search inside the connected Android phone.
9. System extracts visible product text from the Android UI hierarchy.
10. UI displays the inline phone preview on the left and extracted product rows on the right.
11. User can send supervised tap/swipe controls through ADB.
12. User can refresh the screenshot after phone interaction.
13. User can filter by platform.
14. User can select a product row to inspect details/risk notes.
15. User can add chosen product links to Buy with Links.
16. User opens product research page or proceeds to checkout assist.

If no phone is connected, the app shows the device status and does not fabricate product data.

## Research Page

1. User selects a product or product category.
2. System runs the own Google scraper.
3. System attempts to extract Google AI Overview from returned HTML.
4. System extracts parseable Google sources/snippets.
5. System also shows Google/YouTube/review/complaint source links.
6. User decides whether to buy, compare alternatives, or stop.
