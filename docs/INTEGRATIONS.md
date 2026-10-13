# Tool and dependency coverage — v0.2.0

This document separates **source implemented**, **local execution**, **native SDK execution**, **live service validation** and **data entitlement**. They are not interchangeable. No provider was live-validated during packaging; no keys or paid data licenses are included. Contract tests inject representative responses and inspect requests. They do not prove that a live endpoint currently accepts those requests.

## Provider adapters

| Provider | Implemented read capability | Configuration / boundary | Delivery validation |
|---|---|---|---|
| SEC EDGAR | Submissions/filing metadata and company facts by CIK | `SEC_USER_AGENT` identifying a real contact; public-access policies still apply | Request and fixture tests |
| FRED | Series observations, date/vintage query fields | `FRED_API_KEY`; a retrieval date is not an observation date | Request and fixture tests |
| RBA | Statistical CSV tables, including preamble parsing | Public table ID; metadata and units retained | CSV/request fixtures |
| ABS | SDMX data and dataflow metadata | New `data.api.abs.gov.au/rest` base; flow/dimension keys must be verified | Request/CSV fixtures |
| OECD | SDMX data and dataflows | Dataset/dimension keys required; no universal economic-series mapping | Request/XML fixtures |
| IMF | Configurable-by-source SDMX request implementation for data/dataflows | The coded 2.1 route, portal access and series dimensions require live confirmation; optional `IMF_API_KEY` | Constructed request fixture only; particularly provisional |
| CoinGecko | Quote and market-chart history by coin ID | `COINGECKO_API_KEY`; demo/pro endpoints differ; IDs rather than ambiguous tickers | Request/JSON fixtures |
| Yahoo/yfinance | Historical prices, date columns and multi-index symbol fields | `yfinance`; client-side use rights not assumed to cover hosted redistribution | SDK-shaped mock only; native library absent |
| OpenBB | Isolated history/quote/search/FRED macro bridge | `OPENBB_PYTHON`; providers installed/configured within OpenBB; their keys and entitlements still required | Process contract mock only; native SDK absent |
| Alpha Vantage | Adjusted daily history | `ALPHA_VANTAGE_API_KEY`; endpoint may require paid entitlement | Request/JSON fixtures |
| Finnhub | Quote | `FINNHUB_API_KEY` | Request/JSON fixtures |
| MarketData.app | Quote | `MARKETDATA_API_KEY` | Request/JSON fixtures |
| MetalpriceAPI | Base-currency metal rates | `METALPRICE_API_KEY`; rate orientation is not silently inverted into a metal price | Request/JSON fixtures |

Raw payloads retain provider structure. SDMX structure responses are retained as XML, not a complete catalog browser. API envelopes are not automatically joined to asset IDs, converted to total returns, accepted as valuations or fed into optimizers. Those mapping/approval steps remain explicit in the agent workflow.

### Retrieval controls

Built-in HTTP adapters use an HTTPS host allowlist, no redirects, request timeout, response-size limits, bounded retries and per-transport pacing. Live calls require explicit `--allow-network`. SDK adapters use the provider's networking implementation and are not claimed to inherit every transport control. Returned envelopes include the source, query metadata, retrieval time, response hash and rights uncertainty. Known API-key fields are removed from stored request metadata; raw provider payloads still require human review before sharing. There is no persistent cross-process rate-limit scheduler or full circuit-breaker/fallback router in this release.

## Quantitative dependencies

| Tool | Why present | Status |
|---|---|---|
| NumPy / SciPy | Deterministic arrays, constrained optimization, CVaR linear program | Installed and executed locally |
| pandas / scikit-learn | Time-series frames; Ledoit–Wolf covariance shrinkage | Installed and executed locally |
| skfolio | Native MeanRisk and RiskBudgeting bridge | Source and install extra; native package absent here |
| PyPortfolioOpt | Efficient frontier methods, CVaR, HRP, explicit-view Black–Litterman | Source and install extra; native package absent here |
| Plotly | Interactive report charts with embedded Plotly.js | Installed, built and browser-tested |
| Tailwind CSS | Compiled utility CSS and responsive dashboard layout | Real 4.1.10 compiler used; checked-in output included |

