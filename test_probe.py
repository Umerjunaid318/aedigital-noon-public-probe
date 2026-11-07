import unittest,json
from probe import primary,SourceError
from literal_parser import extract
class ProbeTests(unittest.TestCase):
    def product(self):
        return {'sku':'NTEST001V','offer_code':'ae','variants':[{'offers':[{'offer_code':'cheap','is_buyable':True,'partner_code':'p-2','store_name':'Cheaper','price':1069},{'offer_code':'ae','is_buyable':True,'partner_code':'p-98333','store_name':'AEDIGITAL','price':1079}]}]}
    def test_primary_not_cheapest(self):
        r=primary(self.product(),'NTEST001V','p-98333');self.assertEqual(r['winner']['price_aed'],1079);self.assertTrue(r['our_bb']);self.assertEqual(r['alternatives'][0]['price_aed'],1069)
    def test_missing_primary_rejected(self):
        p=self.product();p.pop('offer_code')
        with self.assertRaises(SourceError):primary(p,'NTEST001V','p-98333')
    def test_wrong_sku_rejected(self):
        with self.assertRaises(SourceError):primary(self.product(),'NTEST002V','p-98333')
    def test_exact_seller_match(self):self.assertFalse(primary(self.product(),'NTEST001V','p-983330')['our_bb'])
    def test_literal_data_only(self):self.assertEqual(extract('data:{1.7:0,"2.0":1}','data'),{'1.7':0,'2.0':1})
    def test_duplicate_primary_rejected(self):
        p=self.product();p['variants'].append(p['variants'][0])
        with self.assertRaises(SourceError):primary(p,'NTEST001V','p-98333')
if __name__=='__main__':unittest.main()
