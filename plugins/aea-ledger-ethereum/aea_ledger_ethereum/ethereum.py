# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2026 Valory AG
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Ethereum module wrapping the public and private key cryptography and ledger api."""

import concurrent.futures
import decimal
import json
import logging
import math
import threading
import warnings
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast
from uuid import uuid4

import requests
from aea_ledger_ethereum.rpc_rotation import RotatingHTTPProvider, parse_rpc_urls
from eth_account import Account
from eth_account._utils.legacy_transactions import (
    encode_transaction,
    serializable_unsigned_transaction_from_dict,
)
from eth_account._utils.signing import to_standard_signature_bytes
from eth_account.datastructures import HexBytes, SignedTransaction
from eth_account.messages import _hash_eip191_message, encode_defunct
from eth_account.signers.local import LocalAccount
from eth_keys import keys
from eth_typing import BlockNumber, HexStr
from eth_utils.currency import from_wei, to_wei  # pylint: disable=import-error
from requests import HTTPError
from requests.exceptions import ReadTimeout as RequestsReadTimeoutError
from toolz import curry  # type: ignore  # pylint: disable=import-error
from urllib3.exceptions import ReadTimeoutError as Urllib3ReadTimeoutError
from web3 import AsyncWeb3, Web3
from web3._utils.events import EventFilterBuilder
from web3._utils.http import DEFAULT_HTTP_TIMEOUT
from web3.contract.contract import ContractEvent
from web3.datastructures import AttributeDict
from web3.exceptions import ContractLogicError, TransactionNotFound, Web3ValueError
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import ExtraDataToPOAMiddleware, Web3Middleware
from web3.middleware.base import Web3MiddlewareBuilder
from web3.types import (
    MakeRequestFn,
    RPCEndpoint,
    RPCId,
    RPCResponse,
    TxData,
    TxParams,
    TxReceipt,
    Wei,
)
from web3.utils.caching import SimpleCache

from aea.common import Address, JSONLike
from aea.crypto.base import Crypto, FaucetApi, Helper, LedgerApi
from aea.crypto.helpers import DecryptError, KeyIsIncorrect, hex_to_bytes_for_key
from aea.exceptions import enforce
from aea.helpers.base import try_decorator
from aea.helpers.constants import NETWORK_REQUEST_DEFAULT_TIMEOUT
from aea.helpers.io import open_file

_default_logger = logging.getLogger("aea.ledger_apis.ethereum")

_ETHEREUM = "ethereum"
TESTNET_NAME = "ganache"
DEFAULT_ADDRESS = "http://127.0.0.1:8545"
DEFAULT_CHAIN_ID = 1337
DEFAULT_CURRENCY_DENOM = "wei"
GWEI = "gwei"
ETH_GASSTATION_URL = "https://ethgasstation.info/api/ethgasAPI.json"
_ABI = "abi"
_BYTECODE = "bytecode"
EIP1559 = "eip1559"
EIP1559_POLYGON = "eip1559_polygon"
GAS_STATION = "gas_station"
AVAILABLE_STRATEGIES = (EIP1559, GAS_STATION, EIP1559_POLYGON)
SPEED_FAST = "fast"  # safeLow, standard, fast
POLYGON_GAS_ENDPOINT = "https://gasstation.polygon.technology/v2"
MAX_GAS_FAST = 1500
RPC_CALL_MAX_WORKERS = 1

# How many blocks to consider for priority fee estimation
FEE_HISTORY_BLOCKS = 10

# Which percentile of effective priority fees to include
FEE_HISTORY_PERCENTILE = 5

# Returned if above trigger is not met (GWEI)
DEFAULT_PRIORITY_FEE = None

# In case something goes wrong fall back to this estimate
DEFAULT_FALLBACK_ESTIMATE = {
    "maxFeePerGas": to_wei(20, GWEI),
    "maxPriorityFeePerGas": to_wei(3, GWEI),
}

PRIORITY_FEE_INCREASE_BOUNDARY = 200  # percentage

DEFAULT_MIN_ALLOWED_TIP = 1
DEFAULT_GNOSIS_MIN_ALLOWED_TIP = to_wei(1, GWEI)

# Per-chain EIP-1559 strategy overrides applied by `get_default_gas_strategy`
# when the caller does not pass `gas_price_strategies` explicitly. Each entry
# is a patch on top of `DEFAULT_EIP1559_STRATEGY` (see below); keys present
# here replace the defaults, anything absent is inherited. A `fallback_estimate`
# override applies to both `eip1559` and `eip1559_polygon` strategies.
# Chains not listed here inherit the defaults entirely (including
# `DEFAULT_FALLBACK_ESTIMATE`).
CHAIN_EIP1559_OVERRIDES: Dict[int, Dict[str, Any]] = {
    # Gnosis: typical base fee <2 gwei; 1 gwei validator floor on priority fee.
    # ``max_gas_fast`` set ~4x above legitimate congestion bursts (~5-8 gwei
    # during Tornado-deposit waves) but well below the range observed during
    # production RPC anomalies that burned ~45% of an agent's xDAI budget on
    # a single 694 gwei tx (gnosisscan.io tx 0x727262d9...). Anything above
    # this ceiling triggers the ``fallback_estimate`` (5/1 gwei) instead.
    100: {
        "max_gas_fast": 30,
        "min_allowed_tip": DEFAULT_GNOSIS_MIN_ALLOWED_TIP,
        "fallback_estimate": {
            "maxFeePerGas": to_wei(5, GWEI),
            "maxPriorityFeePerGas": to_wei(1, GWEI),
        },
    },
    # OP-stack L2s (Optimism / Base / Mode / Fraxtal): sub-gwei typical; no
    # enforced tip floor, so default ``min_allowed_tip`` (1 wei) is fine.
    # ``max_gas_fast`` sized to preserve operability during legitimate
    # congestion events (Base sustained ~24 gwei averages with >100 gwei
    # bursts during the March 2024 Dencun memecoin frenzy; Optimism had
    # similar Worldcoin-era spikes) while still capping fee-oracle anomalies
    # at orders of magnitude below the chain-agnostic 1500 gwei default.
    10: {  # Optimism
        "max_gas_fast": 100,
        "fallback_estimate": {
            "maxFeePerGas": to_wei(5, GWEI),
            "maxPriorityFeePerGas": to_wei(3, GWEI),
        },
    },
    8453: {  # Base
        "max_gas_fast": 100,
        "fallback_estimate": {
            "maxFeePerGas": to_wei(5, GWEI),
            "maxPriorityFeePerGas": to_wei(3, GWEI),
        },
    },
    34443: {  # Mode
        "max_gas_fast": 50,
        "fallback_estimate": {
            "maxFeePerGas": to_wei(5, GWEI),
            "maxPriorityFeePerGas": to_wei(3, GWEI),
        },
    },
    252: {  # Fraxtal (OP-stack)
        "max_gas_fast": 50,
        "fallback_estimate": {
            "maxFeePerGas": to_wei(5, GWEI),
            "maxPriorityFeePerGas": to_wei(3, GWEI),
        },
    },
    # Arbitrum One: 0.02 gwei floor (Nov 2025 AIP raised from 0.01), ~0.02
    # gwei typical; no enforced tip floor either. 5 gwei is ~250x the floor
    # and well above any observed daily-average congestion.
    42161: {
        "max_gas_fast": 5,
        "fallback_estimate": {
            "maxFeePerGas": to_wei(2, GWEI),
            "maxPriorityFeePerGas": to_wei(1, GWEI),
        },
    },
    # Polygon PoS: validator-enforced ~30 gwei min priority fee — `min_allowed_tip`
    # set so the estimator proposes at least 30 gwei when recent blocks have no
    # tips. `max_gas_fast` raised because Polygon bursts routinely exceed the
    # default. `fallback_estimate` maxFee has headroom for congestion bursts.
    137: {
        "max_gas_fast": 10000,
        "min_allowed_tip": to_wei(30, GWEI),
        "fallback_estimate": {
            "maxFeePerGas": to_wei(6000, GWEI),
            "maxPriorityFeePerGas": to_wei(30, GWEI),
        },
    },
    # Celo: governance raised min gas price to 25 gwei in 2025 — `min_allowed_tip`
    # and `fallback_estimate` tip both set at/above the network floor.
    42220: {
        "min_allowed_tip": to_wei(25, GWEI),
        "fallback_estimate": {
            "maxFeePerGas": to_wei(50, GWEI),
            "maxPriorityFeePerGas": to_wei(25, GWEI),
        },
    },
}

DEFAULT_EIP1559_STRATEGY = {
    "max_gas_fast": MAX_GAS_FAST,
    "fee_history_blocks": FEE_HISTORY_BLOCKS,
    "fee_history_percentile": FEE_HISTORY_PERCENTILE,
    "default_priority_fee": DEFAULT_PRIORITY_FEE,
    "fallback_estimate": DEFAULT_FALLBACK_ESTIMATE,
    "min_allowed_tip": DEFAULT_MIN_ALLOWED_TIP,
    "priority_fee_increase_boundary": PRIORITY_FEE_INCREASE_BOUNDARY,
}

DEFAULT_EIP1559_STRATEGY_POLYGON = {
    "gas_endpoint": POLYGON_GAS_ENDPOINT,
    "speed": SPEED_FAST,
    "fallback_estimate": DEFAULT_FALLBACK_ESTIMATE,
}

DEFAULT_GAS_STATION_STRATEGY = {"gas_price_api_key": "", "gas_price_strategy": "fast"}

GAS_STATION_FALLBACK_ESTIMATE = 20  # gwei

DEFAULT_GAS_PRICE_STRATEGIES: Dict[str, Dict[str, Any]] = {
    EIP1559: DEFAULT_EIP1559_STRATEGY,
    GAS_STATION: DEFAULT_GAS_STATION_STRATEGY,
    EIP1559_POLYGON: DEFAULT_EIP1559_STRATEGY_POLYGON,
}

BASE_FEE_MULTIPLIER = defaultdict(lambda: 1.2, {40: 2.0, 100: 1.6, 200: 1.4})

GAS_PRICE_ORACLE_ADDRESS = "0x420000000000000000000000000000000000000F"
GET_L1_FEE_ABI = [
    {
        "inputs": [{"internalType": "bytes", "name": "_data", "type": "bytes"}],
        "name": "getL1Fee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
]
MAX_OP_L1_FEE_INCREASE_RELATIVE_PER_BLOCK = 1.125

# OP-stack chain IDs: Optimism, Base, Mode, Fraxtal.
_OP_STACK_CHAIN_IDS = frozenset({10, 8453, 34443, 252})

# Arbitrum Nitro chain IDs: Arbitrum One, Arbitrum Nova.
_ARBITRUM_CHAIN_IDS = frozenset({42161, 42170})
ARBITRUM_NODE_INTERFACE_ADDRESS = "0x00000000000000000000000000000000000000C8"
ARBITRUM_GAS_ESTIMATE_L1_COMPONENT_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "bool", "name": "contractCreation", "type": "bool"},
            {"internalType": "bytes", "name": "data", "type": "bytes"},
        ],
        "name": "gasEstimateL1Component",
        "outputs": [
            {"internalType": "uint64", "name": "gasEstimateForL1", "type": "uint64"},
            {"internalType": "uint256", "name": "baseFee", "type": "uint256"},
            {
                "internalType": "uint256",
                "name": "l1BaseFeeEstimate",
                "type": "uint256",
            },
        ],
        "stateMutability": "payable",
        "type": "function",
    }
]
# Arbitrum docs recommend padding by 10% when using the returned estimate
# to build a live tx (NodeInterface.sol, gasEstimateL1Component docstring).
ARBITRUM_L1_FEE_PADDING = 1.1

# The tip increase is the minimum required of 10%.
TIP_INCREASE = 1.1

# the `web3` methods' names for logs filtering operations
MATCH_SINGLE = "match_single"
MATCH_ANY = "match_any"

REQUESTS_TIMEOUT_KEY = "timeout"

ETH_CHAIN_ID = "eth_chainId"
JSON_RPC_VERSION = "2.0"


def to_eth_unit(
    number: Union[int, float, str, decimal.Decimal],
    unit_in: str = DEFAULT_CURRENCY_DENOM,
    unit_out: str = GWEI,
) -> Union[int, Wei, decimal.Decimal]:
    """Covert a number to the given unit."""
    if not (isinstance(number, int) and unit_in == DEFAULT_CURRENCY_DENOM):
        number = to_wei(number, unit_in)

    if unit_out == DEFAULT_CURRENCY_DENOM:
        return number

    return from_wei(number, unit_out)


def get_base_fee_multiplier(base_fee_gwei: Union[int, decimal.Decimal]) -> float:
    """Returns multiplier value."""
    valid_fees = {fee for fee in BASE_FEE_MULTIPLIER if base_fee_gwei <= fee}
    # add negative fee in case the valid fees set is empty, to trigger the default value
    if not valid_fees:
        valid_fees.add(-1)
    return BASE_FEE_MULTIPLIER[min(valid_fees)]


def get_default_gas_strategy(chain_id: int) -> Dict[str, Any]:
    """Get default gas strategy for the given chain ID."""
    default_strategy = deepcopy(DEFAULT_GAS_PRICE_STRATEGIES)
    overrides = CHAIN_EIP1559_OVERRIDES.get(chain_id, {})
    if "fallback_estimate" in overrides:
        # apply to every strategy that carries a `fallback_estimate` (covers
        # both `eip1559` and `eip1559_polygon`)
        for strategy in default_strategy.values():
            if "fallback_estimate" in strategy:
                strategy["fallback_estimate"] = deepcopy(overrides["fallback_estimate"])
    for key in ("min_allowed_tip", "max_gas_fast"):
        if key in overrides:
            default_strategy[EIP1559][key] = overrides[key]

    return default_strategy


def estimate_priority_fee(  # pylint: disable=too-many-positional-arguments
    web3_object: Web3,
    block_number: int,
    default_priority_fee: Optional[int],
    fee_history_blocks: int,
    fee_history_percentile: int,
    min_allowed_tip: int,
    priority_fee_increase_boundary: int,
) -> int:
    """Estimate priority fee from base fee."""

    if default_priority_fee is not None:
        return default_priority_fee

    fee_history = web3_object.eth.fee_history(
        fee_history_blocks, block_number, [fee_history_percentile]  # type: ignore
    )

    # This is going to break if more percentiles are introduced in the future,
    # i.e., `fee_history_percentile` param becomes a `List[int]`.
    rewards = sorted(
        [
            reward[0]
            for reward in fee_history.get("reward", [])
            if reward[0] >= min_allowed_tip
        ]
    )
    if len(rewards) == 0:
        _default_logger.warning(
            f"Network activity has been very low for the past {fee_history_blocks} blocks "
            f"(current block: {block_number}). Tipping with {min_allowed_tip=}."
        )
        return min_allowed_tip

    if len(rewards) == 1:
        return rewards[0]

    # Calculate percentage increases from between ordered list of fees
    percentage_increases = [
        ((j - i) / i) * 100 if i != 0 else 0 for i, j in zip(rewards[:-1], rewards[1:])
    ]
    highest_increase = max(percentage_increases)
    highest_increase_index = percentage_increases.index(highest_increase)

    values = rewards.copy()
    # If we have big increase in value, we could be considering "outliers" in our estimate
    # Skip the low elements and take a new median
    if (
        highest_increase > priority_fee_increase_boundary
        and highest_increase_index >= len(values) // 2
    ):
        values = values[highest_increase_index:]

    return values[len(values) // 2]


def get_gas_price_strategy_eip1559(  # pylint: disable=too-many-positional-arguments
    max_gas_fast: int,
    fee_history_blocks: int,
    fee_history_percentile: int,
    default_priority_fee: Optional[int],
    fallback_estimate: Dict[str, Wei],
    min_allowed_tip: int,
    priority_fee_increase_boundary: int,
) -> Callable[[Web3, TxParams], Dict[str, Wei]]:
    """Get the gas price strategy."""

    def fallback(
        reason: str = "An error occurred while estimating gas price.",
    ) -> Dict[str, Wei]:
        """Return the fallback estimate and log a warning naming the values and override knob."""
        _default_logger.warning(
            f"{reason} Falling back to "
            f"maxFeePerGas={fallback_estimate.get('maxFeePerGas')} wei, "
            f"maxPriorityFeePerGas={fallback_estimate.get('maxPriorityFeePerGas')} wei. "
            "To override, pass `gas_price_strategies` (with an `eip1559.fallback_estimate` "
            "block tuned for the target chain) to `make_ledger_api`."
        )
        # return a copy; callers may mutate the returned dict (e.g. repricing in
        # try_get_gas_pricing)
        return dict(fallback_estimate)

    def eip1559_price_strategy(
        web3: Web3,  # pylint: disable=redefined-outer-name
        transaction_params: TxParams,  # pylint: disable=unused-argument
    ) -> Dict[str, Wei]:
        """
        Get gas price using EIP1559.

        Visit `https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md`
        for more information.

        :param web3: web3 instance
        :param transaction_params: transaction parameters
        :return: dictionary containing gas price strategy
        """

        latest_block = web3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas")
        block_number = latest_block.get("number")

        if base_fee is None or block_number is None:
            return fallback()

        base_fee_gwei = to_eth_unit(base_fee)

        estimated_priority_fee = estimate_priority_fee(
            web3,
            block_number,
            default_priority_fee=default_priority_fee,
            fee_history_blocks=fee_history_blocks,
            fee_history_percentile=fee_history_percentile,
            min_allowed_tip=min_allowed_tip,
            priority_fee_increase_boundary=priority_fee_increase_boundary,
        )

        multiplier = get_base_fee_multiplier(base_fee_gwei)
        potential_max_fee = base_fee * multiplier
        max_fee_per_gas = (
            (potential_max_fee + estimated_priority_fee)
            if estimated_priority_fee > potential_max_fee
            else potential_max_fee
        )

        if (
            to_eth_unit(max_fee_per_gas) >= max_gas_fast
            or to_eth_unit(estimated_priority_fee) >= max_gas_fast
        ):
            return fallback(
                "The estimated gas price is larger than the `max_gas_fast`."
            )

        estimate = {
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": estimated_priority_fee,
        }
        return {
            fee: to_eth_unit(amount, unit_out=DEFAULT_CURRENCY_DENOM)
            for fee, amount in estimate.items()
        }

    return eip1559_price_strategy


def get_gas_price_strategy_eip1559_polygon(
    gas_endpoint: str,
    fallback_estimate: Dict[str, Wei],
    speed: Optional[str] = SPEED_FAST,
) -> Callable[[Any, Any], Dict[str, Wei]]:
    """Get the gas price strategy."""

    def eip1559_price_strategy(
        web3: Web3,  # pylint: disable=redefined-outer-name,unused-argument
        transaction_params: TxParams,  # pylint: disable=unused-argument
    ) -> Dict[str, Wei]:
        try:
            response = requests.get(
                gas_endpoint, timeout=NETWORK_REQUEST_DEFAULT_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()[speed]
                return {
                    "maxFeePerGas": Wei(to_wei(data["maxFee"], GWEI)),
                    "maxPriorityFeePerGas": Wei(to_wei(data["maxPriorityFee"], GWEI)),
                }
            # return a copy; see note in get_gas_price_strategy_eip1559.fallback
            return dict(fallback_estimate)
        except requests.exceptions.RequestException:
            return dict(fallback_estimate)

    return eip1559_price_strategy


def rpc_gas_price_strategy_wrapper(
    web3: Web3, transaction_params: TxParams  # pylint: disable=redefined-outer-name
) -> Dict[str, Wei]:
    """RPC gas price strategy wrapper."""
    return {"gasPrice": rpc_gas_price_strategy(web3, transaction_params)}


def get_gas_price_strategy(
    gas_price_strategy: Optional[str] = None, gas_price_api_key: Optional[str] = None
) -> Callable[[Web3, TxParams], Dict[str, Wei]]:
    """Get the gas price strategy."""
    supported_gas_price_modes = ["safeLow", "average", "fast", "fastest"]

    if gas_price_strategy is None:
        _default_logger.debug(
            "Gas price strategy not provided. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy_wrapper

    if gas_price_strategy not in supported_gas_price_modes:
        _default_logger.debug(
            f"Gas price strategy `{gas_price_strategy}` not in list of supported modes: {supported_gas_price_modes}. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy_wrapper

    if gas_price_api_key is None:
        _default_logger.debug(
            "No ethgasstation api key provided. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy_wrapper

    def gas_station_gas_price_strategy(
        web3: Web3,  # pylint: disable=redefined-outer-name
        transaction_params: TxParams,  # pylint: disable=unused-argument
    ) -> Dict[str, Wei]:
        """
        Get gas price from Eth Gas Station api.

        Visit `https://docs.ethgasstation.info/gas-price` for documentation.
        :param web3: web3 instance
        :param transaction_params: transaction parameters
        :return: wei
        """
        _default_logger.info(  # pragma: nocover
            "`ethgasstation.info` has been deprecated and will be replaced with an alternative on the next release."
        )
        response = requests.get(
            f"{ETH_GASSTATION_URL}?api-key={gas_price_api_key}",
            timeout=NETWORK_REQUEST_DEFAULT_TIMEOUT,
        )
        if response.status_code != 200:  # pragma: nocover
            # TODO : Use some other gas station API # pylint: disable=fixme
            _default_logger.error(
                f"Gas station API response: {response.status_code}, {response.text}, using fallback gas price."
            )
            return {"gasPrice": web3.to_wei(GAS_STATION_FALLBACK_ESTIMATE, GWEI)}
        response_dict = response.json()
        _default_logger.debug("Gas station API response: {}".format(response_dict))
        result = response_dict.get(gas_price_strategy, None)
        if type(result) not in [int, float]:  # pragma: nocover
            raise ValueError(f"Invalid return value for `{gas_price_strategy}`!")
        gwei_result = result / 10  # adjustment (see api documentation)
        wei_result = web3.to_wei(gwei_result, GWEI)
        return {"gasPrice": wei_result}

    return gas_station_gas_price_strategy


def rpc_call_with_timeout(func: Callable, timeout: int) -> Any:
    """Execute an RPC call with a timeout."""

    with concurrent.futures.ThreadPoolExecutor(RPC_CALL_MAX_WORKERS) as executor:
        # submit the function with the RPC call to the executor
        future = executor.submit(func)

        try:
            # wait for the result with a timeout
            data = future.result(timeout=timeout)
        except TimeoutError:
            # handle the case where the execution times out
            err = f"The RPC didn't respond within {timeout} seconds."
            return None, err

        # check if an error occurred
        if isinstance(data, str):
            # handle the case where the execution fails
            return None, data

        return data, None


def match_items(
    filter_: EventFilterBuilder,
    event_name: str,
    method_to_matches: Dict[str, Dict[str, Any]],
):
    """Build filters for the given match dictionary."""
    for method, matches in method_to_matches.items():
        for arg, value in matches.items():
            arg_filter = filter_.args.get(arg, None)
            if arg_filter is None:
                raise ValueError(
                    f"There is no argument {arg!r} in the event {event_name}!"
                )
            filtering_method = getattr(arg_filter, method, None)
            if filtering_method is None:
                raise ValueError(
                    f"There is no filtering method named {filtering_method}!"
                )
            filtering_method(value)


class SignedTransactionTranslator:
    """Translator for SignedTransaction."""

    @staticmethod
    def to_dict(signed_transaction: SignedTransaction) -> Dict[str, Union[str, int]]:
        """Write SignedTransaction to dict."""
        signed_transaction_dict: Dict[str, Union[str, int]] = {
            "raw_transaction": cast(
                str, signed_transaction.raw_transaction.to_0x_hex()
            ),
            "hash": cast(str, signed_transaction.hash.to_0x_hex()),
            "r": cast(int, signed_transaction.r),
            "s": cast(int, signed_transaction.s),
            "v": cast(int, signed_transaction.v),
        }
        return signed_transaction_dict

    @staticmethod
    def from_dict(signed_transaction_dict: JSONLike) -> SignedTransaction:
        """Get SignedTransaction from dict."""
        if (
            not isinstance(signed_transaction_dict, dict)
            and len(signed_transaction_dict) == 5
        ):
            raise ValueError(  # pragma: nocover
                f"Invalid for conversion. Found object: {signed_transaction_dict}."
            )
        signed_transaction = SignedTransaction(
            raw_transaction=HexBytes(
                cast(str, signed_transaction_dict["raw_transaction"])
            ),
            hash=HexBytes(cast(str, signed_transaction_dict["hash"])),
            r=cast(int, signed_transaction_dict["r"]),
            s=cast(int, signed_transaction_dict["s"]),
            v=cast(int, signed_transaction_dict["v"]),
        )
        return signed_transaction


class AttributeDictTranslator:
    """Translator for AttributeDict."""

    @classmethod
    def _remove_hexbytes(cls, value: Any) -> Any:
        """Process value to remove hexbytes."""
        if value is None:
            return value
        if isinstance(value, HexBytes):
            return value.to_0x_hex()
        if isinstance(value, list):
            return cls._process_list(value, cls._remove_hexbytes)
        if type(value) in (bool, int, float, str, bytes):
            return value
        if isinstance(value, (AttributeDict, dict)):
            return cls.to_dict(value)
        raise NotImplementedError(  # pragma: nocover
            f"Unknown type conversion. Found type: {type(value)}"
        )

    @classmethod
    def _add_hexbytes(cls, value: Any) -> Any:
        """Process value to add hexbytes."""
        if value is None:
            return value
        if isinstance(value, str):
            try:
                int(value, 16)
                return HexBytes(value)
            except Exception:  # pylint: disable=broad-except
                return value
        if isinstance(value, list):
            return cls._process_list(value, cls._add_hexbytes)
        if isinstance(value, dict):
            return cls.from_dict(value)
        if type(value) in (bool, int, float, bytes):
            return value
        raise NotImplementedError(  # pragma: nocover
            f"Unknown type conversion. Found type: {type(value)}"
        )

    @classmethod
    def _process_list(cls, li: list, callable_name: Callable) -> List:
        """Simplify a list with process value."""
        return [callable_name(el) for el in li]

    @classmethod
    def _valid_key(cls, key: Any) -> str:
        """Check validity of key."""
        if isinstance(key, str):
            return key
        raise ValueError("Key must be string.")  # pragma: nocover

    @classmethod
    def to_dict(
        cls, attr_dict: Union[AttributeDict, TxReceipt, TxData, Dict[str, Any]]
    ) -> JSONLike:
        """Simplify to dict."""
        # TxReceipt / TxData are TypedDicts (dict subclasses), so accept both
        # AttributeDict and plain dict.
        if not isinstance(attr_dict, (AttributeDict, dict)):
            raise ValueError(  # pragma: nocover
                f"Expected AttributeDict or dict-like, "
                f"got {type(attr_dict).__name__}"
            )
        result = {
            cls._valid_key(key): cls._remove_hexbytes(value)
            for key, value in attr_dict.items()
        }
        return result

    @classmethod
    def from_dict(cls, di: JSONLike) -> AttributeDict:
        """Get back attribute dict."""
        if not isinstance(di, dict):
            raise ValueError("No dict provided.")  # pragma: nocover
        processed_dict = {
            cls._valid_key(key): cls._add_hexbytes(value) for key, value in di.items()
        }
        return AttributeDict(processed_dict)


class EthereumCrypto(Crypto[LocalAccount]):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _ETHEREUM

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        password: Optional[str] = None,
        extra_entropy: Union[str, bytes, int] = "",
    ) -> None:
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        :param password: the password to encrypt/decrypt the private key.
        :param extra_entropy: add extra randomness to whatever randomness your OS can provide
        """
        super().__init__(
            private_key_path=private_key_path,
            password=password,
            extra_entropy=extra_entropy,
        )

        bytes_representation = Web3.to_bytes(hexstr=self.entity.key.to_0x_hex())
        self._public_key = str(keys.PrivateKey(bytes_representation).public_key)
        self._address = self.entity.address

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        64 random hex characters (i.e. 32 bytes) + "0x" prefix.

        :return: a private key string in hex format
        """
        return self.entity.key.to_0x_hex()

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        128 hex characters (i.e. 64 bytes) + "0x" prefix.

        :return: a public key string in hex format
        """
        return self._public_key

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        40 hex characters (i.e. 20 bytes) + "0x" prefix.

        :return: an address string in hex format
        """
        return self._address

    @classmethod
    def load_private_key_from_path(
        cls, file_name: str, password: Optional[str] = None
    ) -> LocalAccount:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.
        :param password: the password to encrypt/decrypt the private key.
        :return: the Entity.
        """
        private_key = cls.load(file_name, password)
        try:
            if not private_key.startswith("0x"):
                hex_to_bytes_for_key(private_key)
        except KeyIsIncorrect as e:
            if not password:
                raise KeyIsIncorrect(
                    f"Error on key `{file_name}` load! Try to specify `password`: Error: {repr(e)} "
                ) from e
            raise KeyIsIncorrect(
                f"Error on key `{file_name}` load! Wrong password?: Error: {repr(e)} "
            ) from e

        account = Account.from_key(  # pylint: disable=no-value-for-parameter
            private_key=private_key
        )
        return account

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message to be signed
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """
        if is_deprecated_mode and len(message) == 32:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                signature_dict = self.entity.unsafe_sign_hash(message)
            signed_msg = signature_dict["signature"].to_0x_hex()
        else:
            signable_message = encode_defunct(primitive=message)
            signature = self.entity.sign_message(signable_message=signable_message)
            signed_msg = signature["signature"].to_0x_hex()
        return signed_msg

    def sign_transaction(self, transaction: JSONLike) -> JSONLike:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :return: signed transaction
        """
        signed_transaction = cast(Account, self.entity).sign_transaction(
            transaction_dict=transaction
        )
        signed_transaction_dict = SignedTransactionTranslator.to_dict(
            signed_transaction
        )
        return cast(JSONLike, signed_transaction_dict)

    @classmethod
    def generate_private_key(
        cls, extra_entropy: Union[str, bytes, int] = ""
    ) -> LocalAccount:
        """
        Generate a key pair for ethereum network.

        :param extra_entropy: add extra randomness to whatever randomness your OS can provide
        :return: account object
        """
        account = Account.create(
            extra_entropy
        )  # pylint: disable=no-value-for-parameter
        return account

    def encrypt(self, password: str) -> str:
        """
        Encrypt the private key and return in json.

        :param password: the password to decrypt.
        :return: json string containing encrypted private key.
        """
        encrypted = Account.encrypt(self.private_key, password)
        return json.dumps(encrypted)

    @classmethod
    def decrypt(cls, keyfile_json: str, password: str) -> str:
        """
        Decrypt the private key and return in raw form.

        :param keyfile_json: json str containing encrypted private key.
        :param password: the password to decrypt.
        :return: the raw private key (without leading "0x").
        """
        try:
            private_key = Account.decrypt(keyfile_json, password)
        except ValueError as e:
            if e.args[0] == "MAC mismatch":
                raise DecryptError() from e
            raise
        return private_key.hex()


