# Cost target — 2026-09-10

User benchmark: https://robu.in/product/18650-battery-holder-development-board-compatible-with-raspberry-pi3b-3b/

Listing checked in browser: SKU 890166, ₹198 including GST, in stock, holder included. Listing advertises 1 A charging. Its claimed 6 A output is not independently verified and is not an adopted design requirement.

User wants the mass-manufactured product to cost less than three times comparable existing boards. Against this retail listing, ₹594 including GST is the comparison ceiling, not a manufacturing-cost allowance. Work toward a materially lower price; no finished-board cost has been established. Compare equivalent taxes, holder inclusion, quantity and distribution costs. Cell excluded.

Audit the charger, USB-C controllers, 3.3 V regulator and fuel gauge before committing the next layout. Do not silently remove the three-position charge selector, protection, requested interfaces or battery reporting. Optional host-interface population can be evaluated separately, but changes to delivered functionality require an explicit explanation.

Current layout is an unfinished engineering draft. Horizontal output holes, holder-face LED and mounting notch have been introduced, but routing and mechanical checks remain open. Existing STEP, ZIP, images and validation summary predate these changes. The current holder model is Keystone 1042, not the requested generic Robocraze holder; its replacement footprint still needs verified terminal dimensions.

## Confirmed commercial target — 2026-09-11

User intends to sell at INR400 and wants the assembled board below INR200 at scale. Treat INR200 as a cost ceiling, not a verified estimate. For quotation planning, use 1,000+ units as an explicit provisional scale assumption until an actual production quantity is supplied.

Factory-cost scope: PCB, components, holder, assembly, programming and production test; excludes the cell, enclosure, freight, import costs and tax. Prefer INR150–180 factory cost to leave room for landed costs, packaging, selling fees, returns and warranty. Do not claim that INR400 minus INR200 is net profit.

The current draft does NOT yet meet this target. The corrected priced subset remains around INR347 at the indicative catalogue prices, before unpriced items. Rework procurement and architecture as necessary, obtain quantity-specific quotes, and check the full assembled cost before final layout release. No under-INR200 production cost has been demonstrated.
