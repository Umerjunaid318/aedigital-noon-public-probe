"""Public-only Noon source acceptance test. Standard library; no credentials or writes."""
import os,re,json,time,threading,math
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from literal_parser import extract

class SourceError(Exception):pass
class PublicHTTP:
    def __init__(self):self.lock=threading.Lock();self.next=0;self.stopped=threading.Event()
    def get(self,url):
        with self.lock:
            wait=max(0,self.next-time.monotonic());self.next=max(self.next,time.monotonic())+.5
        if wait:self.stopped.wait(wait)
        if self.stopped.is_set():raise SourceError('Source access stopped; no retry')
        try:
            with urlopen(Request(url,headers={'User-Agent':'Public-Noon-Access-Test/1.0'}),timeout=30) as response:
                b=response.read(8*1024*1024+1)
                if len(b)>8*1024*1024:raise SourceError('Response too large')
                text=b.decode('utf-8')
        except HTTPError as exc:
            if exc.code in (401,403,429):self.stopped.set()
            raise SourceError('Public HTTP '+str(exc.code)) from None
        except SourceError:raise
        except Exception as exc:raise SourceError('Public request failed: '+type(exc).__name__) from None
        title=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S)
        if (title and re.search(r'verify.*human|checking your browser|just a moment|access denied|captcha',title[1],re.I)) or (len(text)<50000 and re.search(r'verify you are human|px-captcha|cdn-cgi/challenge-platform|captcha-delivery\.com',text,re.I)):
            self.stopped.set();raise SourceError('Verification response; no bypass')
        return text

def primary(p,sku,seller):
    if not isinstance(p,dict) or p.get('sku')!=sku:raise SourceError('Missing/mismatched canonical product')
    code=p.get('offer_code');variants=p.get('variants')
    if not code or not isinstance(variants,list):raise SourceError('Missing default offer')
    matches=[v for v in variants if isinstance(v,dict) and isinstance(v.get('offers'),list) and any(isinstance(o,dict) and o.get('offer_code')==code for o in v['offers'])]
    if len(matches)!=1:raise SourceError('Ambiguous default variant')
    offers=[o for o in matches[0]['offers'] if isinstance(o,dict) and o.get('is_buyable') is True]
    selected=[o for o in offers if o.get('offer_code')==code]
    if len(selected)!=1:raise SourceError('Unavailable/ambiguous default offer')
    def compact(o):
        price=o.get('sale_price') if o.get('sale_price') is not None else o.get('price')
        if isinstance(price,bool) or not isinstance(price,(int,float)) or not math.isfinite(price) or price<0 or not isinstance(o.get('partner_code'),str) or not o.get('store_name'):raise SourceError('Incomplete offer data')
        return {'seller':o['store_name'],'seller_id':o['partner_code'],'price_aed':price}
    winner=compact(selected[0]);seen={winner['seller_id']};alternatives=[]
    for o in offers:
        if o.get('partner_code') not in seen:alternatives.append(compact(o));seen.add(o['partner_code'])
    return {'winner':winner,'our_bb':winner['seller_id']==seller,'alternatives':alternatives[:2]}