class EthereumHelper(Helper):
    """Helper class usable as Mixin for EthereumApi or as standalone class."""

    @staticmethod
    def is_transaction_settled(tx_receipt: JSONLike) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_receipt: the receipt associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            is_successful = tx_receipt.get("status", 0) == 1
        return is_successful

    @staticmethod
    def get_contract_address(tx_receipt: JSONLike) -> Optional[str]:
        """
        Retrieve the `contract_address` from a transaction receipt.

        :param tx_receipt: the receipt of the transaction.
        :return: the contract address, if present
        """
        contract_address = cast(Optional[str], tx_receipt.get("contractAddress", None))
        return contract_address

    @staticmethod
    def is_transaction_valid(
        tx: dict,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :return: True if the random_message is equals to tx['input']
        """
        is_valid = False
        if tx is not None:
            is_valid = (
                tx.get("input") == tx_nonce
                and tx.get("value") == amount
                and tx.get("from") == client
                and tx.get("to") == seller
            )
        return is_valid

    @staticmethod
    def generate_tx_nonce(seller: Address, client: Address) -> str:
        """
        Generate a unique hash to distinguish transactions with the same terms.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        aggregate_hash = Web3.keccak(
            b"".join([seller.encode(), client.encode(), uuid4().bytes])
        )
        return aggregate_hash.to_0x_hex()

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> str:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        keccak_hash = Web3.keccak(hexstr=public_key)
        raw_address = keccak_hash[-20:].to_0x_hex()
        address = Web3.to_checksum_address(raw_address)
        return address

    @classmethod
    def recover_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[Address, ...]:
        """
        Recover the addresses from the hash.

        :param message: the message we expect
        :param signature: the transaction signature
        :param is_deprecated_mode: if the deprecated signing was used
        :return: the recovered addresses
        """
        if is_deprecated_mode:
            enforce(len(message) == 32, "Message must be hashed to exactly 32 bytes.")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                address = Account._recover_hash(  # pylint: disable=no-value-for-parameter,protected-access
                    message_hash=message, signature=signature
                )
        else:
            signable_message = encode_defunct(primitive=message)
            address = Account.recover_message(  # pylint: disable=no-value-for-parameter
                signable_message=signable_message, signature=signature
            )
        return (address,)

    @classmethod
    def recover_public_keys_from_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[str, ...]:
        """
        Get the public key used to produce the `signature` of the `message`

        :param message: raw bytes used to produce signature
        :param signature: signature of the message
        :param is_deprecated_mode: if the deprecated signing was used
        :return: the recovered public keys
        """
        if not is_deprecated_mode:
            signable_message = encode_defunct(primitive=message)
            message = _hash_eip191_message(signable_message)
        hash_bytes = HexBytes(message)
        # code taken from https://github.com/ethereum/eth-account/blob/master/eth_account/account.py#L428
        if len(hash_bytes) != 32:  # pragma: nocover
            raise ValueError("The message hash must be exactly 32-bytes")
        signature_bytes = HexBytes(signature)
        signature_bytes_standard = to_standard_signature_bytes(signature_bytes)
        signature_obj = keys.Signature(signature_bytes=signature_bytes_standard)
        pubkey = signature_obj.recover_public_key_from_msg_hash(hash_bytes)
        return (str(pubkey),)

    @staticmethod
    def get_hash(message: bytes) -> str:
        """
        Get the hash of a message.

        :param message: the message to be hashed.
        :return: the hash of the message as a hex string.
        """
        digest = Web3.keccak(message).to_0x_hex()
        return digest

    @classmethod
    def load_contract_interface(cls, file_path: Path) -> Dict[str, str]:
        """
        Load contract interface.

        :param file_path: the file path to the interface
        :return: the interface
        """
        with open_file(file_path, "r") as interface_file_ethereum:
            contract_interface = json.load(interface_file_ethereum)
        for key in [_ABI, _BYTECODE]:
            if key not in contract_interface:  # pragma: nocover
                raise ValueError(f"Contract {file_path} missing key {key}.")
        return contract_interface


def rpc_response(result: Any, request_id: RPCId = 1) -> RPCResponse:
    """Construct an RPC response."""
    return {
        "jsonrpc": JSON_RPC_VERSION,
        "id": request_id,
        "result": result,
    }


class CachedChainIdMiddleware(Web3MiddlewareBuilder):
    """A custom web3 middleware to cache the chain id, avoiding unnecessary RPC costs by repeated eth_chainId calls."""

    chain_id: int

    @staticmethod
    @curry
    def build(w3: Union[AsyncWeb3, Web3], **kwargs: Any) -> Web3Middleware:
        """Build the middleware."""
        chain_id = kwargs.get("chain_id")
        if not isinstance(chain_id, int) or chain_id < 1:
            raise Web3ValueError(
                f"You must set a valid chain id for the {CachedChainIdMiddleware.__name__} middleware."
            )
        middleware = CachedChainIdMiddleware(w3)
        middleware.chain_id = chain_id
        return middleware

    def wrap_make_request(self, make_request: MakeRequestFn) -> MakeRequestFn:
        """Wrap the make_request."""

        def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
            """Middleware function to override the request with."""
            if method == ETH_CHAIN_ID:
                return rpc_response(self.chain_id)
            return make_request(method, params)

        return middleware


class EthereumApi(LedgerApi, EthereumHelper):
    """Class to interact with the Ethereum Web3 APIs."""

    identifier = _ETHEREUM

    _gas_price_strategy_callables: Dict[str, Callable] = {
        GAS_STATION: get_gas_price_strategy,
        EIP1559: get_gas_price_strategy_eip1559,
        EIP1559_POLYGON: get_gas_price_strategy_eip1559_polygon,
    }

    def __init__(self, **kwargs: Any):
        """
        Initialize the Ethereum ledger APIs.

        :param kwargs: keyword arguments
        """
        address = kwargs.pop("address", DEFAULT_ADDRESS)
        rpc_urls = parse_rpc_urls(address)
        self._chain_id = kwargs.pop("chain_id", DEFAULT_CHAIN_ID)
        request_kwargs = {
            REQUESTS_TIMEOUT_KEY: kwargs.pop(REQUESTS_TIMEOUT_KEY, DEFAULT_HTTP_TIMEOUT)
        }
        # RotatingHTTPProvider handles failover and retry across endpoints at
        # the transport layer.  Because rotation lives inside the provider
        # rather than as a middleware, the standard web3 middleware chain runs
        # untouched on every call — defaults plus any user-injected middleware.
        self._rpc_rotation = RotatingHTTPProvider(
            rpc_urls=rpc_urls,
            request_kwargs=request_kwargs,
            chain_id=self._chain_id,
        )
        self._api = Web3(self._rpc_rotation)
        # cache the chain id and use it for all the `eth_chainId` calls to avoid excess RPC usage
        cached_chain_id = (
            CachedChainIdMiddleware.build(  # pylint: disable=no-value-for-parameter
                chain_id=self._chain_id
            )
        )
        self._api.middleware_onion.add(cached_chain_id)

        self._is_gas_estimation_enabled = kwargs.pop("is_gas_estimation_enabled", False)

        self._default_gas_price_strategy: str = kwargs.pop(
            "default_gas_price_strategy", EIP1559
        )
        if self._default_gas_price_strategy not in AVAILABLE_STRATEGIES:
            raise ValueError(
                f"Gas price strategy must be one of {AVAILABLE_STRATEGIES}, provided: {self._default_gas_price_strategy}"
            )  # pragma: nocover

        self._gas_price_strategies: Dict[str, Dict] = kwargs.pop(
            "gas_price_strategies", get_default_gas_strategy(self._chain_id)
        )

        self._poa_chain = kwargs.pop("poa_chain", False)
        if self._poa_chain:
            # https://web3py.readthedocs.io/en/stable/middleware.html#geth-style-proof-of-authority
            self._api.middleware_onion.inject(
                ExtraDataToPOAMiddleware, name="ExtraDataToPOAMiddleware", layer=0
            )
            _default_logger.info(
                "EthereumApi has been configured with Proof of Authority chain support"
            )

    @property
    def api(self) -> Web3:
        """Get the underlying API object."""
        return self._api

    def get_balance(
        self, address: Address, raise_on_try: bool = False
    ) -> Optional[int]:
        """Get the balance of a given account."""
        return self._try_get_balance(address, raise_on_try=raise_on_try)

    @try_decorator("Unable to retrieve balance: {}", logger_method="warning")
    def _try_get_balance(self, address: Address, **_kwargs: Any) -> Optional[int]:
        """Get the balance of a given account."""
        check_address = self._api.to_checksum_address(address)
        return self._api.eth.get_balance(check_address)  # pylint: disable=no-member

    def get_state(
        self, callable_name: str, *args: Any, raise_on_try: bool = False, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Call a specified function on the ledger API."""
        response = self._try_get_state(
            callable_name, *args, raise_on_try=raise_on_try, **kwargs
        )
        return response

    @try_decorator("Unable to get state: {}", logger_method="warning")
    def _try_get_state(  # pylint: disable=unused-argument
        self, callable_name: str, *args: Any, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Try to call a function on the ledger API."""

        if "raise_on_try" in kwargs:
            logging.info(
                f"popping `raise_on_try` from {self.__class__.__name__}.get_state kwargs"
            )
            kwargs.pop("raise_on_try")

        response = getattr(self._api.eth, callable_name)(*args, **kwargs)

        if isinstance(response, AttributeDict):
            result = AttributeDictTranslator.to_dict(response)
            return result

        if type(response) in (int, float, bytes, str, list, dict):  # pragma: nocover
            # missing full checks for nested objects
            return {f"{callable_name}_result": response}
        raise NotImplementedError(  # pragma: nocover
            f"Response must be of types=int, float, bytes, str, list, dict. Found={type(response)}."
        )

    def get_transfer_transaction(  # pylint: disable=too-many-positional-arguments
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        chain_id: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[str] = None,
        gas_price: Optional[str] = None,
        gas_price_strategy: Optional[str] = None,
        gas_price_strategy_extra_config: Optional[Dict] = None,
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred (in Wei).
        :param tx_fee: the transaction fee (gas) to be used (in Wei).
        :param tx_nonce: verifies the authenticity of the tx.
        :param chain_id: the Chain ID of the Ethereum transaction.
        :param max_fee_per_gas: maximum amount you're willing to pay, inclusive of `baseFeePerGas` and `maxPriorityFeePerGas`. The difference between `maxFeePerGas` and `baseFeePerGas + maxPriorityFeePerGas` is refunded  (in Wei).
        :param max_priority_fee_per_gas: the part of the fee that goes to the miner (in Wei).
        :param gas_price: the gas price (in Wei)
        :param gas_price_strategy: the gas price strategy to be used.
        :param gas_price_strategy_extra_config: extra config for gas price strategy.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: keyword arguments
        :return: the transfer transaction
        """
        transaction: Optional[JSONLike] = None
        chain_id = chain_id if chain_id is not None else self._chain_id
        destination_address = self._api.to_checksum_address(destination_address)
        sender_address = self._api.to_checksum_address(sender_address)
        nonce = self._try_get_transaction_count(
            sender_address,
            raise_on_try=raise_on_try,
        )
        if nonce is None:
            return transaction
        transaction = {
            "from": sender_address,
            "nonce": nonce,
            "chainId": chain_id,
            "to": destination_address,
            "value": amount,
            "gas": tx_fee,
            "data": tx_nonce,
        }
        if self._is_gas_estimation_enabled:
            transaction = self.update_with_gas_estimate(transaction)

        if max_fee_per_gas is not None:
            max_priority_fee_per_gas = (
                self._try_get_max_priority_fee(raise_on_try=raise_on_try)
                if max_priority_fee_per_gas is None
                else max_priority_fee_per_gas
            )
            transaction.update(
                {
                    "maxFeePerGas": max_fee_per_gas,
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                }
            )

        if gas_price is not None:
            transaction.update({"gasPrice": gas_price})

        if gas_price is None and max_fee_per_gas is None:
            gas_pricing = self.try_get_gas_pricing(
                gas_price_strategy,
                gas_price_strategy_extra_config,
                raise_on_try=raise_on_try,
            )
            if gas_pricing is None:
                return transaction  # pragma: nocover
            transaction.update(gas_pricing)

        return transaction

    def _get_gas_price_strategy(
        self,
        gas_price_strategy: Optional[str] = None,
        extra_config: Optional[Dict] = None,
    ) -> Optional[Tuple[str, Callable]]:
        """
        Returns parameters for gas price callable.

        Note: The priority of gas price callable will be
        `extra_config(Runtime params) > self._gas_price_strategies (Set using config file.) > DEFAULT_GAS_PRICE_STRATEGIES (Default values.)`

        :param gas_price_strategy: name of the gas price strategy.
        :param extra_config: gas price strategy getter parameters.
        :return: gas price strategy's name and callable.
        """
        gas_price_strategy = (
            gas_price_strategy
            if gas_price_strategy is not None
            else self._default_gas_price_strategy
        )
        if gas_price_strategy not in AVAILABLE_STRATEGIES:  # pragma: nocover
            _default_logger.debug(
                f"Gas price strategy must be one of {AVAILABLE_STRATEGIES}, provided: {self._default_gas_price_strategy}"
            )
            return None

        _default_logger.debug(f"Using strategy: {gas_price_strategy}")
        gas_price_strategy_getter = self._gas_price_strategy_callables[
            gas_price_strategy
        ]

        parameters = cast(
            dict, get_default_gas_strategy(self._chain_id).get(gas_price_strategy)
        )
        parameters.update(self._gas_price_strategies.get(gas_price_strategy, {}))
        parameters.update(extra_config or {})
        return gas_price_strategy, gas_price_strategy_getter(**parameters)

    @staticmethod
    def __reprice(old_price: Wei) -> Wei:
        return Wei(math.ceil(old_price * TIP_INCREASE))

    @try_decorator("Unable to retrieve gas price: {}", logger_method="warning")
    def try_get_gas_pricing(
        self,
        gas_price_strategy: Optional[str] = None,
        extra_config: Optional[Dict] = None,
        old_price: Optional[Dict[str, Wei]] = None,
        **_kwargs: Any,
    ) -> Optional[Dict[str, Wei]]:
        """
        Try get the gas price based on the provided strategy.

        :param gas_price_strategy: the gas price strategy to use, e.g., the EIP-1559 strategy.
            Can be either `eip1559` or `gas_station`.
        :param extra_config: gas price strategy getter parameters.
        :param old_price: the old gas price params in case that we are trying to resubmit a transaction.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: a dictionary with the gas data.
        """

        retrieved_strategy = self._get_gas_price_strategy(
            gas_price_strategy,
            extra_config,
        )
        if retrieved_strategy is None:  # pragma: nocover
            return None
        gas_price_strategy, gas_price_strategy_callable = retrieved_strategy

        prior_strategy = (
            self._api.eth._gas_price_strategy  # pylint: disable=protected-access
        )
        try:
            self._api.eth.set_gas_price_strategy(gas_price_strategy_callable)
            gas_price = self._api.eth.generate_gas_price()
        finally:
            self._api.eth.set_gas_price_strategy(prior_strategy)  # pragma: nocover

        if gas_price is None or old_price is None:
            return gas_price

        gas_price = cast(Dict[str, Wei], gas_price)
        if gas_price_strategy in (EIP1559, EIP1559_POLYGON):
            updated_max_fee_per_gas = self.__reprice(old_price["maxFeePerGas"])
            updated_max_priority_fee_per_gas = self.__reprice(
                old_price["maxPriorityFeePerGas"]
            )

            if gas_price["maxFeePerGas"] < updated_max_fee_per_gas:
                gas_price["maxFeePerGas"] = updated_max_fee_per_gas
                gas_price["maxPriorityFeePerGas"] = updated_max_priority_fee_per_gas

        elif gas_price_strategy == GAS_STATION:
            updated_gas_price = self.__reprice(old_price["gasPrice"])
            gas_price["gasPrice"] = max(gas_price["gasPrice"], updated_gas_price)

        return gas_price

    @try_decorator("Unable to retrieve transaction count: {}", logger_method="warning")
    def _try_get_transaction_count(
        self, address: Address, **_kwargs: Any
    ) -> Optional[int]:
        """Try get the transaction count."""
        check_address = self._api.to_checksum_address(address)
        return self._api.eth.get_transaction_count(
            check_address
        )  # pylint: disable=no-member

    def update_with_gas_estimate(  # pylint: disable=arguments-differ
        self, transaction: JSONLike, raise_on_try: bool = False
    ) -> JSONLike:
        """
        Attempts to update the transaction with a gas estimate

        :param transaction: the transaction
        :param raise_on_try: whether the method will raise or log on error
        :return: the updated transaction
        """
        gas_estimate = self._try_get_gas_estimate(
            transaction,
            raise_on_try=raise_on_try,
        )
        if gas_estimate is not None:
            transaction["gas"] = gas_estimate
        return transaction

    @try_decorator("Unable to retrieve gas estimate: {}", logger_method="warning")
    def _try_get_gas_estimate(
        self, transaction: JSONLike, **_kwargs: Any
    ) -> Optional[int]:
        """Try get the gas estimate."""
        transaction = deepcopy(transaction)
        del transaction["gas"]

        try:
            return self._api.eth.estimate_gas(  # pylint: disable=no-member
                transaction=cast(TxParams, transaction)
            )
        except (ContractLogicError, ValueError) as e:
            _default_logger.warning(
                f"Unable to estimate gas with default state , "
                f"{type(e).__name__}: {str(e)}"
            )
            # gas estimation might fail when repricing txs
            # to avoid effects of pending txs when estimating gas
            # we can set the block identifier to "latest" block
            # this might fail if the node doesn't support the `block_identifier` param
            return self._api.eth.estimate_gas(  # pylint: disable=no-member
                transaction=cast(TxParams, transaction),
                block_identifier="latest",
            )

    def get_l1_data_fee(self, transaction: JSONLike) -> int:
        """Get the L1 data fee for the transaction in wei (0 if chain is not a supported L2)."""
        if self._chain_id in _OP_STACK_CHAIN_IDS:
            return self._get_op_stack_l1_data_fee(transaction)
        if self._chain_id in _ARBITRUM_CHAIN_IDS:
            return self._get_arbitrum_l1_data_fee(transaction)
        return 0

    def _get_op_stack_l1_data_fee(self, transaction: JSONLike) -> int:
        """Get the L1 data fee on OP-stack chains via the GasPriceOracle."""
        transaction = deepcopy(transaction)
        transaction.pop("from", None)
        try:
            unsigned_raw_tx = serializable_unsigned_transaction_from_dict(transaction)
            # v, r, s don't affect size; the oracle only needs the raw bytes
            unsigned_raw_tx_hex = encode_transaction(unsigned_raw_tx, (0, "0", "0"))
            gas_oracle = self.api.eth.contract(
                address=GAS_PRICE_ORACLE_ADDRESS,
                abi=GET_L1_FEE_ABI,
            )

            l1_fee_estimate = gas_oracle.functions.getL1Fee(unsigned_raw_tx_hex).call()
        except (ContractLogicError, ValueError) as e:
            _default_logger.warning(
                f"Unable to estimate L1 data fee with default state , "
                f"{type(e).__name__}: {str(e)}"
            )
            l1_fee_estimate = 0

        # pad by 12.5% for next-block worst case (per Optimism docs)
        return int(l1_fee_estimate * MAX_OP_L1_FEE_INCREASE_RELATIVE_PER_BLOCK)

    # How to estimate gas in Arbitrum https://docs.arbitrum.io/build-decentralized-apps/how-to-estimate-gas#where-to-get-each-variable
    def _get_arbitrum_l1_data_fee(self, transaction: JSONLike) -> int:
        """Get the L1 data fee on Arbitrum Nitro chains via NodeInterface."""
        to_address = (
            transaction.get("to") or "0x0000000000000000000000000000000000000000"
        )
        data_hex = transaction.get("data", b"") or b""
        is_contract_creation = not transaction.get("to")
        try:
            node_interface = self.api.eth.contract(  # type: ignore[call-overload]
                address=ARBITRUM_NODE_INTERFACE_ADDRESS,
                abi=ARBITRUM_GAS_ESTIMATE_L1_COMPONENT_ABI,
            )
            # precompile is declared payable but invoked via eth_call per its docstring
            (
                gas_estimate_for_l1,
                base_fee,
                _l1_base_fee_estimate,
            ) = node_interface.functions.gasEstimateL1Component(
                to_address, is_contract_creation, data_hex
            ).call()
        except (ContractLogicError, ValueError) as e:
            _default_logger.warning(
                f"Unable to estimate Arbitrum L1 data fee, "
                f"{type(e).__name__}: {str(e)}"
            )
            return 0

        return int(gas_estimate_for_l1 * base_fee * ARBITRUM_L1_FEE_PADDING)

    def send_signed_transaction(
        self, tx_signed: JSONLike, raise_on_try: bool = False
    ) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :param raise_on_try: whether the method will raise or log on error
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(
            tx_signed, raise_on_try=raise_on_try
        )
        return tx_digest

    @try_decorator("Unable to send transaction: {}", logger_method="warning")
    def _try_send_signed_transaction(
        self, tx_signed: JSONLike, **_kwargs: Any
    ) -> Optional[str]:
        """
        Try send a signed transaction.

        :param tx_signed: the signed transaction
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: tx_digest, if present
        """
        signed_transaction = SignedTransactionTranslator.from_dict(tx_signed)
        hex_value = self._api.eth.send_raw_transaction(  # pylint: disable=no-member
            signed_transaction.raw_transaction
        )
        tx_digest = hex_value.to_0x_hex()
        _default_logger.debug(
            "Successfully sent transaction with digest: {}".format(tx_digest)
        )
        return tx_digest

    def get_transaction_receipt(
        self, tx_digest: str, raise_on_try: bool = False
    ) -> Optional[JSONLike]:
        """
        Get the transaction receipt for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :param raise_on_try: whether the method will raise or log on error
        :return: the tx receipt, if present
        """
        tx_receipt = self._try_get_transaction_receipt(
            tx_digest,
            raise_on_try=raise_on_try,
        )

        if tx_receipt is not None and not bool(tx_receipt["status"]):
            tx = self.get_transaction(tx_digest, raise_on_try=raise_on_try)
            tx_receipt["revert_reason"] = self._try_get_revert_reason(
                tx,
                raise_on_try=raise_on_try,
            )

        return tx_receipt

    @try_decorator(
        "Error when attempting getting tx receipt: {}", logger_method="debug"
    )
    def _try_get_transaction_receipt(
        self, tx_digest: str, **_kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Try get the transaction receipt.

        :param tx_digest: the digest associated to the transaction.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: the tx receipt, if present
        """
        tx_receipt = self._api.eth.get_transaction_receipt(  # pylint: disable=no-member
            cast(HexStr, tx_digest)
        )
        return AttributeDictTranslator.to_dict(tx_receipt)

    def get_transaction(
        self,
        tx_digest: str,
        raise_on_try: bool = False,
    ) -> Optional[JSONLike]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :param raise_on_try: whether the method will raise or log on error
        :return: the tx, if present
        """
        tx = self._try_get_transaction(tx_digest, raise_on_try=raise_on_try)
        return tx

    @try_decorator("Error when attempting getting tx: {}", logger_method="debug")
    def _try_get_transaction(
        self, tx_digest: str, **_kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Get the transaction.

        :param tx_digest: the transaction digest.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: the tx, if found
        """
        tx = self._api.eth.get_transaction(
            cast(HexStr, tx_digest)
        )  # pylint: disable=no-member
        return AttributeDictTranslator.to_dict(tx)

    @try_decorator(
        "Error when attempting getting tx revert reason: {}", logger_method="debug"
    )
    def _try_get_revert_reason(self, tx: TxData, **_kwargs: Any) -> str:
        """Try to check the revert reason of a transaction.

        :param tx: the transaction for which we want to get the revert reason.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: the revert reason message.
        """
        # build a new transaction to replay:
        replay_tx = {
            "to": tx["to"],
            "from": tx["from"],
            "value": tx["value"],
            "data": tx["input"],
        }

        try:
            # replay the transaction on the provider
            self.api.eth.call(replay_tx, tx["blockNumber"] - 1)
        except ContractLogicError as e:
            # execution reverted exception
            return e.message
        except HTTPError as e:
            # http exception
            raise e
        else:
            # given tx not reverted
            raise ValueError(f"The given transaction has not been reverted!\ntx: {tx}")

    def get_contract_instance(
        self, contract_interface: Dict[str, str], contract_address: Optional[str] = None
    ) -> Any:
        """
        Get the instance of a contract.

        :param contract_interface: the contract interface.
        :param contract_address: the contract address.
        :return: the contract instance
        """
        if contract_address is None:
            instance = self.api.eth.contract(
                abi=contract_interface[_ABI],
                bytecode=contract_interface[_BYTECODE],
            )
        else:
            _contract_address = self.api.to_checksum_address(contract_address)
            instance = self.api.eth.contract(
                address=_contract_address,
                abi=contract_interface[_ABI],
                bytecode=contract_interface[_BYTECODE],
            )
        return instance

    def get_deploy_transaction(  # pylint: disable=arguments-differ
        self,
        contract_interface: Dict[str, str],
        deployer_address: Address,
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Get the transaction to deploy the smart contract.

        :param contract_interface: the contract interface.
        :param deployer_address: The address that will deploy the contract.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: keyword arguments
        :return: the transaction dictionary.
        """

        # value to send to contract (in Wei)
        value: int = kwargs.pop("value", 0)

        # the gas to be used (in Wei)
        gas: Optional[int] = kwargs.pop("gas", None)

        # maximum amount you’re willing to pay, inclusive of `baseFeePerGas` and
        # `maxPriorityFeePerGas`. The difference between `maxFeePerGas` and
        # `baseFeePerGas + maxPriorityFeePerGas` is refunded  (in Wei).
        max_fee_per_gas: Optional[int] = kwargs.pop("max_fee_per_gas", None)

        # the part of the fee that goes to the miner (in Wei).
        max_priority_fee_per_gas: Optional[str] = kwargs.pop(
            "max_priority_fee_per_gas", None
        )

        # the gas price (in Wei)
        gas_price: Optional[str] = kwargs.pop("gas_price", None)

        # the gas price strategy to be used.
        gas_price_strategy: Optional[str] = kwargs.pop("gas_price_strategy", None)

        # extra config for gas price strategy.
        gas_price_strategy_extra_config: Optional[Dict] = kwargs.pop(
            "gas_price_strategy_extra_config", None
        )

        transaction: Optional[JSONLike] = None
        _deployer_address = self.api.to_checksum_address(deployer_address)
        nonce = self._try_get_transaction_count(
            _deployer_address, raise_on_try=raise_on_try
        )
        if nonce is None:
            return transaction
        instance = self.get_contract_instance(contract_interface)
        transaction = {
            "value": value,
            "nonce": nonce,
        }
        if max_fee_per_gas is not None:
            max_priority_fee_per_gas = (
                self._try_get_max_priority_fee(raise_on_try=raise_on_try)
                if max_priority_fee_per_gas is None
                else max_priority_fee_per_gas
            )
            if max_priority_fee_per_gas is None:
                return None  # pragma: nocover
            transaction.update(
                {
                    "maxFeePerGas": max_fee_per_gas,
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                }
            )

        if gas_price is not None:
            transaction.update({"gasPrice": gas_price})

        if gas_price is None and max_fee_per_gas is None:
            gas_pricing = self.try_get_gas_pricing(
                gas_price_strategy,
                gas_price_strategy_extra_config,
                raise_on_try=raise_on_try,
            )

            if gas_pricing is None:
                return None  # pragma: nocover

            transaction.update(gas_pricing)

        transaction.update({"from": _deployer_address})
        transaction = instance.constructor(**kwargs).build_transaction(transaction)
        if transaction is None:
            return None  # pragma: nocover
        transaction.pop("to", None)  # only 'from' address, don't insert 'to' address!
        if gas is not None:
            transaction.update({"gas": gas})
        if self._is_gas_estimation_enabled:
            transaction = self.update_with_gas_estimate(
                transaction, raise_on_try=raise_on_try
            )
        return transaction

    @try_decorator("Unable to retrieve max_priority_fee: {}", logger_method="warning")
    def _try_get_max_priority_fee(self, **_kwargs: Any) -> str:
        """Try get the gas estimate."""
        return cast(str, self.api.eth.max_priority_fee)

    @classmethod
    def is_valid_address(cls, address: Address) -> bool:
        """
        Check if the address is valid.

        :param address: the address to validate
        :return: whether the address is valid
        """
        return Web3.is_checksum_address(address)

    @classmethod
    def contract_method_call(  # pylint: disable=arguments-differ
        cls,
        contract_instance: Any,
        method_name: str,
        **method_args: Any,
    ) -> Optional[JSONLike]:
        """Call a contract's method

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract call parameters
        :return: the call result
        """
        method = getattr(contract_instance.functions, method_name)
        result = method(**method_args).call()
        return result

    def build_transaction(  # pylint: disable=too-many-positional-arguments
        self,
        contract_instance: Any,
        method_name: str,
        method_args: Optional[Dict[Any, Any]],
        tx_args: Optional[Dict[Any, Any]],
        raise_on_try: bool = False,
    ) -> Optional[JSONLike]:
        """Prepare a transaction

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract parameters
        :param tx_args: the transaction parameters
        :param raise_on_try: whether the method will raise or log on error
        :return: the transaction
        """

        if method_args is None:
            raise ValueError("Argument 'method_args' cannot be 'None'.")

        method = getattr(contract_instance.functions, method_name)
        tx = method(**cast(Dict, method_args))

        if tx_args is None:
            raise ValueError("Argument 'tx_args' cannot be 'None'.")

        tx_args = cast(Dict, tx_args)

        nonce = self.api.eth.get_transaction_count(tx_args["sender_address"])
        tx_params = {
            "nonce": nonce,
            "value": tx_args["value"] if "value" in tx_args else 0,
            "gas": 1,  # set this as a placeholder to avoid estimation on build_transaction()
        }

        # Parameter camel-casing due to contract api requirements
        for field in [
            "gas",
            "gasPrice",
            "maxFeePerGas",
            "maxPriorityFeePerGas",
        ]:
            if field in tx_args and tx_args[field] is not None:
                tx_params[field] = tx_args[field]

        if (
            "gasPrice" not in tx_params
            and "maxFeePerGas" not in tx_params
            and "maxPriorityFeePerGas" not in tx_params
        ):
            gas_data = self.try_get_gas_pricing(
                old_price=tx_args.get("old_price"), raise_on_try=raise_on_try
            )
            if gas_data:
                tx_params.update(gas_data)  # pragma: nocover

        tx = tx.build_transaction(tx_params)
        if self._is_gas_estimation_enabled:
            tx = self.update_with_gas_estimate(tx, raise_on_try=raise_on_try)

        return tx

    def get_transaction_transfer_logs(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        contract_instance: Any,
        tx_hash: str,
        target_address: Optional[str] = None,
    ) -> Optional[JSONLike]:
        """
        Get all transfer events derived from a transaction.

        :param contract_instance: the contract
        :param tx_hash: the transaction hash
        :param target_address: optional address to filter transfer events to just those that affect it
        :return: the transfer logs
        """
        try:
            tx_receipt = self.api.eth.get_transaction_receipt(tx_hash)
            if tx_receipt is None:
                raise ValueError  # pragma: nocover

        except (TransactionNotFound, ValueError):  # pragma: nocover
            return dict(logs=[])

        transfer_logs = contract_instance.events.Transfer().processReceipt(tx_receipt)

        return dict(logs=transfer_logs)

    def send_signed_transactions(
        self,
        signed_transactions: List[JSONLike],
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[List[str]]:
        """
        Atomically send multiple of transactions.

        This operation is not supported for the ethereum ledger.

        :param signed_transactions: the signed transactions to bundle together and send.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: the keyword arguments.
        """
        raise NotImplementedError(  # pragma: nocover
            f"Sending a bundle of transactions is not supported for the {self.identifier} plugin"
        )

    def batch_filter_wrapper(  # pylint: disable=too-many-positional-arguments
        self,
        event: ContractEvent,
        match_single: Dict[str, Any],
        match_any: Dict[str, Any],
        to_block: BlockNumber,
        from_block: BlockNumber,
    ) -> Any:
        """A wrapper for a single batch's event filtering operation."""

        def batch_filter() -> Any:
            """Filter events for a specific batch."""
            filter_ = event.build_filter()
            filter_.from_block = from_block
            filter_.to_block = to_block
            method_to_match_dict = {
                MATCH_SINGLE: match_single,
                MATCH_ANY: match_any,
            }
            match_items(filter_, event.event_name, method_to_match_dict)

            try:
                return list(filter_.deploy(self.api).get_all_entries())
            except (Urllib3ReadTimeoutError, RequestsReadTimeoutError):
                msg = (
                    "The RPC timed out! This usually happens if the filtering is too wide. "
                    f"The service tried to filter the blocks in the range [{from_block} - {to_block}]. "
                    f"If this issue persists, please try lowering the batch size!"
                )
                return msg

        return batch_filter

    def filter_event(  # pylint: disable=too-many-positional-arguments
        self,
        event: ContractEvent,
        match_single: Dict[str, Any],
        match_any: Dict[str, Any],
        to_block: BlockNumber,
        from_block: BlockNumber = 0,
        batch_size: int = 5_000,
        max_retries: int = 5,
        reduce_factor: float = 0.25,
        timeout: int = 5 * 60,
    ) -> Optional[JSONLike]:
        """Filter an event using batching to avoid RPC timeouts.

        :param event: the event to filter for.
        :param match_single: the filter parameters with value checking against the event abi. It allows for defining a single match value.
        :param match_any: the filter parameters with value checking against the event abi. It allows for defining multiple match values.
        :param to_block: the block to which to filter.
        :param from_block: the block from which to start filtering.
        :param batch_size: the blocks' batch size of the filtering.
        :param max_retries: the maximum number of retries.
        :param reduce_factor: the percentage by which the batch size is reduced in case of a timeout.
        :param timeout: a timeout in seconds to interrupt the operation in case the RPC request hangs.
        :return: the filtering result.
        """

        filtering_result = []
        n_retries = 0
        while from_block < to_block:
            max_to_block = from_block + batch_size
            to_block_adj = BlockNumber(min(max_to_block, to_block))
            filtering_operation = self.batch_filter_wrapper(
                event, match_single, match_any, to_block_adj, from_block
            )
            batch_result, err = rpc_call_with_timeout(filtering_operation, timeout)
            if err is not None:
                _default_logger.warning(err)

            if not batch_result and n_retries == max_retries:
                err = "Skipping the filtering operation as the RPC is misbehaving."
                raise ValueError(err)

            if not batch_result:
                n_retries += 1
                keep_fraction = 1 - reduce_factor
                batch_size = int(batch_size * keep_fraction)
                _default_logger.warning(
                    f"Repeating this call with a decreased batch size of {batch_size}."
                )
                continue

            from_block += batch_size
            filtering_result.extend(batch_result)

        return dict(filtering_result=filtering_result)


class EthereumFaucetApi(FaucetApi):
    """Ethereum testnet faucet API."""

    identifier = _ETHEREUM
    testnet_name = TESTNET_NAME

    def get_wealth(self, address: Address, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url
        """
        self._try_get_wealth(address, url)

    @staticmethod
    @try_decorator(
        "An error occured while attempting to generate wealth:\n{}",
        logger_method="error",
    )
    def _try_get_wealth(address: Address, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url
        """
        if url is None:
            raise ValueError(  # pragma: nocover
                "Url is none, no default url provided. Please provide a faucet url."
            )
        response = requests.get(url + address, timeout=NETWORK_REQUEST_DEFAULT_TIMEOUT)
        if response.status_code // 100 == 5:  # pragma: no cover
            _default_logger.error("Response: {}".format(response.status_code))
        elif response.status_code // 100 in [3, 4]:  # pragma: nocover
            response_dict = json.loads(response.text)
            _default_logger.warning(
                "Response: {}\nMessage: {}".format(
                    response.status_code, response_dict.get("message")
                )
            )
        elif response.status_code // 100 == 2:  # pragma: no cover
            response_dict = json.loads(response.text)
            _default_logger.info(
                "Response: {}\nMessage: {}".format(
                    response.status_code, response_dict.get("message")
                )
            )


class SimpleCacheLockWrapper:
    """Wrapper for session_cache with threading.Lock."""

    def __init__(self, session_cache: SimpleCache) -> None:
        """Init wrapper."""
        self.session_cache = session_cache
        self.lock = threading.Lock()

    def __contains__(self, *args: Any, **kwargs: Any) -> Any:
        """Contain item."""
        with self.lock:
            return self.session_cache.__contains__(*args, **kwargs)

    def __len__(self) -> int:
        """Length of the cache"""
        return len(self.session_cache)

    def cache(self, key: str, value: Any) -> Dict[str, Any]:
        """session_cache Cache."""
        return self.session_cache.cache(key=key, value=value)

    def get_cache_entry(self, key: str) -> Any:
        """Get cache entry."""
        with self.lock:
            return self.session_cache.get_cache_entry(key)

    def clear(self) -> None:
        """Clear cache entries."""
        with self.lock:
            self.session_cache.clear()

    def items(self) -> Dict[str, Any]:
        """Return session items."""
        return self.session_cache.items()
