# Release History - open AEA

## Unreleased

Plugins:

- `open-aea-ledger-ethereum`: tightens `max_gas_fast` per chain in `CHAIN_EIP1559_OVERRIDES`. Until now low-fee chains (Gnosis, Optimism, Base, Mode, Fraxtal, Arbitrum One) inherited the chain-agnostic 1500 gwei default, so a fee-oracle anomaly could authorise a tx priced 100×+ above the chain's normal range before the cap engaged. A production market-creator deployment on Gnosis submitted a routine multisend at 694 gwei (~700× the validator floor of 1 gwei) on 2026-04-22 ([tx 0x727262d9…](https://gnosisscan.io/tx/0x727262d9238881e72eeaeb01bf88b234b380c6d3d2dc9e60fcb71b07354933bd)), paying 0.637 xDAI — ~45% of the agent's 30-day spend — while the inherited 1500 gwei ceiling did not trigger the fallback. New per-chain ceilings: Gnosis 30 gwei, Optimism / Base 100 gwei, Mode / Fraxtal 50 gwei, Arbitrum One 5 gwei. Sized to preserve operability during legitimate congestion (Base's March 2024 Dencun memecoin frenzy sustained ~24 gwei averages with bursts >100 gwei in individual blocks; Gnosis Tornado-deposit waves briefly hit 5–8 gwei) while bounding fee-oracle anomalies. Polygon (10000 gwei ceiling) and Celo (default 1500 gwei) are unchanged. #909

Packages:

- `valory/ledger` connection: aligns per-chain `max_gas_fast` in `connection.yaml` with the new plugin-level ceilings — Gnosis 30, Optimism / Base 100, Mode / Fraxtal 50, Arbitrum One 5. Self-documenting and defensible if the plugin defaults ever drift. #909

## 2.2.5 (2026-05-08)

Plugins:

- `open-aea-ledger-ethereum`: refactors `RPCRotationMiddleware` into a `RotatingHTTPProvider` (an `HTTPProvider` subclass) and constructs `Web3(RotatingHTTPProvider(...))` directly in `EthereumApi.__init__`. Rotation now lives at the transport layer, so the standard web3 middleware chain — defaults plus any user-injected middleware — runs untouched on every call. Fixes the v2.2.4 regression where `ledger_api.api.eth.<method>(...)` returned plain dicts instead of `AttributeDict`, breaking attribute access (e.g. `receipt.blockNumber`) for downstream consumers reaching into the underlying web3 handle directly (open-autonomy `TxSettler.settle()`, etc.). All inner middleware (`AttributeDictMiddleware`, `ENSNameToAddressMiddleware`, `FormattingMiddleware`, `BufferedGasEstimateMiddleware`, `GasPriceStrategyMiddleware`, and any user-injected `inject(layer=0)` middleware) — silently dead under the v2.2.4 bypass — now run normally. `ExtraDataToPOAMiddleware` reverts to its standard placement at `inject(layer=0)`. #889
- `open-aea-ledger-ethereum`: `RotatingHTTPProvider.endpoint_uri` is overridden as a property that reflects the *currently active* RPC URL, so diagnostic tooling (metrics, logs, request IDs) reading `w3.provider.endpoint_uri` post-rotation observes the correct endpoint instead of the URL passed to `super().__init__`. #889
- `open-aea-ledger-ethereum`: `RotatingHTTPProvider` raises `ValueError` at construction if `rpc_urls` (after Chainlist enrichment) is empty, replacing the silent failure that previously surfaced as an opaque `requests` error on the first RPC call. #889
- `open-aea-ledger-ethereum`: `_mark_rpc_backoff` and `_is_rpc_healthy` now run under the rotation lock (switched to `threading.RLock` so they remain callable from inside `_rotate`), closing a torn-read window on `_backoff_until` under concurrent error/rotation events. Unknown-category errors emit a `WARNING` log before re-raising so novel transport failures are no longer silent. `classify_error` now returns a `Literal[...]` so the categorical switches in `make_request` / `_handle_error_and_rotate` are mypy-checkable. #889

Tooling:

- `strategy.ini`: loosens the `urllib3` license-whitelist pin from `==2.6.3` to `>=2.6.3,<3` to track minor upgrades that `requests` resolves transitively. Resolves the `liccheck` CI failure where `requests` pulled `urllib3 2.7.0` while the strategy still authorized only `2.6.3`. #889

## 2.2.4 (2026-05-07)

Plugins:

- `open-aea-ledger-ethereum`: makes `RPCRotationMiddleware`'s connection-reset detection locale-safe. `classify_error` now matches on `isinstance(ConnectionResetError)`, `isinstance(ssl.SSLError)` (excluding `ssl.SSLCertVerificationError`), and `errno == 10054` (WSAECONNRESET) — and walks the `__cause__`/`__context__` chain — instead of substring-matching the localized OS message. On non-English Windows installs, transient resets that previously slipped through as `"unknown"` and skipped the retry path are now retried correctly. Resolves the `terminate_and_withdraw` HTTP 500 reported on Polystrat / Pearl. #887
- `open-aea-ledger-ethereum`: on connection-reset errors, `RPCRotationMiddleware` now evicts the cached `requests.Session` for the affected provider (`_evict_provider_session`) before retrying, so the next attempt performs a fresh TCP/TLS handshake instead of reusing the half-closed pooled socket. The cache read and `clear()` execute under the session manager's `_lock` when one is exposed; the `_current_index` snapshot in `_handle_error_and_rotate` is taken under the middleware's own lock. Eviction failures are logged at `WARNING` with `exc_info=True` so recovery-path regressions remain diagnosable. #887
- `open-aea-ledger-ethereum`: removes the `len(rpc_urls) > 1` gate from `RPCRotationMiddleware.wrap_make_request` — single-URL deployments (Pearl's default) now enter the retry / session-eviction loop. The retry budget remains `min(MAX_RETRIES, len(rpc_urls) * 2)`; when the configured `MAX_RETRIES` is clamped by the pool size, an INFO log line is emitted once at `build()` time. On genuine pool exhaustion a single WARNING summary is emitted before the final `raise`, distinguishing systemic outages from one-off transient failures. #887
- `open-aea-ledger-ethereum`: changes the registration of `ExtraDataToPOAMiddleware` from `inject(layer=0)` (innermost) to `add(...)` (outermost). Required because `RPCRotationMiddleware.wrap_make_request` calls each provider directly and bypasses the inner middleware chain (formatters, ENS, retry, exception, `AttributeDictMiddleware`); PoA processing must therefore wrap the rotation layer to apply on every response. Fixes BSC `extraData` field truncation that surfaced during CI. #887
- `open-aea-ledger-ethereum`: widens `AttributeDictTranslator.to_dict` to accept plain `dict` (`Union[AttributeDict, TxReceipt, TxData, Dict[str, Any]]`). Required because responses returning through the rotation path arrive as plain dicts rather than `AttributeDict` instances (the inner middleware chain is bypassed). `TxReceipt` and `TxData` are TypedDicts and continue to flow through the same arm. The existing `AttributeDict` callers are unaffected. #887

Tests:

- Reworks `ACNWithBootstrappedEntryNodesDockerImage` (the libp2p ACN docker fixture) to support a multi-container topology (bootstrap node plus two entry nodes), replacing the single-container `wait()` with a per-container port poll. Resolves flaky ACN integration tests; unrelated to the WSAECONNRESET fix but absorbed into the same release for CI continuity. #887

## 2.2.3 (2026-05-04)

AEA:

- Bumps the `GitPython` floor to `>=3.1.47,<4.0.0` to pull in the upstream fixes for `GHSA-rpm5-65cw-6hj4` (insecure non-multi options in clone / clone_from) and `GHSA-x2qx-6953-8485` (blind local-file-read via `git ls-remote`). #884

Tooling:

- Collapses the four out-of-band lint/test config files (`pytest.ini`, `setup.cfg`, `.pylintrc`, `.gitleaks.toml`) into `pyproject.toml` + `tox.ini` (Wave 2a). Pytest config moves to `[tool.pytest.ini_options]`; the only remaining `setup.cfg` content is a minimal `[isort]` block consumed by `aea generate-all-protocols` to format generated protocol code. `[mypy]` and per-module `[mypy-*]` overrides plus the `[darglint]` block live at the bottom of `tox.ini` (mypy/darglint don't read pyproject.toml); the `[testenv:mypy]` command passes `--config-file=tox.ini` so they're picked up. #885
- Bumps `tomte` to `==0.7.0` (released). Every lint testenv now references `{envsitepackagesdir}/tomte/configs/<config>` for its config — pylint, mypy, isort, flake8, bandit, darglint, safety, gitleaks — instead of carrying a forked copy in this repo. The pylint testenv keeps OAEA-specific extras (`--ignored-modules=…`, `--ignore-patterns=…`) inline because they're project-specific. #885
- Slims `pyproject.toml` to strict PEP 621 + `[tool.poetry]` + `[tool.pytest.ini_options]` + `[tool.isort]` (no `[tool.pylint.*]` / `[tool.flake8]` / `[tool.mypy]` blocks). #885
- Updates the `gitleaks` GitHub Actions job to install tomte and run with `--config={envsitepackagesdir}/tomte/configs/gitleaks.toml`. The previous job ran against gitleaks default rules. `.gitleaksignore` regenerated via `tomte freeze-gitleaks` (66 historical fingerprints). #885

## 2.2.2 (2026-04-24)

Plugins:

- `open-aea-ledger-ethereum`: generalises `EthereumApi.get_l1_data_fee` to dispatch by `chain_id`. Covers OP-stack (Optimism, Base, Mode, Fraxtal) via the `GasPriceOracle` and Arbitrum Nitro (Arbitrum One, Arbitrum Nova) via the `NodeInterface` precompile; returns 0 on any other chain. Non-OP-stack L2 queries previously failed silently. Callers that need the L1 data fee (e.g. drain-address budgeting) invoke the helper explicitly — it is safe to call on any chain. #780
- `open-aea-ledger-ethereum`: adds chain-aware fallback defaults inside the plugin itself via a unified `CHAIN_EIP1559_OVERRIDES` map applied by `get_default_gas_strategy(chain_id)`. Per-chain tunings: Optimism / Base / Mode / Fraxtal (5 gwei maxFeePerGas, 3 gwei tip — OP-stack), Arbitrum One (2 gwei maxFeePerGas, 1 gwei tip — above the 0.1 gwei floor), Polygon (6000 gwei maxFeePerGas, 30 gwei tip, `min_allowed_tip` 30 gwei — clears the validator-enforced priority fee floor; `max_gas_fast` 10000), Celo (50 gwei maxFeePerGas, 25 gwei tip, `min_allowed_tip` 25 gwei — above the 25 gwei network floor), and Gnosis (5 gwei maxFeePerGas, 1 gwei tip, `min_allowed_tip` 1 gwei). All other chains inherit `DEFAULT_FALLBACK_ESTIMATE`. Applies whether the ledger is built via `make_ledger_api('ethereum', chain_id=...)` directly OR through the `valory/ledger` connection, and covers both `eip1559` and `eip1559_polygon` strategies. User-supplied `gas_price_strategies` kwargs still take precedence. #775
- `open-aea-ledger-ethereum`: improves the fallback-gas warning emitted by `get_gas_price_strategy_eip1559` to name the actual `maxFeePerGas` / `maxPriorityFeePerGas` values being used and point at the `gas_price_strategies` kwarg as the supported override. #775
- `open-aea-ledger-ethereum`: updates `POLYGON_GAS_ENDPOINT` from the deprecated `gasstation-mainnet.matic.network/v2` to the canonical `gasstation.polygon.technology/v2` per Polygon docs. Affects callers of the `eip1559_polygon` strategy. #775
- `open-aea-ledger-solana`: bumps `solana>=0.33.0,<0.34.0`, `solders>=0.21.0,<0.22.0`, `anchorpy>=0.20.0,<0.21.0`. Removes the transitive `cachetools<5` pin that `solana-py` 0.29–0.32 carried, unblocking consumers that need `cachetools>=7` (e.g. `tomte[tox]==0.6.5 → tox 4.46`). `solana.blockhash.BlockhashCache` was removed upstream in 0.33.0; inlined locally as a minimal TTL cache to preserve the plugin's public import surface. See `open-autonomy#2479`. #880
- `open-aea-ledger-ethereum-hwi`: drops the orphaned `construct<=2.10.61` cap from the plugin's `install_requires` and the repo-level `pyproject.toml` / `tox.ini`, unblocking dependency resolution for consumers that pull in the solana plugin alongside hwi. #882

Packages:

- `valory/ledger` connection: aligns per-chain `fallback_estimate` and `min_allowed_tip` in `connection.yaml` with the new plugin-level defaults — Optimism / Base / Mode / Fraxtal 5 gwei, Arbitrum 2 gwei, Polygon 6000 gwei + 30 gwei tip + `max_gas_fast` 10000, Celo 50 gwei + 25 gwei tip, Gnosis 5 gwei + 1 gwei tip. Also adds a Polygon-specific `eip1559_polygon` block (the chain's default strategy) so tuned values apply on the default path, not only when callers explicitly select `eip1559`. Technically redundant now that the plugin ships matching defaults, but keeps the YAML self-documenting and defensible if the plugin defaults ever drift. #775

## 2.2.1 (2026-04-15)

AEA:
- Populates the PyPI `Description` section for the root package and every plugin from the corresponding `README.md` (was empty / a one-liner before). #876

Plugins:
- Removes the unmaintained `open-aea-ledger-ethereum-flashbots` plugin and every CI / docs / config reference to it. Consumers should drop `ethereum_flashbots` from the `valory/ledger` connection config and remove `aea_ledger_ethereum_flashbots` PyInstaller flags. See `docs/upgrading.md`.
- Makes `aea-ci generate-api-docs` configurable (`--source-dir`, `--packages-dir`, `--plugins-dir`, `--docs-dir`, `--default-package`, `--ignore-plugin`, `--ignore-prefix`, `--parallel`) so downstream repos can reuse it. Parallel mode now surfaces worker exceptions instead of silently dropping them. #876
- Adds `aea-ci check-third-party-hashes` — verifies local `packages/packages.json` `third_party` entries against one or more upstream repos, with per-upstream fault tolerance. #876

Tests:
- Re-enables the "Local" `test_libp2p` DHT integration tests against the rebuilt `valory/open-acn:latest` image (libp2p v0.33.2). Switches fixture entry-peer multiaddrs from `0.0.0.0` to `127.0.0.1` to satisfy libp2p v0.33's stricter dial checks. #876

CI:
- Adds `bugs.python.org/issue8296` to the doc-link skip list to eliminate a flaky external URL. #876

## 2.2.0 (2026-04-13)

AEA:
- Removes `requests`, `ipfshttpclient`, `jsonschema`, `python-dotenv`, `semver`, `morphys`, `ecdsa`, `base58`/`multibase`/`multicodec`/`pymultihash` from core dependencies -- replaced with stdlib or inlined implementations. #858 #859 #860 #861 #862 #863 #866 #867
- Adds env var resolution on component override sections in AEABuilder. #868
- Switches to strict PEP 440 version parsing (replaces `semver`). #859
- Enhances env file parser to support `export` prefix, `${VAR}` interpolation, and inline comments. #860
- Inlines IPFS HTTP client (replaces `ipfshttpclient`). #866
- Inlines JSON Schema Draft-04 validator (replaces `jsonschema`). #862
- Inlines secp256k1 validation (replaces `ecdsa` from base deps). #863
- Inlines multiformat helpers (replaces `base58`/`multibase`/`multicodec`/`pymultihash`). #861

Plugins:
- Adds new plugin: `open-aea-ci-helpers` (`aea-ci`) with 8 CI automation commands migrated from scripts/. #871
- Adds new plugin: `open-aea-dev-helpers` (`aea-dev`) with 7 release/dev tool commands migrated from scripts/. #865
- Migrates `check_copyright`, `check_doc_links`, `freeze_dependencies` to tomte CLI. #865
- Widens dependency pins across all plugins for broader compatibility. #864

Go / libp2p:
- Bumps Go module dependencies to Go 1.24. #872
- Restores circuit-relay v2 routing parity. #872
- Fixes golangci-lint integration for libp2p_node. #872
- Adds Python<->Go FIPA e2e test harness to CI. #872

Tooling:
- Migrates from Pipenv to Poetry. #857
- Bumps `tomte` from `0.6.1` to `0.6.5`. #857
- Deletes 12 Python scripts from scripts/ (migrated to plugins). #865 #871
- Removes benchmark/checks/ legacy scripts. #865
- Comprehensive docs refresh. #872

CI:
- Bumps GitHub Actions (checkout v4, setup-python v5, golangci-lint v6). #872
- Bumps Go from 1.17-1.20 to 1.24. #872
- Adds golangci-lint for libp2p_node and aealite. #872
- Reduces platform matrix for faster CI runs. #869
- Fixes Click `flag_value` default handling follow-up. #855


## 2.1.0 (2026-03-06)

AEA:
- Extends Python support from `3.10-3.11` to `3.10-3.14`. #831
- Adds support for pytest v8 and updates related test and utility modules. #835
- Makes CLI `flag_value` defaults robust across Click processing-order changes (including `packages sync` defaults and registry flag defaults). #839 #848
- Adds `AEA_PASSWORD` environment variable support for CLI password handling. #825
- Fixes multiple high-impact audit findings across behaviours, multiplexer, manager, dependency installation, and registry handling. #846

Plugins:
- Adds multiple RPC rotation with automatic failover in the Ethereum ledger plugin stack. #829
- Fixes `open-aea-ledger-ethereum-flashbots` dependency constraints to be compatible with `open-aea-ledger-ethereum` in the `2.1.0rc6` line. #850

Tooling and dependencies:
- Bumps `tomte` from `0.4.0` to `0.6.1`. #831
- Updates Click range to `<8.4.0` and applies compatibility fixes for 8.3.x behaviour rules. #838 #839 #848
- Updates several pinned dependencies for Python 3.12-3.14 compatibility, including `packaging==26`, `pytest>=8.2,<10`, `protobuf>=5,<6`, `requests>=2.32.5,<3`, `openapi-core==0.22.0`, `openapi-spec-validator>=0.7.0,<0.8.0`, `docker==7.1.0`, `hypothesis==6.151.9`, and `cosmpy>=0.11.0,<0.12`. #831
- Removes obsolete/deprecated compatibility dependencies and paths (including `gym` and `distutils` usage). #831 #836

Compatibility and regression fixes:
- Fixes Python 3.13/3.14 regressions in async/multiprocessing paths (including `multiprocessing.Manager` context handling and asyncio event-loop compatibility changes). #843
- Reworks ready-awaitable internals to avoid Python 3.14 warnings/regressions and follow-up flaky behaviour. #831 #847
- Fixes local connection cross-thread queue loop handling to avoid race conditions caused by private asyncio queue internals. #847
- Adds follow-up fixes for CLI and framework regressions found after the initial interpreter/dependency bump, including critical audit issues and command behaviour corrections. #846 #847 #848


## 2.0.8 (2026-01-20)

Packages:
- Warns when the chain id is not specified in a message #824
- Caches the chain id to avoid excessive RPC usage #826

## 2.0.7 (2025-10-17)

Docs:
- Updates the docs to use the new naming convention for Agent blueprints and AI agents #821

## 2.0.6 (2025-09-30)

AEA:
- Pins `click` to `>=8.1.0,<8.3.0` # 819
Packages:
- Makes timeout in `http_server` configurable by any skill that's using this connection #818

## 2.0.5 (2025-08-15)

Plugins:
- Bumps `open-aea-flashbots==2.0.0` in `open-aea-ledger-ethereum-flashbots` #814
- Fixes `valory/open-aea-user` docker image building and warnings #817

## 2.0.4 (2025-08-11)

Packages:
- Updates the `acn.staging.autonolas.tech` DNS entries to `acn.autonolas.tech`

## 2.0.3 (2025-08-07)

Plugins:
- Fixes no attribute error in `aea-ledger-ethereum` plugin when calling `update_with_gas_estimate` along with `from` address in the transaction. #812

## 2.0.2 (2025-08-05)

AEA, Plugins, Packages:
- Bumps the version of `web3py` to `>=7.0.0,<8.0.0`  # 810
- Bumps the version of `eth-account` to `>=0.13.0,<0.14.0`  # 810
- Bumps the version of `hexbytes` to `==1.3.1`  # 810

## 2.0.1 (2025-07-25)

AEA:
- Loosens the pytest version range to `>=7.0.0,<8.0.0` # 808

Plugins:
- Removes pytest from the base dependencies of `aea-cli-ipfs` plugin and keeps it only for tests # 808

## 2.0.0 (2025-07-16)

AEA, Plugins, Packages:
- Ends support for Python 3.8 and 3.9. #801
- Docker images now use Python 3.10 as the base Python version #801
- `get_metavar` now requires a new parameter, `ctx: Context` #801
- `aea` and its subcommands that expect some arguments (for example `aea`, `aea ipfs`, etc.), when used without any arguments will now finish with exit code 2 instead of 0, and print their usage help in `stderr`. #801

## 1.65.0 (2025-03-13)

Packages:
- Refines the default EIP-1559 values in the ledger connection's configuration #788 && #791

Plugins:
- Uses the minimum tip as a fallback #789
- Makes the timeout of RPC requests configurable #792

Docs:
- Fixes broken submodule and Macro syntax error #787

Tests:
- Creates a test for the EIP-1559 fee calculation #791
- Makes the public RPCs overridable via environment variables #793

## 1.64.0 (2025-02-12)

Plugins:
- `open-aea-ethereum` now multiplies the base gas fee as before.  #786

## 1.63.0 (2025-02-03)

Plugins:
- Defaults the minimum allowed tip as 1000000000 for Gnosis chain, and 1 for the rest.  #784
- Adds a new function `get_l1_data_fee` to the `EthereumApi` class, to get the L1 data fee for a transaction.  #784

## 1.62.0 (2025-01-29)

Packages:
- Updates tasks.py log level to debug #774

Plugins:
- Accounts for the minimum allowed tip on chains #782

## 1.61.0 (2025-01-24)

AEA:
- Fixes encoding #779

Plugins:
- Removes incorrect key from the fallback estimate #779
- Fixes the transaction receipt's retrieval on the ledger dispatcher #773

Chores:
- Upgrades macOS in workflow #772

Docs:
- Adds explicit reference to the version of `mkdocs-mermaid-plugin` #776
- Fixes reference to the multiplexer image #778

## 1.60.0 (2024-11-15)

Plugins:
- Fixes the handling of dropped ACN node connection #769
- Fixes an edge case in the gas estimation #770

## 1.59.0 (2024-10-29)

Plugins:
- Fixes the gas estimation #766

AEA
- Avoids validation failures with --help #764

## 1.58.0 (2024-10-03)

AEA:
- Adds support for dictionary overrides #750, #761

## 1.57.0 (2024-09-24)

AEA:
- Adds support for custom components in `publish` and `eject` commands. #758

Plugins:
- Improves the EIP1559 strategy #759

## 1.56.0 (2024-09-17)

Plugins:
- Fixes the pricing logic. #756

## 1.55.0 (2024-08-05)

Plugins:
- Adds support for polygon, fraxtal, base and mode. #746 && #747

## 1.54.0 (2024-07-27)

Plugins:
- Adds optimism config to the ledger connection. #744

Chore:
- Updates the release process document. #743
 
## 1.53.0 (2024-05-27)

AEA:
- Pins `python-dotenv` to `>=0.14.0,<1.0.1`

## 1.52.0 (2024-04-26)

AEA:
- Loosens up the version range for several dependencies to allow better integration with other frameworks

Plugins:
- Implements a custom filtering method to handle RPC timeouts and hanging.

Packages:
- Adds `Celo` to ledger connection configurations

Chore:
- Adds whitelist for component mint check


## 1.51.0 (2024-04-10)

AEA:
- Adds support for pushing custom components to the IPFS registry

Packages:
- Make timeout configurable on the http client connection
- Adds `Celo` to ledger connection configurations

## 1.50.0 (2024-03-13)

AEA:

- Fixes IPFS node address parsing on Git console 
- Adds support for caching and reusing packages 

## 1.49.0 (2024-03-06)

AEA:
- Pins `python-dotenv>=0.14.0,<0.22.0`

## 1.48.0.post1 (2024-02-27)

AEA:
- Fixes custom file references in the CLI commands

## 1.48.0 (2024-02-21)

AEA:
- Adds support for scaffolding and managing [custom packages](https://github.com/valory-xyz/open-aea/pull/717#pullrequestreview-1887581886)

## 1.47.0 (2024-02-13)

Plugins:
- Bumps `cosmpy@0.9.2`
- Fixes the `_try_send_signed_transaction` on the solana plugin to separate the transaction receipt retrieval

## 1.46.0 (2024-01-23)

AEA:
- Updates the `generate-key` command to include ledger specifier when writing keys in a JSON file

## 1.45.0 (2024-01-11)

Plugins:
- Fixes transaction deserialisation for adding nonce on the solana ledger
- Increases the number of retries for fetching transaction receipt

## 1.44.0 (2024-01-04)

Packages:
- Regenerates the protocols to update the copyright header
- Updates the date range for issuing the certificates
- Adds optional key word arguments to `SEND_TRANSACTION` messages

## 1.43.0.post2 (2023-12-26)

AEA:
- Fixes the default environment variable parsing for the base types

## 1.43.0.post1 (2023-12-19)

AEA:
- Fixes the default environment variable parsing for the list types

## 1.43.0 (2023-12-14)

AEA:
- Adds `--timeout` flag on aea install command
- Fixes circular import issues on package manager
- Fixes nested list environment variable parsing

Plugins:
- Adds support for versioned transactions on `solana` plugin

## 1.42.0 (2023-11-20)

AEA:
- Pins `openapi-core==0.15.0`, `openapi-spec-validator<0.5.0,>=0.4.0` and `jsonschema<4.4.0,>=4.3.0`

Chore:
- Adds a script for managing dependencies across various project configurations

## 1.41.0.post1 (2023-10-23)

Packages:
- Use `kwargs.pop` instead of `kwargs.get` to avoid extra argument error on ledger connection

## 1.41.0 (2023-10-10)

AEA:
- Fixes the source repository validation regex
- Updates the `generate-key` command to prompt before overwriting the existing keys file
- Fixes the inconsistent hashing caused by the `CRLF` line endings
- Updates the component loader to ignore the test modules when loading the component
- Adds support for overriding dependencies
- Updates the `sync` command to download missing dependencies and update `packages.json`
- Updates the error messages for missing ledger plugins on `generate-key` command
  
Plugins:
- Adds missing `py.typed` markers
- Backports the changes from the `agent-academy-2` repository on the ledger connection
- Ports `http_server` as a valory connection

## 1.40.0 (2023-09-26)

AEA:
- Adds support for specifying extra dependencies and overriding dependencies via `-e` flag on `aea install`
- Updates the selection of dependencies in `aea install` command to override the dependencies in the `extra dependencies provided by flag > agent > skill > connection > contract > protocol` order instead of merging them.

## 1.40.0 (2023-09-26)

AEA:
- Removes the `web3py` fork as a dependency
- Bumps the protobuf to `protobuf>=4.21.6,<5.0.0`
- Updates protocol buffers compiler to `v24.3`
- Updates the protocol generator
- Removes unused layers from the user image and uses minimal python image as base

## 1.39.0.post1 (2023-09-21)

AEA:
- Pins `jsonschema<=4.19.0,>=4.16.0`

## 1.39.0 (2023-09-07)

AEA:
- Removes the rust installation layer from the user image

## 1.38.0 (2023-08-09)

Framework:
- Deprecates the support for `Python 3.7` and adds support for `Python 3.11`
- Adds support for multi platform docker images

Plugins:
- Replaces `web3py==5.31.4` with `open-aea-web3==6.0.1`
- Replaces `flashbots==1.1.1` with `open-aea-flashbots==1.3.0`
- Bumps `open-aea-cosmpy` to `v0.6.5`
- Deprecates the `apduboy` as a dependency
- Pins `ledgerwallet==0.1.3`

## 1.37.0 (2023-07-25)

Plugins:
- Replaces `cosmpy` with `open-aea-cosmpy`

## 1.36.0 (2023-07-19)

AEA:
- pyyaml updated, tomte updated  

Plugins:
- cosmpy updated to 0.6.0

## 1.35.0 (2023-06-20)

Plugins:
- Adds support for multiple transaction builders on `flashbots` ledger plugin
- Pins
  - `eth-account`to `>=0.5.9,<0.6.0`
  - `protobuf` to `==3.19.5`
  - `web3` to `==5.31.4`
  - `construct` to `<=2.10.61`

## 1.34.0 (2023-05-15)

AEA:
- Fixes a bug on `aea fetch` command which caused issue when using the `--alias` flag if the package with original name already existed in the working directory #630
- Removes the need for intermediate agent for generating protocols #632
  - Adds `-tlr` flag on the aea generate command group
  - Adds support for registering packages to local registry on the package manager
  - Updates the `ProtocolGenerator` implementation to work with the local registry project structure
- Fixes `IPFS` local registry loader #634
- Updates the `scaffold` tool to register the newly scaffolded packages to `packages.json` to the local registry #635
- Sets the apply environment variables to true on `aea build` command #636

Plugins:
- Bumps `solana` and `anchorpy` to resolve dependency issues with the `web3py` library #637

## 1.33.0 (2023-05-02)

AEA:
- Updates package manager to add newly found packages to the `packages.json` instead of raising error #622
- Updates the package manager to add new packages to third party #627

Packages:
- Fixes ACN slow queue issue #624

Plugin:
- Attaches the plugin loggers to the correct namespace #620
- Adds logic on the `flashbots` plugin to check that we are simulating against the current block, and we are targeting a future block when sending a bundle #625
- Adds support for specifying base URI for the IPFS client on the IPFS cli plugin #628

Chores:
- Update release flow parameters to use kebab case to avoid deprecation warnings #623

## 1.32.0 (2023-04-10)

AEA:
- Updates the protocol generator to use `protobuf` double type to represent float values

Packages:
- Adds `SEND_SIGNED_TRANSACTIONS` to the initial states on the ledger connection
  
Plugins:
- Removes unused dependencies from `solana` plugin
- Adds the new plugin the the `new_env` target on the `Makefile`
- Adds support for raising on a simulation failure on the `flashbots` plugin
- Makes `recursive` and `wrap_with_directory` parameters configurable on the IPFS client
- Attaches the plugin loggers to the correct namespace

Chores:
- Bumps `tomte` to `v0.2.4`
- Fixes `pyproject.toml` syntax
- Fixes parsing issues on `check_pipfile_and_toxini.py` script



## 1.31.0 (2023-03-21)

AEA:
- Updates the error messages on the package manager for misconfigured `packages.json` files
- Adds support for initialising empty local packages repository using `aea packkages init` command
- Fixes licence headers on the newly introduced plugins
- Adds two new performatives to the ledger api protocol 
  - `SEND_SIGNED_TRANSACTIONS` to send multiple transactions at once
  - `TRANSACTION_DIGESTS` to retrieve transaction digests for the transactions sent using `SEND_SIGNED_TRANSACTIONS`

Plugin:
- Introduces `Solana` ledger plugin
- Introduces `Ethereum Flashbots` plugin

## 1.30.0 (2023-03-08)

AEA:
- Adds support for syncing third party package hashes from `github` repositories
- Adds support for custom union types on the protocol generator
- Fixes message formatting on the configuration validator

Packages:
- Adds `pytest-asyncio` as a dependency on the ledger connection

Plugin:
- Introduces the `open-aea-ledger-ethereum-hwi` plugin to support hardware wallet interactions

## 1.29.0 (2023-02-02)

AEA:
- Adds support for retries on the `aea push-all` command using `--retries` flag
- Updates the `aea test` command to load dependencies for an agent when running test for an agent package
- Updated the protocol generator to generate tests
- Fixes for process termination in the test tools on windows

Packages:
- Replaces the usage of `time.sleep` with `asyncio.sleep` in asynchronous functions

Test:
- Adds more tests for `aea test` command group

## 1.28.0.post1 (2023-01-16)

AEA:
- Fixes the module import issue on the `aea test` command by removing the usage of spawned process to run the pytest command

Plugins:
- Pins proper version for cosmos plugin on the ledger plugin
- Updates the `LedgerApi.update_with_gas_estimation` method to raise instead of logging the error if specified by the user

Chores:
- Pins `pywin32` to `>=304`

## 1.28.0 (2023-01-11)

AEA:
- Adds checks to make sure the author name and the package name are in snake case only
- Adds tools for automating the protocol tests
- Updates the test command to spawn a process for running the pytest command to make sure there are no issues with the test coverage
- Fixes a race condition found in the `AsyncMultiplexer`

Plugins:
- Makes the fetchai ledger plugin dependent on the cosmos plugin to prevent code duplication

Tests:
- Adds a test to showcase a race condition in `AsyncMultiplexer`

## 1.27.0 (2022-12-27)

AEA:
- Adds auto-generated protobuf `*_pb2.py` and `*_pb2_*.py` files to `coveragerc` ignore template for aea test command.
- Fixes comparison operators ` __eq__`, `__ne__`, `__lt__`, `__le__`, `__gt__`, `__ge__` for multiple classes including `PackageVersion`.
- Adds support to `test packages` command for the `--all` flag and switches default behaviour to only run tests on `dev` packages.
- Fixes miscellaneous issues on base test classes and adds consistency checks via meta classes.

Plugins:
- Updates `open-aea-cli-ipfs` to retry in case an IPFS download fails

Tests:
- Fills coverage gaps on core `aea`
- Fills coverage gaps on multiple packages
- Fills coverage gaps on all plugins

Chores:
- Merges the coverage checks with unit tests and removes the extra test coverage CI run.
- Cleans up release flow.
- Adds workflow for image building.

## 1.26.0 (2022-12-15)

AEA:
- Adds support for hashing byte strings on `IPFSHashOnly` tool
- Introduces `CliTest` tool to help with the `CLI` testing
- Extends aea packages lock command to update fingerprints
- Adds support for appending test coverage with previous runs on `aea test` command and fixes the coverage on `aea test packages` command
- Updates the `BasePackageManager.add_package` to fetch packages recursively

Plugins:
- Updates the `cosmos` and `fetchai` ledger plugins to use `PyCryptodome` for `ripemd160` hash generation
- Adds support for publishing byte strings directly to IPFS daemons without intermediate file storage on the `IPFS` plugin

Chores:
- Pins `tox` version using `tomte` in the CI to maintain version consistency
- Pins `go` version to `v1.17.7` on the CI

## 1.25.0 (2022-12-01)

AEA:
- Fixes the mechanism to convert the `json` path to environment variable string
- Updates the process of agent subprocess termination to make sure we properly terminate agents across the various operating systems
- Introduces `reraise_as_click_exception` to re-raise exceptions as `click.ClickExceptions` on command definitions
- Extends `CliRunner` to allow usage of `capfd` to capture test output
- Introduces `generate_env_vars_recursively` method to auto generate the environment variable names for component overrides
- Extends `aea generate-key` to support creating multiple keys
- Extends the package manager API to
  - Update the hashes for third party packages with a warning
  - Update the dependency hashes when locking packages
  - Verifying the dependency hashes when verifying packages
- Adds deprecation warning for `aea hash all` command since the same functionality is now being provided by `aea packages lock` command

Tests:
- Updates `libp2p` tests to use `capsys` to read `stdout` instead of patching `sys.stdout`
- Re enables tests skipped with `# need remote registry` comment
- Adds tests for package manager API

Chores:
- Updates the `tox` environment setting for unit tests to report duration of tests
- Deprecates the usage of `aea hash all` command from the workflow

## 1.24.0 (2022-11-15)

AEA:
- Adds deprecation warning for `--aev` flag
- Makes the usage of environment variables default
- Extends `push-all` command to push only the development packages
- Adds support for generating environment variable names if not provided by default
- Changes log level from `debug` to `error` on `Exception` handling
- Updates the configuration loader classes to make sure path string serialization is deterministic across the various platforms

Test:
- Fixes the tests skipped because of the wrongly configures ledger ID
- Adds tests to check if path string serialization is deterministic across the various platforms

Chores:
- Updates `scripts/check_ipfs_hashes_pushed.py` to use new `packages.json` format
  
## 1.23.0 (2022-11-09)

AEA:
- Extracts package manager implementation into core module
- Extends the package manager implementation to introduce separation between development and third party packages
- Extends aea packages lock command to work with new `packages.json` format
- Extends aea packages sync command with `--dev`, `--third-party`, `--all` flags to specify what packages to sync avoid updating hashes for third party packages
- Updates the `check-packages` command to make sure we skip `open-aea` when generating list for third party packages in package dependency check
- Adds proper exception handling on `aea fetch` command for bad packages

Chores:
- Updates dependencies in Dockerfile for documentation

## 1.22.0 (2022-11-01)

AEA:
- Updates the cert request serialisation process to maintain consistency across different operating systems
- Updates the `get_or_create_cli_config` method to return default config instead of creating one
- Introduces the `copy_class` utility function for testing different setup configurations
- Updates the overridable policies for the configuration classes

Packages:
- Removes the unwanted autonomy dependency from the ledger connection
  
Tests:
- Updates the cli config fixture to retain user config
- Fixes outbox check test 
- Adds test coverage for
  - `aea/cli`
  - `aea/configurations`
  - `aea/helpers`
  - `aea/test_tools`
  - `aea/manager`

Docs:
- Adds documentation on the usage of component overrides

Chores:
- Adds a script to automatically generate a package table for the docs
- Introduces the usage of `tomte` to maintain third party dependency version consistency
- Updates the script to check the broken links to use parallelization

## 1.21.0 (2022-09-28)

AEA:
- Updates `aea scaffold contract` to include contract ABIs

Packages:
- Adds support for running local ACN nodes
- Converts `ledger` and `http_client` connections and `http`, `ledger_api` and `contract_api` protocols to valory packages and syncs them with `open-autonomy` versions of the same packages
- Extends `ledger` connection to automatically handle contract calls to methods not implemented in the contract package, redirecting them to a default contract method.

Plugins:
- Introduces test tools module for IPFS cli plugin

Tests:
- Fixes flaky timeout tests
- Fixes flaky `DHT (ACN/Libp2p)` tests on windows
- Introduces test for assessing robustness of the ACN setup without agents

Docs:
- Adds a guide on implementing contract packages


## 1.20.0 (2022-09-20)

AEA:
- Ensures author and year in copyright headers are updated in scaffolded components
- Updates `check-packages`
  - to check the presence of the constant `PUBLIC_ID` for connections and skills.
  - to validate author
- Fixes CLI help message for `aea config set` command
- Extends test command to support consistency check skips and to run tests for a specific author
- Adds proper exception raising and error handling
  - Exception handling when downloading from IPFS nodes
  - Better error message when the `--aev` flag is not provided
- Fixes file sorting to maintain consistency of links on `PBNode` object on `IPFSHashOnly` tool

Plugins:
- Updates the IPFS plugin to make make sure we don't use the local IPFS node unless explicitly specified

Packages:
- Ports `libp2p` connection packages tests
  - Ports `p2p_libp2p_mailbox` tests
  - Ports `p2p_libp2p_client` tests
  - Ports `p2p_libp2p` tests
- Introduces `test_libp2p` connection package to test `libp2p` integration

Chores:
- Fixes docstring formatting to make sure doc generator works fine
- Updated `check_ipfs_hashes.py` script to use `packages.json` instead of `hashes.csv`
- Updates the command regex to align with the latest version

## 1.19.0 (2022-09-14)

AEA:
- Updates the `aea init` command to set the local as default registry and IPFS as default remote registry
- Updates the `aea test packages` to include the agent tests
- Introduces
  - `aea packages` command group to manage local packages repository
  - `aea packages lock` command to lock all available packages and create `packages.json` file
  - `aea packages sync` command to synchronize the local packages repository

Chores:
- Fix README header link
- Removes `shebangs` from non-script files
- Adds a command validator for docs and Makefile
- Deprecates the usage of `hashes.csv` to maintain packages consistency

Tests:
- Fixes test failures introduced on `v1.18.0`

## 1.18.0.post1 (2022-09-06)

AEA:
- Reverts a problematic package loading logic introduced in `1.18.0`

Tests:
- Fixes flaky tests

Chores:
- Restructures CI to avoid environment cross-effects between the package and framework tests

## 1.18.0 (2022-09-04)

AEA:
- Fixes protocol header string regex.
- Adds `FIELDS_WITH_NESTED_FIELDS` and `NESTED_FIELDS_ALLOWED_TO_UPDATE` in the base config class.
- Introduces `aea test` command group:
  - `aea test item_type public_id`: Run all tests of the AEA package specified by `item_type` and `public_id`
  - `aea test by-path package_dir`: Run all the tests of the AEA package located at `package_dir`
  - `aea test packages`: Runs all tests in the `packages` (local registry) folder.
  - `aea test`: Runs tests in the `tests` folder, if present in the agent folder.

Tests:
- Ports tests for the following packages into their respective package folders
  - `packages/valory/protocols/acn`
  - `packages/valory/protocols/tendermint`
  - `packages/valory/connections/p2p_libp2p/libp2p_node/dht/dhttests`
  - `packages/open_aea/protocols/signing`
  - `packages/fetchai/skills/generic_seller`
  - `packages/fetchai/skills/http_echo`
  - `packages/fetchai/skills/echo`
  - `packages/fetchai/skills/erc1155_client`
  - `packages/fetchai/skills/gym`
  - `packages/fetchai/skills/erc1155_deploy`
  - `packages/fetchai/skills/generic_buyer`
  - `packages/fetchai/protocols/http`
  - `packages/fetchai/protocols/fipa`
  - `packages/fetchai/protocols/default`
  - `packages/fetchai/protocols/state_update`
  - `packages/fetchai/protocols/ledger_api`
  - `packages/fetchai/protocols/oef_search`
  - `packages/fetchai/protocols/contract_api`
  - `packages/fetchai/protocols/gym`
  - `packages/fetchai/protocols/tac`
  - `packages/fetchai/connections/ledger`
  - `packages/fetchai/connections/http_server`
  - `packages/fetchai/connections/local`
  - `packages/fetchai/connections/stub`
  - `packages/fetchai/connections/gym`
  - `packages/fetchai/connections/http_client`
  - `packages/fetchai/contracts/erc1155`

## 1.17.0 (2022-08-26)

AEA:
- Updates the deploy image Dockerfile to use Python 3.10
- Updates the deploy image Dockerfile to utilize remote registry when fetching components
- Improves handling for variables with potential none values

Chore:
- Bumps `mistune` to a secure version
- Bumps `protobuf` dependencies to address `dependabot` security warning
- Improves command regex on `scripts/check_doc_ipfs_hashes.py`
- Updates `tox` definitions and `Makefile` targets to align with the latest changes

## 1.16.0 (2022-08-18)

AEA:
- Adds schema validation for global CLI config file
- Improves the dependency resolver
- Provides more useful error messages when circular package dependencies are present
- Adds check to make sure all the packages referenced in an AEA package's `config.yaml` are being used as imports in the code, and vice versa that all imported packages are reference in the `config.yaml`
- Adds check to make sure all the packages in an AEA project are listed in the `aea-config.yaml`
- Fixes a bug related to async function call on `TCPSocketProtocol`
- Updates transaction building to handle gas estimation properly
- Update `ContractConfig` class to include contract dependencies in the dependency list

Docs:
- Adds missing command on the `http-echo-demo.md` doc.

Chore:
- Add the gitleaks scan job

## 1.15.0 (2022-08-01)

AEA:
- Updates the protocol generator to use `protocol generator version` as a header rather than using framework version

Chore:
- Cleans up remnants of py3.6
- Updated the release process
- Adds skaffold profiles for releases

## 1.14.0 (2022-07-29)

AEA:
- Adds property to determine if skill is abstract in context
- Fixes ACN process termination
- Refactors ACN tests and adds auto multiplex
- Randomizes libp2p test directories
- Resolves an SSL issue

Chore:
- Updates the consistency-check script to verify that packages have been pushed to IPFS

## 1.13.0 (2022-07-14)

AEA:
- Add test to check package hash on signing protocol constant
- Adds support for CID v1 IPFS hashes

Plugins:
- Updates the `IPFSDaemon` to perform ipfs installation check only when initialised locally.

Packages:
- Upgrades certificate request dates on connection components
- Adds extra logging on internode communication

Docs:
- Adds a FAQ section

## 1.12.0 (2022-07-06)

AEA:
- Updated the default IPFS node multiaddr to the production one
- Fixes CSV io issues on windows
- Makes `publish` command patchable for `open-autonomy`

Plugins:
- Introduces the `raise_on_retry` parameter to the ledgers.

Docs:
- Updates the default font family
- Updates documentation to use IPFS hashes to work with the components

Chore:
- Fixes resolution issues for `packaging` dependency
- Introduces script to check IPFS hash consistency in the documentation

## 1.11.0 (2022-06-22)

AEA:
- Makes `aea publish`, `aea fetch`, `aea push-all` commands patchable to support service packages on `open-autonomy`

Plugins:
- Adds `Proof Of Authority` chain support on ethereum plugin
- Adds gas pricing mechanism for `Polygon` chain on ethereum plugin

Docs:
- Updates docs to use IPFS hashes to work with the packages
- Updates images are in .SVG

Chores:
- Updates the release guide
- Updates Dockerfiles to use `Python 3.10`
- Adds skaffold config to build and tag images

## 1.10.0 (2022-06-09)

AEA:
- Makes config loader patchable
- Adds support for Python 3.10 and removes support for Python 3.6
- Enables fingerprinting for files in `Agent` components
- Adds support for specifying vendors when generating hashes
- Enables the usage of environment variables on `aea config` command

Plugins:
- Introduces benchmark CLI plugin

Docs:
- Add docs for benchmark CLI plugin

Chore:
- Pins correct versions on CI workflow
- Bumps `pywin32` version to `304`
- Bumps `black` and `click` to stable versions
- Separates tox environments for python{3.7, 3.8, 3.9} and Python3.10

## 1.9.0 (2022-05-25)

AEA:
- Introduces `check-packages` command to check package integrity
- Introduces a new component type `service`
- Makes dialogues accessible via their respective handlers
- Fixes default remote registry setting bug
- Introduces `push-all` command to publish all available packages to a specific registry
- Updates `aea hash all` command to extend public ids when hashing

Docs:
- Adds docs on IPFS registry usage

Chores:
- Updates `check_package_versions_in_docs.py` to use new PublicId format


## 1.8.0 (2022-05-12)

AEA:
- Extends the `run` command to print all available addresses at the AEA start up.
- Introduces support for usage of hashes as a part of the `PublicId`
- Adds support for IPFS based registry
- Introduces dialogue cleanup
- Adds support for removing the temporal `None` values in the dialogue label
- Updated the profiler to
  - Removing the unwanted variables in profiling
  - Set counters also in the destructor
  - Only iterate the gc one
  - Use types blacklist
  - Get info from all objects
- Adds support for memray in the profiler
- Ports the `generate_all_protocols.py` and `generate_ipfs_hashes.py` to `aea.cli` as a command line tools.
- Adds support for the usage of environment variables in `issue-certificates` command.

Pluging:
-  Updates IPFS cli plugin tool to support remote registry and extended `PublicId`

Packages:
- Updated `tendermint/protocol` for config sharing

Chores:
- Adds support for IPFS in CI for windows based environments
- Profile parser checks for non empty data before plotting
- The paths to download the packages folder with svn are now pointing to the version tag rather than main.
- Adds the missing search plugin for mkdocs.
- Adds new functionality to the log parser to add an extra plot with common objects in the garbage collector.

## 1.7.0 (2022-04-15)

AEA:
- List all available packages at the AEA start up.
- Updates profiler module to use tracemalloc.
- Fixes dialogue cleanup.

Plugins:
- Fixes repricing bug on ethereum plugin.
- Adds support for lazy imports on cosmos plugin.

Packages:
- Adds protocol package for tendermint.

Docs:
- Adds docs for newly introduced ACN modules and packages.


## 1.6.0 (2022-03-17)

AEA:
- Adds support for packages hashing with `IPFSHashOnly` from `aea.helpers.ipfs.base`
- Updates the `aea run` command to print hash table for available packages in an agent project

Plugins:
- Makes error raising optional when sending transactions and adds error logging for the same

Docs:
- Adds documentation for the newly introduced profiling script
- Removes reference to `docs.fetch.ai`

Chores:
- Adds a script to analyze and visualize profiling data from agent runs
- Updates authors list


## 1.5.0 (2022-02-26)

AEA:
- Adds in null equivalents so that environment variables can default to a none value
- Adds support for remote IPFS registry usage in CLI tool
- Adds support to show IPFS hashes of each component yaml at start of `aea run`

Plugins:
- Adds support for remote IPFS registry usage in IPFS plugin
- Fixes gas price repricing strategy in ethereum ledger plugin

Packages:
- Ports `acn` packages from fetchai repo
- Bumps protobuf compiler version and updates protocols

Docs:
- Adds demo of http connections and skills
- Adds demo of environment variable usage
- Adds miscellaneous updates to documentation based on developer feedback

Chores:
- Updates copyright script to support all patterns
- Simplifies Dockerfiles and removes unneeded dependencies


## Plugins patch (2022-01-27)

Plugins:
- Bumps `open-aea-ethereum-ledger` to `1.4.1` after fixing a bug in the log retrieval logic.

## 1.4.0 (2022-01-26)

AEA:
- Exposes agent data directory on skill context.
- Adds support for environment variables loading from aea-config files.
- Extends contract base class to support new plugin functionality.

Plugins:
- Adds support for transaction preparation and log retrieval into the ethereum plugin.
- Adds support for retrieving the revert reason when transaction is not verified in ethereum plugin.

Docs:
- Simplifies documentation further and updates with latest features

## Plugins patch (2022-01-15)

Plugins:
- Bumps `open-aea-ethereum-ledger` to `1.3.2` after adding tip increase logic

## Plugins patch (2022-01-05)

Plugins:
- Fixes dynamic gas pricing on open-aea-ethereum
- Improves daemon availability check in `IPFSDaemon` on `open-aea-cli-ipfs`
- Bumps `open-aea-cli-ipfs` and open-aea-ethereum-ledger to `1.3.1`

Docs:
- Removes reference to fetch.ai.

## 1.3.0 (2021-12-31)

AEA:
- Adds support to scaffold packages outside an AEA project
- Adds support for IPFS package hashing and IPFS based registry.
- Allows contracts to depend on other contracts.

Plugins:
- Adds support for EIP1559 based gas estimation strategy on aea-ledger-ethereum.
- Adds support for package hashing and local IPFS registry on `aea-cli-ipfs`.
- Bumps `aea-ledger-ethereum` and `aea-cli-ipfs` to `1.3.0`.

Docs:
- Applies new styling
- Simplifies documentation and updates with latest features


## 1.2.0 (2021-11-21)

AEA:
- Adds type hint for dialogue valid replies in protocol generator
- Adds generator fixes to pass darglint checks
- Adds various test fixes and fixes on MAM
- Allows additional entropy to be passed to key generation in plugins (including. via CLI)
- Fixes an issue with message key-value setter
- Fixes an issue with improper termination of subprocesses in the test tools
- Fixes typing issues
- Miscellaneous minor fixes

Plugins:
- Updates aea-ledger-ethereum for EIP1159 compatibility
- Bumps aea-ledger-ethereum dependencies

Packages:
- Miscellaneous minor fixes

Docs:
- Updates API documentation

Chores:
- Enables darglint for protocols

## 1.1.0 (2021-10-31)

AEA:
- Forks 1.1.0 of legacy AEA with the aim of maintaining backwards compatibility where possible
- Removes GOP decision maker handler to reduce dependencies
- Removes hard-coded registry API URL
- Changes default ledger to ethereum
- Removes dependency on fetchai packages
- Removes interact command

Plugins:
- Forks plugins, unfortunately cannot maintain plugin support for legacy aea plugins due to their dependency on legacy aea
- Fixes typing issues

Packages:
- Removes most fetchai packages apart from those currently used in tests
- Adds `open_aea/signing:1.0.0` protocol

Docs:
- Removes most demos

Chores:
- Makes all necessary changes to move to `open-aea`


# Release History - legacy AEA

## 1.1.0 (2021-10-13)

AEA:
- Adds public keys to agent identity and skill context
- Adds contract test tool
- Adds multiprocess support for task manager
- Adds multiprocess backed support to `MultiAgentManager`
- Adds support for excluding connection on `aea run`
- Adds support for adding a key that is being generated (`—add-key` option for `generate-key` command)
- Adds check for dependencies to be present in registry on a package push
- Makes more efficient installing of project dependencies on `aea install`
- Adds dependency conflict detection on `aea install`
- Improves pip install error details on `aea install`
- Adds validation of `aea_version` when loading configuration
- Adds a check for consistency of package versions in `MultiAgent Manager`
- Adds better error reporting for aea registry requests
- Fixes IPFS hash calculation for large files
- Fixes protobuf dictionary serializer's uncovered cases and makes it deterministic
- Fixes scaffolding of error and decision maker handlers
- Fixes pywin32 problem when checking dependency
- Improves existing testing tools

Benchmarks:
- Adds agents construction and decision maker benchmark cases

Plugins:
- Upgrades fetchai plugin to use CosmPy instead of CLI calls
- Upgrades cosmos plugin to use CosmPy instead of CLI calls
- Upgrades fetchai plugin to use StargateWorld
- Upgrades cosmos plugin to Stargate
- Sets the correct maximum Gas for fetch.ai plugin

Packages:
- Adds support for Tac to be run against fetchai StargateWorld test-net
- Adds more informative error messages to CosmWasm ERC1155 contract
- Adds support for atomic swap to CosmWasm ERC1155 contract
- Adds an ACN protocol that formalises ACN communication using the framework's protocol language
- Adds `cosm_trade` protocol for preparing atomic swap transactions for cosmos-based networks
- Adds https support for server connection
- Adds parametrising of http(s) in soef connection
- Fixes http server content length response problem
- Updates Oracle contract to 0.14
- Implements the full ACN spec throughout the ACN packages
- Implements correct error code usage in ACN packages
- Refactors ACN packages to unify reused logic
- Adds tests for gym skills
- Adds dockerised SOEF
- Adds libp2p mailbox connection
- Multiple fixes and stability improvements for `p2p_libp2p` connections

Docs:
- Adds ACN internals documentation
- Fixes tutorial for HTTP connection and skill
- Multiple additional docs updates
- Adds more context to private keys docs

Chores:
- Various development features bumped
- Bumped Mermaid-JS, for UML diagrams to major version 8
- Applies darglint to the code

Examples:
- Adds a unified script for running various versions/modes of Tac

## 1.0.2 (2021-06-03)

AEA:
- Bounds versions of dependencies by next major
- Fixes incoherent warning message during package loading
- Improves various incomprehensible error messages
- Adds debug log message when abstract components are loaded
- Adds tests and minor fixes for password related CLI commands and password usage in `MultiAgentManager`
- Adds default error handler in `MultiAgentManager`
- Ensures private key checks are performed after override setting in `MultiAgentManager`
- Applies docstring fixes suggested by `darglint`
- Fixes `aea push --local` command to use correct author
- Fixes `aea get-multiaddress` command to consider overrides

Plugins:
- Bounds versions of dependencies by next major

Packages:
- Updates `p2p_libp2p` connection to use TCP sockets for all platforms
- Multiple fixes on `libp2p_node` including better error handling and stream creation
- Adds sending queue in `p2p_libp2p` connection to handle sending failures
- Adds unit tests for `libp2p_node` utils
- Adds additional tests for `p2p_libp2p` connection
- Fixes location bug in AW5
- Improves connection check handling in soef connection
- Updates oracle and oracle client contracts for better access control
- Adds skill tests for `erc1155` skills
- Adds skill tests for `aries` skills
- Fixes minor bug in ML skills
- Multiple additional tests and test stability fixes

Docs:
- Extends demo docs to include guidance of usage in AEA Manager
- Adds short guide on Kubernetes deployment
- Multiple additional docs updates

Chores:
- Adds `--no-bump` option to `generate_all_protocols` script
- Adds script to detect if aea or plugins need bumping
- Bumps various development dependencies
- Adds Golang and GCC in Windows install script
- Adds `darglint` to CI

Examples:
- Updates TAC deployment scripts and images

## - (2021-05-05)

Packages:
- Adds node watcher to `p2p_libp2p` connection
- Improves logging and error handling in `p2p_libp2p` node
- Addresses potential overflow issue in `p2p_libp2p` node
- Fixes concurrency issue in `p2p_libp2p` node which could lead to wrongly ordered envelopes
- Improves logging in TAC skills
- Fixes Exception handling in connect/disconnect calls of soef connection
- Extends public DHT tests to include staging
- Adds tests for envelope ordering for all routes
- Multiple additional tests and test stability fixes

## 1.0.1 (2021-04-30)

AEA:
- Fixes wheels issue for Windows
- Fixes password propagation for certificate issuance in `MultiAgentManager`
- Improves error message when local registry not present

AEALite:
- Adds full protocol support
- Adds end-to-end interaction example with AEA (based on `fetchai/fipa` protocol)
- Multiple additional tests and test stability fixes

Packages:
- Fixes multiple bugs in `ERC1155` version of TAC
- Refactors p2p connections for better separation of concerns and maintainability
- Integrates aggregation with simple oracle skill
- Ensures genus and classifications are used in all skills using SOEF
- Extends SOEF connection to implement `oef_search` protocol fully
- Handles SOEF failures in skills
- Adds simple aggregation skills including tests and docs
- Adds tests for registration AW agents
- Adds tests for reconnection logic in p2p connections
- Multiple additional tests and test stability fixes

Docs:
- Extends car park demo with usage guide for AEA manager
- Multiple additional docs updates

Examples:
- Adds TAC deployment example

## 1.0.0 (2021-03-30)

- Improves contributor guide
- Enables additional pylint checks
- Adds configuration support on exception behaviour in ledger plugins
- Improves exception handling in `aea-ledger-cosmos` and `aea-ledger-fetchai` plugins
- Improves quickstart guide
- Fixes multiple flaky tests
- Fixes various outdated metadata
- Resolves a CVE (CVE-2021-27291) affecting development dependencies
- Adds end-to-end support and tests for simple oracle on Ethereum and Fetch.ai ledgers
- Multiple minor fixes
- Multiple additional tests and test stability fixes

## 1.0.0rc2 (2021-03-28)

- Extends CLI command `aea fingerprint` to allow fingerprinting of agents
- Improves `deploy-image` Docker example
- Fixes a bug in `MultiAgentManager` which leaves it in an unclean state when project adding fails
- Fixes dependencies of `aea-legder-fetchai`
- Improves guide on HTTP client and server connection
- Removes pickle library usage in the ML skills
- Adds various consistency checks in configurations
- Replaces usage of `pyaes` with `pycryptodome` in plugins
- Changes generator to avoid non-idiomatic usage of type checks
- Multiple minor fixes
- Multiple additional tests and test stability fixes

## 1.0.0rc1 (2021-03-24)

- Adds CLI command `aea get-public-key`
- Adds support for encrypting private keys at rest
- Adds support for configuration of decision maker and error handler instances from `aea-config.yaml`
- Adds support for explicitly marking behaviours and handlers as dynamic
- Adds support for fetchai ledger to oracle skills and contract
- Adds timeout support on multiplexer calls to connections
- Fixes bug in regex constrained string for id validation
- Adds docs section on how AEAs satisfy 12-factor methodology
- Adds docs section on tradeoffs made in `v1`
- Adds example for logs streaming to browser
- Removes multiple temporary hacks for backwards compatibility
- Adds skills tests coverage for `echo` and `http_echo` skills
- Adds `required_ledgers` field in `aea-config.yaml`
- Removes `registry_path` field in `aea-config.yaml`
- Adds `message_format` field to cert requests
- Removes requirement for exact protocol buffers compiler, prints version used in protocols
- Adds support to configure task manager mode via `aea-config.yaml`
- Fixed spelling across docstrings in code base
- Multiple minor fixes
- Multiple docs updates to fix order of CLI commands with respect to installing dependencies
- Multiple additional tests and test stability fixes


## 0.11.2 (2021-03-17)

- Fixes a package import issue
- Fixes an issue where `AgentLoop` did not teardown properly under certain conditions
- Fixes a bug in testing tools
- Fixes a bug where plugins are not loaded after installation in `MultiAgentManager`
- Adds unit tests for weather, thermometer and car park skills
- Fixes a missing dependency in Windows
- Improves SOEF connections' error handling
- Fixes bug in ML skills and adds unit tests
- Adds script to bump plugin versions
- Adds gas price strategy support in `aea-ledger-ethereum` plugin
- Adds CLI plugin for IPFS interactions (add/get)
- Adds support for CLI plugins to framework
- Multiple additional tests and test stability fixes

## 0.11.1 (2021-03-06)

- Bumps `aiohttp` to `>=3.7.4` to address a CVE affecting `http_server`, `http_client` and `webhook` connections
- Adds script to ensure Pipfile and `tox.ini` dependencies align
- Enforces presence of `protocol_specification_id` in `protocol.yaml`
- Adds support for installation of agent-level PyPI dependencies in `AEABuilder`
- Sets default ledger plugin during `aea create`
- Updates various agent packages with missing ledger plugin dependencies
- Bumps various development dependencies
- Renames `coin_price` skill to `advanced_data_request` skill and generalises it
- Updates `fetch_beacon` skill to use `ledger` connection
- Multiple docs updates to fix order of CLI commands with respect to installing dependencies
- Multiple additional tests and test stability fixes

## 0.11.0 (2021-03-04)

- Adds slots usage in frequently used framework objects, including `Dialogue`
- Fixes a bug in `aea upgrade` command where eject prompt was not offered
- Refactors skill component configurations to allow for skill components (`Handler`, `Behaviour`, `Model`) to be placed anywhere in a skill
- Extends skill component configuration to specify optional `file_path` field
- Extracts all ledger specific functionality in plugins
- Improves error logging in http server connection
- Updates `Development - Use case` documentation
- Adds restart support to `p2p_libp2p` connection on read/write failure
- Adds validation of default routing and default connection configuration
- Refactors and significantly simplifies routing between components
- Limits usage of `EnvelopeContext`
- Adds support for new CosmWasm message format in ledger plugins
- Adds project loading checks and optional auto removal in `MultiAgentManager`
- Adds support for reuse of threaded `Multiplexer`
- Fixes bug in TAC which caused agents to make suboptimal trades
- Adds support to specify dependencies on `aea-config.yaml` level
- Improves release scripts
- Adds lightweight Golang AEALite library
- Adds support for skill-to-skill messages
- Removes CLI GUI
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.10.1 (2021-02-21)

- Changes default URL of `soef` connection to https
- Improves teardown, retry and edge case handling of `p2p_libp2p` and `p2p_libp2p_client` connections
- Adds auto-generation of private keys to `MultiAgentManager`
- Exposes address getters on `MultiAgentManager`
- Improves package validation error messages
- Simplifies default `DecisionMakerHandler` and extracts advanced features in separate class
- Fixes task manager and its usage in skills
- Adds support for multi-language protocol stub generation
- Adds `data_dir` usage to additional connections
- Adds IO helper function for consistent file usage
- Extends release helper scripts
- Removes stub connection as default connection
- Adds support for AEA usage without connections
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.10.0 (2021-02-11)

- Removes error skill from agents which do not need it
- Adds support for relay connection reconnect in ACN
- Multiplexer refactoring for easier connection handling
- Fix `erc1155` skill tests on CosmWasm chains
- Extends docs on usage of CosmWasm chains
- Adds version compatibility in `aea upgrade` command
- Introduces protocol specification id and related changes for better interoperability
- Adds synchronous connection base class
- Exposes state setter in connection base class
- Adds Yoti protocol and connection
- Multiple updates to generic buyer
- Adds additional automation to `MultiAgentManager`, including automated handling of certs, keys and other package specific data
- Multiple test improvements and fixes
- Add stricter typing and checks
- Fixes to MacOS install script
- Adds threading patch for web3
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.9.2 (2021-01-21)

- Fixes `CosmosApi`, in particular for CosmWasm
- Fixes error output from `add-key` CLI command
- Update `aea_version` in non-vendor packages when calling `upgrade` CLI command
- Extend `upgrade` command to fetch newer agent if present on registry
- Add support for mixed fetch mode in `MultiAgentManager`
- Fixes logging overrides in `MultiAgentManager`
- Configuration overrides now properly handle `None` values
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.9.1 (2021-01-14)

- Fixes multiple issues with `MultiAgentManager` including overrides not being correctly applied
- Restructures docs navigation
- Updates `MultiAgentManager` documentation
- Extends functionality of `aea upgrade` command to cover more cases
- Fixes a bug in the `aea upgrade` command which prevented upgrading across version minors
- Fixes a bug in `aea fetch` where the console output was inconsistent with the actual error
- Fixes scaffold connection constructor
- Multiple additional tests to improve stability
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.9.0 (2021-01-06)

- Adds multiple bug fixes on `MultiAgentManager`
- Adds `AgentConfigManager` for better programmatic configuration management
- Fixes auto-filling of `aea_version` field in AEA configuration
- Adds tests for confirmation skills AW2/3
- Extends `MultiAgentManager` to support proper configuration overriding
- Fixes ML skills demo
- Fixes environment variable resolution in configuration files
- Adds support to fingerprint packages by providing a path
- Adds `local-registry-sync` CLI command to sync local and remote registry
- Adds support to push vendorised packages to local registry
- Adds missing tests for code in documentation
- Adds prompt in `scaffold protocol` CLI command to hint at protocol generator
- Adds `issue-certificates` CLI command for Proof of Representation
- Adds `cert_requests` support in connections for Proof of Representation
- Adds support for Proof of Representation in ACN (`p2p_libp2p*` connections)
- Adds automated spell checking for all `.md` files and makes related fixes
- Multiple additional tests to improve stability
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.8.0 (2020-12-17)

- Adds support for protocol dialogue rules validation
- Fixes URL forwarding in http server connection
- Revises protocols to correctly define terminal states
- Adds a build command
- Adds build command support for libp2p connection
- Adds multiple fixes to libp2p connection
- Adds prometheus connection and protocol
- Adds tests for confirmation AW1 skill
- Adds oracle demo docs
- Replaces pickle with protobuf in all protocols
- Refactors OEF models to account for semantic irregularities
- Updates docs for demos relying on Ganache
- Adds generic storage support
- Adds configurable dialogue offloading
- Fixes transaction generation on confirmation bugs
- Fixes transaction processing order in all buyer skills
- Extends ledger API protocol to query ledger state
- Adds remove-key command in CLI
- Multiple tac stability fixes
- Adds support for configurable error handler
- Multiple additional tests to improve stability
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.5 (2020-11-25)

- Adds AW3 AEAs
- Adds basic oracle skills and contracts
- Replaces usage of Ropsten testnet with Ganache in packages
- Fixes multiplexer setup when used outside AEA
- Improves help command output of CLI
- Adds integration tests for simple skills
- Adds version check on CLI push
- Adds integration tests for tac negotiation skills
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.4 (2020-11-18)

- Replaces error skill handler usage with built in handler
- Extends `MultiAgentManager` to support persistence between runs
- Replaces usage of Ropsten testnet with Ganache
- Adds support for symlink creation during scaffold and add
- Makes contract interface loading extensible
- Adds support for PEP561
- Adds integration tests for launcher command
- Adds support for storage of unique page address in SOEF
- Fixes publish command bug on Windows
- Refactors constants usage throughout
- Adds support for profiling on `aea run`
- Multiple stability improvements to core asynchronous modules
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.3 (2020-11-12)

- Extends AW AEAs
- Fixes overwriting of private key files on startup
- Fixes behaviour bugs
- Adds tests for tac participation skill
- Adds development setup guide
- Improves exception logging for easier debugging
- Fixes mixed mode in upgrade command
- Reduces verbosity of some CLI commands
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.2 (2020-11-09)

- Fixes some AW2 AEAs
- Improves generic buyer AEA
- Fixes a few backwards incompatibilities on CLI (upgrade, add, fetch) introduced in 0.7.1
- Fixes geolocation in some tests
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.1 (2020-11-05)

- Adds two AEAs for Agent World 2
- Refactors dialogue class to optimize for memory
- Refactors message class to optimize for memory
- Adds mixed registry mode to CLI and makes it default
- Extends upgrade command to automatically update references of non-vendor packages
- Adds deployment scripts for `kubernetes`
- Extends configuration set/get support for lists and dictionaries
- Fixes location specifiers throughout code base
- Imposes limits on length of user defined strings like author and package name
- Relaxes version specifiers for some dependencies
- Adds support for skills to reference connections as dependencies
- Makes ledger and currency ids configurable
- Adds test coverage for the tac control skills
- Improves quick start guidance and adds docker images
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.7.0 (2020-10-22)

- Adds two AEAs for Agent World 1
- Adds support to apply configuration overrides to CLI calls transfer and get-wealth
- Adds install scripts to install AEA and dependencies on all major OS (Windows, MacOs, Ubuntu)
- Adds developer mailing list opt-in step to CLI `init`
- Modifies custom configurations in `aea-config` to use public id
- Adds all non-optional fields in `aea-config` by default
- Fixes upgrade command to properly handle dependencies of non-vendor packages
- Remove all distributed packages and add them to registry
- Adds public ids to all skill `init` files and makes it a requirement
- Adds primitive benchmarks for libp2p node
- Adds Prometheus monitoring to libp2p node
- Makes body a private attribute in message base class
- Renames `bodyy` to `body` in HTTP protocol
- Adds support for abstract connections
- Refactors protobuf schemas for protocols to avoid code duplication
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.6.3 (2020-10-16)

- Adds skill testing tools and documentation
- Adds human readable log output regarding configuration for `p2p_libp2p` connection
- Adds support to install PyPI dependencies from `AEABuilder` and `MultiAgentManager`
- Adds CLI upgrade command to upgrade entire agent project and components
- Extends CLI remove command to include option to remove dependencies
- Extends SOEF chain identifier support
- Adds CLI transfer command to transfer wealth
- Adds integration tests for skills generic buyer and seller using skill testing tool
- Adds validation of component configurations when setting component configuration overrides
- Multiple refactoring of internal configuration and helper objects and methods
- Fix a bug on CLI push local with latest rather than version specifier
- Adds `README.md` files in all agent projects
- Adds agent name in logger paths of runnable objects
- Fixes tac skills to work with and without ERC1155 contract
- Adds additional validations on message flow
- Multiple docs updates based on user feedback
- Multiple additional tests and test stability fixes

## 0.6.2 (2020-10-01)

- Adds `MultiAgentManager` to manage multiple agent projects programmatically
- Improves SOEF connection reliability on unregister
- Extends configuration classes to handle overriding configurations programmatically
- Improves configuration schemas and validations
- Fixes Multiplexer termination errors
- Allow finer-grained override of component configurations from `aea-config`
- Fixes tac controller to work with Ethereum contracts again
- Fixes multiple deploy and development scripts
- Introduces `isort` to development dependencies for automated import sorting
- Adds reset password command to CLI
- Adds support for abbreviated public ids (latest) to CLI and configurations
- Adds additional documentation string linters for improved API documentation checks
- Multiple docs updates including additional explanations of ACN architecture
- Multiple additional tests and test stability fixes

## 0.6.1 (2020-09-17)

- Adds a standalone script to deploy an ACN node
- Adds filtering of out-dated addresses in DHT lookups
- Updates multiple developer scripts
- Increases code coverage of all protocols to 100%
- Fixes a disconnection issue of the multiplexer
- Extends soef connection to support additional registration commands and search responses
- Extends `oef_search` protocol to include success performative and agent info in search response
- Adds `README.md` files to all skills
- Adds configurable exception policy handling for multiplexer
- Fixes support for http headers in http server connection
- Adds additional consistency checks on addresses in dialogues
- Exposes decision maker address on skill context
- Adds comprehensive benchmark scripts
- Multiple docs updates including additional explanations of soef usage
- Multiple additional tests and test stability fixes

## 0.6.0 (2020-09-01)

- Makes `FetchAICrypto` default again
- Bumps `web3` dependencies
- Introduces support for arbitrary protocol handling by DM
- Removes custom fields in signing protocol
- Refactors and updates dialogue and dialogues models
- Moves dialogue module to protocols module
- Introduces `MultiplexerStatus` to collect aggregate connection status
- Moves Address types from mail to common
- Updates `FetchAICrypto` to work with Agentland
- Fixes circular dependencies in helpers and configurations
- Unifies contract loading with loading mechanism of other packages
- Adds get-multiaddress command to CLI
- Updates helpers scripts
- Introduces `MultiInbox` to unify internal message handling
- Adds additional linters (eradicate, more `pylint` options)
- Improves error reporting in libp2p connection
- Replaces all assert statements with proper exceptions
- Adds skill id to envelope context for improved routing
- Refactors IPC pipes
- Refactors core dependencies
- Adds support for multi-page agent configurations
- Adds type field to all package configurations
- Multiple docs updates including additional explanations of contracts usage
- Multiple additional tests and test stability fixes

## 0.5.4 (2020-08-13)

- Adds support for Windows in P2P connections
- Makes all tests Windows compatible
- Adds integration tests for P2P public DHT
- Modifies contract base class to make it cross-ledger compatible
- Changes dialogue reference nonce generation
- Fixes tac skills (non-contract versions)
- Fixes Aries identity skills
- Extends cosmos crypto API to support `cosmwasm`
- Adds full test coverage for framework and connection packages
- Multiple docs updates including automated link integrity checks
- Multiple additional tests and test stability fixes

## 0.5.3 (2020-08-05)

- Adds support for re-starting agent after stopping it
- Adds full test coverage for protocols generator
- Adds support for dynamically adding handlers
- Improves P2P connection startup reliability
- Addresses P2P connection race condition with long running processes
- Adds connection states in connections
- Applies consistent logger usage throughout
- Adds key rotation and randomised locations for integration tests
- Adds request delays in SOEF connection to avoid request limits
- Exposes runtime states on agent and removes agent liveness object
- Adds readme files in protocols and connections
- Improves edge case handling in dialogue models
- Adds support for `cosmwasm` message signing
- Adds test coverage for test tools
- Adds dialogues models in all connections where required
- Transitions ERC1155 skills and simple search to SOEF and P2P
- Adds full test coverage for skills modules
- Multiple docs updates
- Multiple additional tests and test stability fixes

## 0.5.2 (2020-07-21)

- Transitions demos to agent-land test network, P2P and SOEF connections
- Adds full test coverage for helpers modules
- Adds full test coverage for core modules
- Adds CLI functionality to upload `README.md` files with packages
- Adds full test coverage for registries module
- Multiple docs updates
- Multiple additional tests and test stability fixes

## 0.5.1 (2020-07-14)

- Adds support for agent name being appended to all log statements
- Adds redesigned GUI
- Extends dialogue API for easier dialogue maintenance
- Resolves blocking logic in OEF and gym connections
- Adds full test coverage on AEA modules configurations, components and mail
- Adds ping background task for soef connection
- Adds full test coverage for all connection packages
- Multiple docs updates
- Multiple additional tests and test stability fixes

## 0.5.0 (2020-07-06)

- Refactors all connections to be fully asynchronous friendly
- Adds almost complete test coverage on connections
- Adds complete test coverage for CLI and CLI GUI
- Fixes CLI GUI functionality and removes OEF node dependency
- Refactors P2P go code and increases test coverage
- Refactors protocol generator for higher code reusability
- Adds option for skills to depend on other skills
- Adds abstract skills option
- Adds ledger connections to execute ledger related queries and transactions, removes ledger APIs from skill context
- Adds contracts registry and removes them from skill context
- Rewrites all skills to be fully message based
- Replaces internal messages with protocols (signing and state update)
- Multiple refactoring to improve `pylint` adherence
- Multiple docs updates
- Multiple test stability fixes

## 0.4.1 (2020-06-15)

- Updates component package module loading for skill and connection
- Unifies component package loading across package types
- Adds connections registry to resources
- Upgrades CLI commands for easier programmatic usage
- Adds `AEARunner` and `AEALauncher` for programmatic launch of multiple agents
- Refactors `AEABuilder` to support reentrancy and resetting
- Fixes tac packages to work with ERC1155 contract
- Multiple refactoring to improve public and private access patterns
- Multiple docs updates
- Multiple test stability fixes

## 0.4.0 (2020-06-08)

- Updates message handling in skills
- Replaces serialiser implementation; all serialization is now performed framework side
- Updates all skills for compatibility with new message handling
- Updates all protocols and protocol generator
- Updates package loading mechanism
- Adds `p2p_libp2p_client` connection
- Fixes CLI bugs and refactors CLI
- Adds eject command to CLI
- Exposes identity and connection cryptos to all connections
- Updates connection loading mechanism
- Updates all connections for compatibility with new loading mechanism
- Extracts multiplexer into its own module
- Implements list all CLI command
- Updates wallet to split into several crypto stores
- Refactors component registry and resources
- Extends soef connection functionality
- Implements `AEABuilder` reentrancy
- Updates `p2p_libp2p` connection
- Adds support for configurable runtime
- Refactors documentation
- Multiple docs updates
- Multiple test stability fixes

## 0.3.3 (2020-05-24)

- Adds option to pass ledger APIs to `AEABuilder`
- Refactors decision maker: separates interface and implementation; adds loading mechanisms so framework users can provide their own implementation
- Adds asynchronous and synchronous agent loop implementations; agent can be run in both `sync` and `async` mode
- Completes transition to atomic CLI commands (fetch, generate, scaffold)
- Refactors dialogue API: adds much simplified API; updates generator accordingly; updates skills
- Adds support for crypto module extensions: framework users can register their own crypto module
- Adds crypto module and ledger support for cosmos
- Adds simple-oef (soef) connection
- Adds `p2p_libp2p` connection for true P2P connectivity
- Adds PyPI dependency consistency checks for AEA projects
- Refactors CLI for improved programmatic usage of components
- Adds skill exception handling policies and configuration options
- Adds comprehensive documentation of configuration files
- Multiple docs updates
- Multiple test stability fixes

## 0.3.2 (2020-05-07)

- Adds dialogue generation functionality to protocol generator
- Fixes add CLI commands to be atomic
- Adds Windows platform support
- Stability improvements to test pipeline
- Improves test coverage of CLI
- Implements missing doc tests
- Implements end-to-end tests for all skills
- Adds missing agent projects to registry
- Improves `AEABuilder` class for programmatic usage
- Exposes missing AEA configurations on agent configuration file
- Extends Aries demo
- Adds method to check stdout for test cases
- Adds code of conduct and security guidelines to repo
- Multiple docs updates
- Multiple additional unit tests
- Multiple additional minor fixes and changes

## 0.3.1 (2020-04-27)

- Adds `p2p_stub` connection
- Adds `p2p_noise` connection
- Adds webhook connection
- Upgrades error handling for error skill
- Fixes default timeout on main agent loop and provides setter in `AEABuilder`
- Adds multithreading support for launch command
- Provides support for keyword arguments to AEA constructor to be set on skill context
- Renames `ConfigurationType` with `PackageType` for consistency
- Provides a new `AEATestCase` class for improved testing
- Adds execution time limits for act/react calls
- TAC skills refactoring and contract integration
- Supports contract dependencies being added automatically
- Adds HTTP example skill
- Allows for skill inactivation during initialisation
- Improves error messages on skill loading errors
- Improves `README.md` files, particularly for PyPI
- Adds support for Location based queries and descriptions
- Refactors skills tests to use `AEATestCase`
- Adds fingerprint and scaffold CLI command for contract
- Adds multiple additional docs tests
- Makes task manager initialize pool lazily
- Multiple docs updates
- Multiple additional unit tests
- Multiple additional minor fixes and changes

## 0.3.0 (2020-04-02)

- Introduces IPFS based hashing of files to detect changes, ensure consistency and allow for content addressing
- Introduces `aea fingerprint` command to CLI
- Adds support for contract type packages which wrap smart contracts and their APIs
- Introduces `AEABuilder` class for much improved programmatic usage of the framework
- Moves protocol generator into alpha stage for light protocols
- Switches CLI to use remote registry by default
- Comprehensive documentation updates on new and existing features
- Additional demos to introduce the contracts functionality
- Protocol, Contract, Skill and Connection inherits from the same class, Component
- Improved APIs for Configuration classes
- All protocols now generated with protocol generator
- Multiple additional unit tests
- Multiple additional minor fixes and changes

## 0.2.4 (2020-03-25)

- Breaking change to all protocols as we transition to auto-generated protocols
- Fixes to protocol generator to move it to alpha status
- Updates to documentation on protocols and OEF search and communication nodes
- Improvements and fixes to AEA launch command
- Multiple docs updates and restructuring
- Multiple additional minor fixes and changes

## 0.2.3 (2020-03-19)

- Fixes stub connection file I/O
- Fixes OEF connection teardown
- Fixes CLI GUI subprocesses issues
- Adds support for URI based routing of envelopes
- Improves skill guide by adding a service provider agent
- Protocol generator bug fixes
- Add `aea_version` field to package YAML files for version management
- Multiple docs updates and restructuring
- Multiple additional minor fixes and changes

## 0.2.2 (2020-03-09)

- Fixes registry to only load registered packages
- Migrates default protocol to generator produced version
- Adds http connection and http protocol
- Adds CLI `init` command for easier setting of author
- Refactoring and behind the scenes improvements to CLI
- Multiple docs updates
- Protocol generator improvements and fixes
- Adds CLI launch command to launch multiple agents
- Increases test coverage for AEA package and tests package
- Make project comply with PEP 518
- Multiple additional minor fixes and changes

## 0.2.1 (2020-02-21)

- Add minimal `aea install`
- Updates finite state machine behaviour to use any simple behaviour in states
- Adds example of programmatic and CLI based AEAs interacting
- Exposes the logger on the skill context
- Adds serialization (encoding/decoding) support to protocol generator
- Adds additional docs and videos
- Introduces test coverage to all code in docs
- Increases test coverage for AEA package
- Multiple additional minor fixes and changes

## 0.2.0 (2020-02-07)

- Skills can now programmatically register behaviours
- Tasks are no longer a core component of the skill, the functor pattern is used
- Refactors the task manager
- Adds nonces to transaction data so transactions can be verified
- Adds documentation for the protocol generator
- Fixes several compatibility issues between CLI and registry
- Adds skills to connect a thermometer to an AEA
- Adds generic buyer and seller skills
- Adds much more documentation on AEA vs MVC frameworks, core components, new guides and more
- Removes the wallet from the agent constructor and moves it to the AEA constructor
- Allows behaviours to be initialized from a skill
- Adds multiple improvements to the protocol generator, including custom types and serialization
- Removes the default crypto object
- Replaces `SharedClass` with `Model` taxonomy for easier transition for web developers
- Adds bandit to CLI for security checks
- Makes private key paths in configurations a dictionary so values can be set from CLI
- Introduces Identity object
- Increases test coverage
- Multiple additional minor fixes and changes

## 0.1.17 (2020-01-27)

- Add programmatic mode flag to AEA
- Introduces vendorised project structure
- Adds further tests for decision maker
- Upgrades sign transaction function for Ethereum API proxy
- Adds black and bugbear to linters
- Applies public id usage throughout AEA business logic
- Adds guide on how to deploy an AEA on a raspberry pi
- Addresses multiple issues in the protocol generator
- Fixes `aea-config`
- Adds CLI commands to create wealth and get wealth and address
- Change default author and license
- Adds guide on agent vs AEAs
- Updates docs and improves guides
- Adds support for inactivating skills programmatically
- Makes decision maker run in separate thread
- Multiple additional minor fixes and changes

## 0.1.16 (2020-01-12)

- Completes tac skills implementation
- Adds default ledger field to agent configuration
- Converts ledger APIs to dictionary fields in agent configuration
- Introduces public ids to CLI and deprecate usage of package names only
- Adds local push and public commands to CLI
- Introduces ledger API abstract class
- Unifies import paths for static and dynamic imports
- Disambiguates import paths by introducing pattern of `packages.author.package_type_pluralized.package_name`
- Adds agent directory to packages with some samples
- Adds protocol generator and exposes on CLI
- Removes unused configuration fields
- Updates docs to align with recent changes
- Adds additional tests on CLI
- Multiple additional minor fixes and changes

## 0.1.15 (2019-12-19)

- Moves non-default packages from AEA to packages directory
- Supports get & set on package configurations
- Changes skill configuration resource types from lists to dictionaries
- Adds additional features to decision maker
- Refactors most protocols and improves their API
- Removes multiple unintended side-effects of the CLI
- Improves dependency referencing in configuration files
- Adds push and publish functionality to CLI
- Introduces simple and composite behaviours and applies them in skills
- Adds URI to envelopes
- Adds guide for programmatic assembly of an AEA
- Adds guide on agent-oriented development
- Multiple minor doc updates
- Adds additional tests
- Multiple additional minor fixes and changes

## 0.1.14 (2019-11-29)

- Removes dependency on OEF SDK's FIPA API
- Replaces dialogue id with dialogue references
- Improves CLI logging and list/search command output
- Introduces multiplexer and removes mailbox
- Adds much improved tac skills
- Adds support for CLI integration with registry
- Increases test coverage to 99%
- Introduces integration tests for skills and examples
- Adds support to run multiple connections from CLI
- Updates the docs and adds UML diagrams
- Multiple additional minor fixes and changes

## 0.1.13 (2019-11-08)

- Adds envelope serialiser
- Adds support for programmatically initializing an AEA
- Adds some tests for the GUI and other components
- Exposes connection status to skills
- Updates OEF connection to re-establish dropped connections
- Updates the car park agent
- Multiple additional minor fixes and changes

## 0.1.12 (2019-11-01)

- Adds TCP connection (server and client)
- Fixes some examples and docs
- Refactors crypto modules and adds additional tests
- Multiple additional minor fixes and changes

## 0.1.11 (2019-10-30)

- Adds Python 3.8 test coverage
- Adds almost complete test coverage on AEA package
- Adds filter concept for message routing
- Adds ledger integrations for Fetch.ai and Ethereum
- Adds car park examples and ledger examples
- Multiple additional minor fixes and changes

## 0.1.10 (2019-10-19)

- Compatibility fixes for Ubuntu and Windows platforms
- Multiple additional minor fixes and changes

## 0.1.9 (2019-10-18)

- Stability improvements
- Higher test coverage, including on Python 3.6
- Multiple additional minor fixes and changes

## 0.1.8 (2019-10-18)

- Multiple bug fixes and improvements to GUI of CLI
- Adds full test coverage on CLI
- Improves docs
- Multiple additional minor fixes and changes

## 0.1.7 (2019-10-14)

- Adds GUI to interact with CLI
- Adds new connection stub to read from/write to file
- Adds ledger entities (fetchai and Ethereum); creates wallet for ledger entities
- Adds more documentation and fixes old one
- Multiple additional minor fixes and changes

## 0.1.6 (2019-10-04)

- Adds several new skills
- Extended docs on framework and skills
- Introduces core framework components like decision maker and shared classes
- Multiple additional minor fixes and changes

## 0.1.5 (2019-09-26)

- Adds scaffolding command to the CLI tool
- Extended docs
- Increased test coverage
- Multiple additional minor fixes and changes


## 0.1.4 (2019-09-20)

- Adds CLI functionality to add connections
- Multiple additional minor fixes and changes

## 0.1.3 (2019-09-19)

- Adds Jenkins for CI
- Adds docker develop image
- Parses dependencies of connections/protocols/skills on the fly
- Adds validations of configuration files
- Adds first two working skills and fixes gym examples
- Adds docs
- Multiple additional minor fixes and changes

## 0.1.2 (2019-09-16)

- Adds AEA CLI tool.
- Adds AEA skills framework.
- Introduces static typing checks across AEA, using `Mypy`.
- Extends gym example

## 0.1.1 (2019-09-04)

- Provides examples and fixes.

## 0.1.0 (2019-08-21)

- Initial release of the package.
