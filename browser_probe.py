"""Ordinary Chromium with normal page rendering. No credentials or security bypass."""
import os,re,time,json
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
from probe import SourceError,primary,catalog
from literal_parser import extract

class SequentialPool:
    def __init__(self,**kwargs):pass
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def map(self,fn,values):return map(fn,values)

class BrowserHTTP:
    def __init__(self,context):self.context=context;self.next=0;self.stopped=False
    def get(self,url):
        if self.stopped:raise SourceError('Source access stopped; no retry')
        if not url.startswith('https://www.noon.com/uae-en/') or '?' in url and not re.fullmatch(r'https://www\.noon\.com/uae-en/[a-zA-Z0-9_/-]+\?limit=50&page=[0-9]+',url):raise SourceError('Unsupported public URL')
        time.sleep(max(0,self.next-time.monotonic()));self.next=time.monotonic()+.5
        page=self.context.new_page()
        try:
            response=page.goto(url,wait_until='domcontentloaded',timeout=45000)
            if response is None:raise SourceError('No document response')
            if response.status in (401,403,429):self.stopped=True;raise SourceError('Source HTTP '+str(response.status)+'; no retry')
            if response.status!=200:raise SourceError('Source HTTP '+str(response.status))
            if not response.url.startswith('https://www.noon.com/uae-en/'):raise SourceError('Unexpected redirect')
            page.locator('body').wait_for(state='visible',timeout=15000)
            body=page.content().encode('utf-8')
            if len(body)>8*1024*1024:raise SourceError('Response too large')
            text=body.decode('utf-8');title=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S)
            if (title and re.search(r'verify.*human|checking your browser|just a moment|access denied|captcha',title[1],re.I)) or (len(text)<50000 and re.search(r'verify you are human|px-captcha|cdn-cgi/challenge-platform|captcha-delivery\.com',text,re.I)):
                self.stopped=True;raise SourceError('Verification response; no bypass')
            return text
        except SourceError:raise
        except Exception as exc:
            code=re.search(r'net::ERR_[A-Z0-9_]+',str(exc))
            raise SourceError('Browser request failed: '+type(exc).__name__+((' '+code.group(0)) if code else '')) from None
        finally:page.close()

def main():
    seller='p-98333';sku='N70376247V';started=time.monotonic()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--disable-http2'])
        try:
            context=browser.new_context(java_script_enabled=True)
            http=BrowserHTTP(context)
            print('BROWSER_TEST_STARTED: Standard Chromium; HTTP/2 disabled for this isolated test; HTTPS certificate validation unchanged; no keys or Sheet writes.',flush=True)
            html=http.get('https://www.noon.com/uae-en/'+sku+'/p/')
            print('DOCUMENT_RECEIVED:',len(html),'characters',flush=True)
            product=extract(html,'product');result=primary(product,sku,seller)
            print('CANONICAL_DEFAULT_OFFER_OK',json.dumps(result),flush=True)
            coverage=catalog(http,seller,executor=SequentialPool)
            if coverage['store']!='AEDIGITAL':raise SourceError('Store identity mismatch')
            print('BROWSER_ACCESS_PASS',json.dumps({'catalog':coverage,'elapsed_seconds':round(time.monotonic()-started,1),'checked_at':datetime.now(timezone.utc).isoformat()}),flush=True)
            print('Source access verified for this run only; recurring monitor remains disabled.',flush=True)
            context.close()
        finally:browser.close()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('BROWSER_ACCESS_FAILED:',str(exc) if isinstance(exc,SourceError) else type(exc).__name__,flush=True)
        raise SystemExit(1)
