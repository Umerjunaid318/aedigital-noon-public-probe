# Public Noon source-access probe

This repository tests **public data access only** from a standard Linux GitHub Actions runner. It is not the finished monitoring system.

- No recurring schedule. The HTTP test is manual; the standard-Chromium test also runs once when its code/workflow changes on main.
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

## First hosted test result

On 7 November 2026, the standard GitHub Linux runner passed all six offline tests, but the first canonical public product request timed out after approximately 30 seconds. No valid live source data was obtained. Full catalog access was not reached. Recurring monitoring remains disabled and no Google key was requested or installed.

Run: https://github.com/Umerjunaid318/aedigital-noon-public-probe/actions/runs/42380089691

## Standard Chromium test

The second source test uses ordinary headless Chromium with JavaScript disabled. It parses only the original document response. No credentials, profiles, fingerprint modifications, network switching, challenge bypass or Sheets writes are used. The workflow uses the official Playwright package/browser installer on a standard public Linux runner. A valid canonical offer and complete catalog must both pass before this approach is accepted.

### Standard Chromium result

The standard GitHub-hosted Chromium test did not obtain a valid document. The browser navigation failed before product parsing. This does not establish a specific bot block or its cause. Both hosted approaches remain unverified for live collection; no recurring schedule or Google connection has been enabled.
Run: https://github.com/Umerjunaid318/aedigital-noon-public-probe/actions/runs/42381115186