def catalog(http,seller,executor=ThreadPoolExecutor):
    base='https://www.noon.com/uae-en/'+seller+'/'
    first=http.get(base+'?limit=50&page=1');total=extract(first,'nbHits');pages=extract(first,'nbPages')
    if isinstance(total,bool) or not isinstance(total,int) or not 1<=total<=5000:raise SourceError('Invalid public catalog count')
    if isinstance(pages,bool) or not isinstance(pages,int) or not 1<=pages<=100:raise SourceError('Invalid public catalog pagination')
    records={};offer_ids=set();store_names=set()
    def accept(html,brand=None):
        hits=extract(html,'hits')
        if not isinstance(hits,list):raise SourceError('Missing public catalog hits')
        for hit in hits:
            if not isinstance(hit,dict) or not isinstance(hit.get('sku'),str) or not re.fullmatch(r'[A-Z0-9_-]{6,40}',hit['sku']):raise SourceError('Invalid public SKU')
            if hit.get('partner_code') not in (None,seller):raise SourceError('Store identity mismatch')
            if not hit.get('store_name'):raise SourceError('Missing store identity')
            if brand and hit.get('brand_code')!=brand:raise SourceError('Brand navigation not applied')
            records[hit['sku']]=True;offer_ids.add(hit.get('offer_code') or hit.get('catalog_sku') or hit['sku']);store_names.add(hit['store_name'])
    accept(first);jobs=[]
    if total>500:
        facets=extract(first,'facets')
        if not isinstance(facets,list):raise SourceError('Missing brand navigation')
        codes=[x.get('code') for f in facets if isinstance(f,dict) and f.get('code')=='brand' for x in f.get('data',[]) if isinstance(x,dict)]
        if not codes or any(not isinstance(c,str) or not re.fullmatch(r'[a-z0-9_-]+',c) for c in codes):raise SourceError('Invalid brand navigation')
        urls=[(c,base+c+'/') for c in dict.fromkeys(codes)]
        with executor(max_workers=4) as pool:
            for (brand,url),html in zip(urls,pool.map(http.get,[u+'?limit=50&page=1' for _,u in urls])):
                count=extract(html,'nbHits');n=extract(html,'nbPages')
                if isinstance(count,bool) or not isinstance(count,int) or not 0<=count<=500 or isinstance(n,bool) or not isinstance(n,int) or not 0<=n<=10:raise SourceError('Unsupported brand partition')
                accept(html,brand);jobs.extend((url+f'?limit=50&page={page}',brand) for page in range(2,max(n,(count+49)//50)+1))
    else:jobs=[(base+f'?limit=50&page={page}',None) for page in range(2,max(pages,(total+49)//50)+1)]
    with executor(max_workers=4) as pool:
        for (_,brand),html in zip(jobs,pool.map(http.get,[u for u,_ in jobs])):accept(html,brand)
    if len(store_names)!=1:raise SourceError('Ambiguous storefront display identity')
    info={'reported_offers':total,'distinct_offers':len(offer_ids),'distinct_skus':len(records),'store':next(iter(store_names))}
    if len(offer_ids)!=total:raise SourceError('Catalog changed or coverage incomplete: '+json.dumps(info))
    return info

def main():
    seller=os.environ.get('PUBLIC_SELLER','p-98333');sku=os.environ.get('PUBLIC_SKU','N70376247V')
    if not re.fullmatch(r'p-[0-9]{1,12}',seller) or not re.fullmatch(r'[A-Z0-9_-]{6,40}',sku):raise SourceError('Invalid public test identifiers')
    http=PublicHTTP();start=time.monotonic()
    print('PUBLIC_TEST_STARTED: No credentials, Google access, marketplace writes or recurring schedule.',flush=True)
    p=extract(http.get('https://www.noon.com/uae-en/'+sku+'/p/'),'product');result=primary(p,sku,seller)
    print('CANONICAL_DEFAULT_OFFER_OK',json.dumps(result),flush=True)
    coverage=catalog(http,seller)
    if seller=='p-98333' and coverage['store']!='AEDIGITAL':raise SourceError('AEDIGITAL store identity mismatch')
    print('PUBLIC_ACCESS_PASS',json.dumps({'catalog':coverage,'elapsed_seconds':round(time.monotonic()-start,1),'checked_at':datetime.now(timezone.utc).isoformat()}),flush=True)
    print('This proves source access on this runner for this test, not continuous monitoring or a Sheets connection.',flush=True)
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('PUBLIC_ACCESS_FAILED:',str(exc) if isinstance(exc,SourceError) else type(exc).__name__,flush=True)
        raise SystemExit(1)
