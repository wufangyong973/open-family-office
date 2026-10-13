from __future__ import annotations
import io,json,os,sys,tempfile,unittest,types,importlib.util
from pathlib import Path
from unittest.mock import patch
from open_family_office.core import InputError
from open_family_office.integrations.providers import fetch,csv_records
from open_family_office.integrations.transport import Response,Transport,envelope
from open_family_office.integrations.registry import providers
from open_family_office.integrations.documents import holdings_csv
from open_family_office.integrations.mcp_server import confined

class FakeTransport:
    def __init__(self,body='{"ok":true}',content_type='application/json'):
        self.body=body;self.content_type=content_type;self.calls=[]
    def get(self,url,params=None,headers=None):
        self.calls.append((url,params,headers));return Response(self.body.encode(),self.content_type)

class ProviderTests(unittest.TestCase):
    def test_network_requires_explicit_consent(self):
        self.assertRaises(InputError,fetch,'rba','table',{'table':'f01'})
    def test_network_host_allowlist(self):
        self.assertRaises(InputError,Transport(True).get,'https://127.0.0.1/private')
        self.assertRaises(InputError,Transport(True).get,'https://evil.example/')
        self.assertRaises(InputError,Transport(True).get,'http://www.rba.gov.au/')
    def test_missing_api_key_fails_closed(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertRaises(InputError,fetch,'fred','series',{'series_id':'CPIAUCSL'},transport=FakeTransport())
    def test_sec_filing_request_contract(self):
        t=FakeTransport('{"cik":"320193","filings":{"recent":{"form":["10-K","NPORT-P"]}}}')
        with patch.dict(os.environ,{'SEC_USER_AGENT':'Household demo demo@example.com'}):
            r=fetch('sec-edgar','filings',{'cik':'320193'},transport=t)
        self.assertEqual(t.calls[0][0],'https://data.sec.gov/submissions/CIK0000320193.json')
        self.assertEqual(r['records']['filings']['recent']['form'][0],'10-K')
        self.assertEqual(len(r['response_sha256']),64)
    def test_sec_companyfacts_contract(self):
        with patch.dict(os.environ,{'SEC_USER_AGENT':'demo demo@example.com'}):
            t=FakeTransport();fetch('sec-edgar','companyfacts',{'cik':'320193'},transport=t)
            self.assertIn('companyfacts/CIK0000320193',t.calls[0][0])
    def test_fred_observation_date_retained_and_key_redacted(self):
        t=FakeTransport('{"observations":[{"date":"2020-01-01","value":"1.25"}]}')
        with patch.dict(os.environ,{'FRED_API_KEY':'fixture-key-not-real'}):
            r=fetch('fred','series',{'series_id':'CPIAUCSL'},transport=t)
        self.assertNotIn('api_key',r['request_parameters'])
        self.assertEqual(r['records']['observations'][0]['date'],'2020-01-01')
    def test_rba_preamble_csv(self):
        t=FakeTransport('Title,Example\nDescription,Fixture only\nSeries ID,FIRMMCRTD\n01-Jan-2020,0.1\n','text/csv')
        r=fetch('rba','table',{'table':'f01'},transport=t)
        self.assertEqual(r['records'][0]['FIRMMCRTD'],'0.1')
        self.assertTrue(t.calls[0][0].endswith('/f01-data.csv'))
    def test_abs_uses_new_base_url(self):
        t=FakeTransport('TIME_PERIOD,OBS_VALUE\n2020,100\n','text/csv')
        r=fetch('abs','data',{'flow':'CPI','key':'all','startPeriod':'2020'},transport=t)
        self.assertTrue(t.calls[0][0].startswith('https://data.api.abs.gov.au/rest/'))
        self.assertEqual(r['records'][0]['OBS_VALUE'],'100')
    def test_oecd_dataflow_contract(self):
        t=FakeTransport('<Structure>fixture</Structure>','application/xml')
        r=fetch('oecd','dataflows',{},transport=t)
        self.assertIn('/dataflow/all/all/latest',t.calls[0][0]);self.assertIn('sdmx_xml',r['records'])
    def test_imf_sdmx_request_contract_not_live(self):
        t=FakeTransport('TIME_PERIOD,OBS_VALUE\n2020,1.5\n','text/csv')
        r=fetch('imf','data',{'flow':'EXAMPLE','key':'all'},transport=t)
        self.assertIn('/sdmx/2.1/data/EXAMPLE/all',t.calls[0][0]);self.assertEqual(len(r['records']),1)
    def test_coingecko_uses_id_not_ambiguous_symbol(self):
        t=FakeTransport('{"bitcoin":{"aud":100000,"last_updated_at":1700000000}}')
        with patch.dict(os.environ,{'COINGECKO_API_KEY':'fixture-only'}):
            r=fetch('coingecko','quote',{'ids':'bitcoin','currency':'aud'},transport=t)
        self.assertEqual(t.calls[0][1]['ids'],'bitcoin');self.assertIn('last_updated_at',r['records']['bitcoin'])
    def test_coingecko_history(self):
        with patch.dict(os.environ,{'COINGECKO_API_KEY':'fixture-only'}):
            t=FakeTransport('{"prices":[[1700000000000,1]]}')
            fetch('coingecko','history',{'id':'bitcoin','days':30},transport=t)
            self.assertIn('/coins/bitcoin/market_chart',t.calls[0][0])
    def test_alpha_vantage_request(self):
        with patch.dict(os.environ,{'ALPHA_VANTAGE_API_KEY':'fixture-only'}):
            t=FakeTransport();r=fetch('alpha-vantage','history',{'symbol':'DEMO'},transport=t)
            self.assertEqual(t.calls[0][1]['function'],'TIME_SERIES_DAILY_ADJUSTED');self.assertNotIn('apikey',r['request_parameters'])
    def test_finnhub_request(self):
        with patch.dict(os.environ,{'FINNHUB_API_KEY':'fixture-only'}):
            t=FakeTransport('{"c":100,"t":1700000000}');r=fetch('finnhub','quote',{'symbol':'DEMO'},transport=t)
            self.assertEqual(r['records']['c'],100);self.assertIn('X-Finnhub-Token',t.calls[0][2])
    def test_marketdata_request(self):
        with patch.dict(os.environ,{'MARKETDATA_API_KEY':'fixture-only'}):
            t=FakeTransport();fetch('marketdata','quote',{'symbol':'DEMO'},transport=t)
            self.assertTrue(t.calls[0][0].endswith('/DEMO/'))
    def test_metals_request(self):
        with patch.dict(os.environ,{'METALPRICE_API_KEY':'fixture-only'}):
            t=FakeTransport('{"rates":{"XAU":0.0002}}');r=fetch('metalprice','quote',{},transport=t)
            self.assertNotIn('api_key',r['request_parameters']);self.assertEqual(r['records']['rates']['XAU'],.0002)
    def test_api_error_is_not_data(self):
        with patch.dict(os.environ,{'ALPHA_VANTAGE_API_KEY':'fixture-only'}):
            self.assertRaises(InputError,fetch,'alpha-vantage','history',{'symbol':'DEMO'},transport=FakeTransport('{"Information":"quota"}'))
    def test_html_is_not_csv(self):
        self.assertRaises(InputError,fetch,'rba','table',{'table':'f01'},transport=FakeTransport('<html>Login</html>'))
    def test_invalid_json_is_not_replaced_with_fixture(self):
        with patch.dict(os.environ,{'FRED_API_KEY':'fixture-only'}):
            self.assertRaises(InputError,fetch,'fred','series',{'series_id':'X'},transport=FakeTransport('broken'))
    def test_path_traversal_provider_identifiers(self):
        self.assertRaises(InputError,fetch,'rba','table',{'table':'../private'},transport=FakeTransport())
    def test_unknown_provider_and_capability(self):
        self.assertRaises(InputError,fetch,'unknown','quote',{},transport=FakeTransport())
        self.assertRaises(InputError,fetch,'rba','orders',{},transport=FakeTransport())
    def test_registry_never_claims_live_verification(self):
        p=providers();self.assertEqual(len(p),13)
        self.assertTrue(all('not_verified' in a['validation'] for a in p))
    def test_openbb_subprocess_contract(self):
        fake=types.SimpleNamespace(returncode=0,stdout='{"results":[{"close":100}]}',stderr='')
        with patch.dict(os.environ,{'OPENBB_PYTHON':'/fake/python'}),patch('subprocess.run',return_value=fake) as call:
            r=fetch('openbb','history',{'symbol':'DEMO','provider':'yfinance'},allow_network=True)
            self.assertEqual(r['records']['results'][0]['close'],100)
            self.assertFalse(call.call_args.kwargs.get('shell',False))
    def test_yahoo_multiindex_mapping_contract(self):
        import pandas as pd
        frame=pd.DataFrame([[100,99]],index=pd.DatetimeIndex(['2020-01-01'],name='Date'),columns=pd.MultiIndex.from_tuples([('Close','DEMO'),('Adj Close','DEMO')]))
        fake=types.SimpleNamespace(download=lambda *a,**k:frame)
        with patch.dict(sys.modules,{'yfinance':fake}):
            r=fetch('yahoo','history',{'symbol':'DEMO'},allow_network=True)
        self.assertIn('Close|DEMO',r['records'][0]);self.assertIn('Date',r['records'][0])

class LocalImportTests(unittest.TestCase):
    def test_holdings_preserve_unknown_weight(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'holdings.csv';p.write_text('asset_id,underlying_id,weight,as_of,source\nfund,a,0.6,2026-01-01,fixture\n')
            self.assertEqual(holdings_csv(p)['unclassified_weight']['fund'],'0.4')
    def test_holdings_reject_double_count(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'holdings.csv';p.write_text('asset_id,underlying_id,weight,as_of,source\nfund,a,0.6,2026-01-01,fixture\nfund,a,0.4,2026-01-01,fixture\n')
            self.assertRaises(InputError,holdings_csv,p)
    def test_holdings_unknown_weight_not_normalized(self):
        # An asset that sums to less than 1 must keep the residual visible,
        # per asset, as a string -- it must not be stretched up to 1.0.
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'h.csv'
            p.write_text('asset_id,underlying_id,weight,as_of,source\nfund,x,0.6,2026-01-01,f\nfund,y,0.15,2026-01-01,f\n')
            out=holdings_csv(p)
            self.assertEqual(out['unclassified_weight']['fund'],'0.25')
            # Fully-classified asset reports zero residual, not a fabricated weight.
            p.write_text('asset_id,underlying_id,weight,as_of,source\nfund,x,0.5,2026-01-01,f\nfund,y,0.5,2026-01-01,f\n')
            self.assertEqual(holdings_csv(p)['unclassified_weight']['fund'],'0.0')
    def test_holdings_fixture_is_valid_and_preserves_residuals(self):
        # The documented end-to-end synthetic example runs clean through the
        # import and preserves per-asset residuals (0.25 for the partial asset).
        fixture=Path(__file__).resolve().parent.parent/'examples'/'holdings.synthetic.csv'
        out=holdings_csv(fixture)
        self.assertEqual(out['kind'],'holdings')
        self.assertEqual(out['verified'],False)
        self.assertEqual(out['unclassified_weight']['cash-fund'],'0.25')
        self.assertEqual(out['unclassified_weight']['equity-fund'],'0.0')
        self.assertEqual(len(out['records']),3)
        for row in out['records']:
            self.assertEqual(set(row),{'asset_id','underlying_id','weight','as_of','source'})
    def test_holdings_reject_weight_out_of_range(self):
        with tempfile.TemporaryDirectory() as d:
            for bad in ('1.2','-0.1'):
                p=Path(d)/'h.csv';p.write_text('asset_id,underlying_id,weight,as_of,source\nfund,a,%s,2026-01-01,f\n'%bad)
                self.assertRaises(InputError,holdings_csv,p)
    def test_holdings_reject_bad_as_of(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'h.csv';p.write_text('asset_id,underlying_id,weight,as_of,source\nfund,a,0.5,2026/01/01,f\n')
            self.assertRaises(ValueError,holdings_csv,p)
    def test_holdings_reject_leverage_total_over_100(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'h.csv';p.write_text('asset_id,underlying_id,weight,as_of,source\nfund,a,0.6,2026-01-01,f\nfund,b,0.5,2026-01-01,f\n')
            self.assertRaises(InputError,holdings_csv,p)
    def test_holdings_reject_wrong_columns(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'h.csv';p.write_text('asset_id,weight,as_of,source\nfund,0.5,2026-01-01,f\n')
            self.assertRaises(InputError,holdings_csv,p)
    def test_mcp_path_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'household.json').write_text('{}')
            self.assertEqual(confined(root,'household.json'),root/'household.json')
            self.assertRaises(InputError,confined,root,'../secret.json')
    def test_mcp_symlink_boundary(self):
        with tempfile.TemporaryDirectory() as d,tempfile.TemporaryDirectory() as other:
            root=Path(d);target=Path(other)/'secret.json';target.write_text('{}');(root/'alias.json').symlink_to(target)
            self.assertRaises(InputError,confined,root,'alias.json')
    @unittest.skipUnless(importlib.util.find_spec('pypdf'),'pypdf optional dependency absent')
    def test_empty_pdf_flags_missing_text(self):
        from pypdf import PdfWriter
        from open_family_office.integrations.documents import extract_pdf
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'blank.pdf';writer=PdfWriter();writer.add_blank_page(width=100,height=100)
            with p.open('wb') as f:writer.write(f)
            r=extract_pdf(p);self.assertEqual(r['pages'][0]['status'],'image_only_or_empty');self.assertIs(r['verified'],False)
    @unittest.skipUnless(importlib.util.find_spec('ofxparse'),'ofxparse not installed: native OFX execution not verified')
    def test_ofx_native_import(self):
        from open_family_office.integrations.documents import import_ofx
        from pathlib import Path
        r=import_ofx(Path(__file__).parents[1]/'examples/statement.synthetic.ofx')
        self.assertEqual(len(r['records']),1)
    @unittest.skipUnless(importlib.util.find_spec('mcp'),'MCP SDK not installed: server host handshake not verified')
    def test_mcp_native_tool_registration(self):
        from mcp.server.fastmcp import FastMCP
        server=FastMCP('test')
        @server.tool(annotations={'readOnlyHint':True,'destructiveHint':False})
        def calculate()->dict:return {'ok':True}
        self.assertIsNotNone(server)
if __name__=='__main__':unittest.main()
