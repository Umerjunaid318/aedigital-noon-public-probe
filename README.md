# Public Noon source-access probe

This repository tests **public data access only** from a standard Linux GitHub Actions runner. It is not the finished monitoring system.

- Manual `workflow_dispatch` only: no push trigger or recurring schedule.
- No Google credentials, spreadsheet identifiers, private inventory or customer data.
- No Noon API keys, account login, browser JavaScript, CAPTCHA handling, proxy switching, disabled certificate checks or seller-forcing URL parameters.
- No Google Sheets, price, stock or marketplace writes.
- Standard library only; one shared maximum of two request starts per second.
- A denial, verification response or source failure produces a failed run rather than bypass or retry.
- Logs contain only public offer information, aggregate catalog counts and test status. Raw pages and inventory lists are not saved as artifacts.

## Run

Actions → **Public Noon access test** → **Run workflow**. Default inputs refer to public AEDIGITAL storefront p-98333 and public product N70376247V. Repository inputs are validated before constructing URLs.

The test first matches the canonical product's explicit default offer to one active offer in one variant. It never picks the lowest-price seller as the Buy Box. It then scans the public storefront, using normal public brand navigation when the broad result set is capped at 500. Unique offers and SKUs are counted separately. Inconsistent coverage fails the test.

`PUBLIC_ACCESS_PASS` establishes access from that runner at that time only. It does not establish future availability, a 10-minute service, stock-zero/OOS status or a Google Sheets connection. Scheduled jobs must not be enabled until access and a separate credential-safe integration are verified.

To test locally: `python3 -m unittest -q test_probe.py`. No external dependencies or credentials are required for offline tests.

Do not upload keys or private data here. A standard public runner is the intended free test environment; larger/paid runners are not used.