The default demonstrated methods use SciPy, **not skfolio/PyPortfolioOpt disguised behind their names**. Native engines fail clearly when missing. HRP has no cap support in the supplied wrapper. The SciPy CVaR wrapper caps dense optimization at 2,500 periods. Risk parity is a constrained numerical objective, not a promise of exactly equal contributions when caps bind. The efficient frontier and metrics are sample-dependent research.

## Documents, agents and local data

| Tool | Implemented | Important limit |
|---|---|---|
| Household JSON and cashflow CSV | Validated structured input with evidence references | User approval required |
| Normalized fund holdings CSV | Weights, dates and sources; unknown fraction preserved | Not a universal ETF-website scraper |
| pypdf | Page-level text extraction, source hash and empty-page flags | Basic native test; no OCR; no reliable arbitrary-statement fact extraction claimed |
| ofxparse | Account transaction import with ID deduplication | Native library not installed during packaging; transactions need review and mapping |
| MCP Python SDK | Seven read-only stdio tools confined to private JSON workspace | Source/path tests; host handshake not run |
| Agent Skills | Sixteen canonical workflows with thin Codex/Claude pointers | Actual host/version discovery and end-to-end interview not run |
| Ownership graph | Explicit DAG and leaf aggregation; rejects double counting/cycles | Supplied ownership values only; not inferred trust/legal ownership |
| Exposure engine | Separate currency/geography/sector dimensions and unknown proportions | No invented property-cycle beta or cross-asset correlation |

The normalized fund holdings CSV (`ofo import-holdings`) is documented
field-by-field in
[`docs/holdings-csv.md`](holdings-csv.md): required columns, how `weight` is
interpreted, how the unclassified residual is preserved per asset, duplicate
rejection, and `as_of`/`source` expectations. The documented example is
[`examples/holdings.synthetic.csv`](../examples/holdings.synthetic.csv), which
the holdings tests run end to end.

## Earlier references that are not installation dependencies

**ai-job-search** inspired profile-first workflows and thin pointers; it is not embedded as the finance runtime. **Addepar** informed ownership/position concepts; its proprietary product/API is not a dependency. **Wealthfolio/Ghostfolio** are product/architecture references, not bundled applications or copied AGPL source. No restricted Wealthfolio dataset is shipped. Adding these entire applications would not make this project more complete; it would add overlapping state and unrelated licensing obligations.

OpenBB can expose additional providers, but FMP, Tiingo, Polygon and TradingEconomics are not each separately implemented or validated here. IBKR, CommSec, Schwab, Binance/Coinbase, bank OAuth and automatic super/pension synchronization are not connected. Local CSV/OFX/manual records cover the input boundary. SEC filing discovery does not include a complete N-PORT XML holdings parser. Private assets/property require explicit valuations; an index is not a property appraisal.

No adviser licensing, tax filing, insurance purchase, financial-product suitability determination, brokerage execution or automatic capital allocation is included. A disclaimer does not by itself determine a future hosted product's legal classification. Product scope and jurisdiction need to be assessed before a real launch.

## Official technical references consulted

- SEC API: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- ABS API: https://www.abs.gov.au/statistics/application-programming-interfaces-apis/data-api-user-guide
- RBA tables: https://www.rba.gov.au/statistics/tables/
- FRED observations: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- IMF API portal: https://data.imf.org/en/Resource-Pages/IMF-API
- CoinGecko: https://docs.coingecko.com/reference/simple-price
- OpenBB: https://docs.openbb.co/python/installation/
- skfolio: https://skfolio.org/generated/skfolio.optimization.MeanRisk.html
- PyPortfolioOpt: https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html
- Plotly: https://plotly.com/javascript/financial-charts/
- Tailwind: https://tailwindcss.com/docs/installation/tailwind-cli
- MCP: https://modelcontextprotocol.io/docs/develop/build-server

Consulted 2026-09-21. Service availability, API dimensions, package compatibility and use rights must be rechecked at integration time.
