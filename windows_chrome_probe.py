"""One public page using installed Chrome on Windows, normal rendering, no profile reuse."""
import re,json
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=False)
        try:
            context=browser.new_context();page=context.new_page()
            print('TEST: Installed Google Chrome on Windows. Normal JavaScript. Default HTTPS certificate validation. No keys, account login, proxy or Sheet writes.',flush=True)
            response=page.goto('https://www.noon.com/uae-en/N70376247V/p/',wait_until='domcontentloaded',timeout=60000)
            print('STATUS:',response.status if response else None,flush=True)
            if not response or response.status!=200:raise RuntimeError('No successful public response')
            title=page.title()
            if re.search(r'verify.*human|checking your browser|just a moment|access denied|captcha',title,re.I):raise RuntimeError('Verification response; stopping without bypass')
            page.locator('h1').wait_for(state='visible',timeout=20000)
            print('TITLE:',page.locator('h1').inner_text(),flush=True)
            seller=page.get_by_role('link',name=re.compile(r'^Sold by '))
            href=seller.get_attribute('href');print('MAIN_SELLER_LINK:',href,flush=True)
            page.get_by_role('button',name=re.compile(r'^More offers from other sellers')).click(timeout=15000)
            cards=page.locator('a[class*="_card_"]').filter(has=page.locator('[class*="_sellerName_"]'))
            cards.first.wait_for(state='visible',timeout=15000)
            print('RENDERED_OFFERS:',json.dumps(cards.evaluate_all("els=>els.map(el=>({selected:!!el.querySelector('[class*=\"_selectedTag_\"]'),seller:el.querySelector('[class*=\"_sellerName_\"]')?.textContent,price:el.querySelector('strong')?.textContent,href:el.getAttribute('href')}))")),flush=True)
            print('WINDOWS_CHROME_SOURCE_PASS',flush=True)
            context.close()
        finally:browser.close()
if __name__=='__main__':
    try:main()
    except Exception as e:
        codes=re.findall(r'net::ERR_[A-Z0-9_]+',str(e))
        print('WINDOWS_CHROME_SOURCE_FAIL:',type(e).__name__,' '.join(codes),flush=True)
        raise SystemExit(1)
