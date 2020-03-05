# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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

"""This test module contains the integration test for the erc1155 smart contract."""

import logging
import os
from pathlib import Path
from random import randrange

import pytest

from vyper.functions import keccak256

from .conftest import PRIVATE_KEY_1, PRIVATE_KEY_2


def generate_id(token_id, item_id):
    """Generate an id for the token we want to create."""
    # x << y: returns x with the bits shifted to the left by y places, which is equivalent to multiply x by 2**y.
    token_id = token_id
    index = item_id
    final_id_int = (token_id << 128) + index
    return final_id_int


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BATCH_TOKEN_IDS = []
NFT = 1
FT = 2
for j in range(10):
    BATCH_TOKEN_IDS.append(generate_id(FT, j))

BATCH_TOKEN_QUANTITIES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
URI = ["uri1", "uri2", "uri3", "uri4", "uri5", "uri6", "uri7", "uri8", "uri9", "uri10"]
SINGLE_TOKEN_ID = generate_id(FT, 11)
SINGLE_TOKEN_QUANTITY = 110
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ERC165_INTERFACE_ID = (
    "0x0000000000000000000000000000000000000000000000000000000001ffc9a7"
)
BURN_QUANTITY = 1


@pytest.fixture
def storage_contract(w3, get_contract):
    owner, operator, agent = w3.eth.accounts[:3]
    path = Path(
        os.getcwd(),
        "packages",
        "fetchai",
        "contracts",
        "erc1155",
        "contracts",
        "erc1155.vy",
    )
    with open(path) as f:
        contract_code = f.read()
    contract = get_contract(contract_code)
    contract.createSingle(
        operator,
        SINGLE_TOKEN_ID,
        "http://serverWithTheJsonDetailsOfTheItem",
        transact={"from": owner},
    )

    contract.mint(
        operator, SINGLE_TOKEN_ID, SINGLE_TOKEN_QUANTITY, transact={"from": owner}
    )

    contract.createBatch(operator, BATCH_TOKEN_IDS, transact={"from": owner})

    contract.mintBatch(
        operator, BATCH_TOKEN_IDS, BATCH_TOKEN_QUANTITIES, transact={"from": owner}
    )
    return contract


def test_supported_interface(storage_contract):
    """Test the supported interface."""
    assert storage_contract.supportsInterface(ERC165_INTERFACE_ID) == 1


def test_get_hash(w3, storage_contract):
    """Test the get hash functionality."""
    agent1 = w3.eth.account.from_key(private_key=PRIVATE_KEY_1)
    agent2 = w3.eth.account.from_key(private_key=PRIVATE_KEY_2)
    from_hash = storage_contract.getAddress(agent1.address)
    to_hash = storage_contract.getAddress(agent2.address)
    new_batch_token_ids = []
    for i in range(100, 110):
        new_batch_token_ids.append(generate_id(FT, i))
    _from_values = [2, 0, 2, 0, 1, 2, 3, 5, 2, 3]
    _to_values = [0, 1, 0, 2, 0, 0, 0, 0, 0, 0]
    value_eth = 1
    nonce = randrange(0, 10000000)
    while storage_contract.is_nonce_used(agent1.address, nonce):
        nonce = randrange(0, 10000000)
    hashed_data = get_hash(
        from_hash,
        to_hash,
        new_batch_token_ids,
        _from_values,
        _to_values,
        value_eth,
        nonce,
    )
    assert (
        storage_contract.getHash(
            agent1.address,
            agent2.address,
            new_batch_token_ids,
            _from_values,
            _to_values,
            value_eth,
            nonce,
        )
        == hashed_data
    )


def test_get_hash_single(w3, storage_contract):
    """Test the get hash functionality."""
    agent1 = w3.eth.account.from_key(private_key=PRIVATE_KEY_1)
    agent2 = w3.eth.account.from_key(private_key=PRIVATE_KEY_2)
    from_hash = storage_contract.getAddress(agent1.address)
    to_hash = storage_contract.getAddress(agent2.address)
    token_id = generate_id(FT, 1)
    _from_value = 0
    _to_value = 2
    value_eth = 1
    nonce = randrange(0, 10000000)
    while storage_contract.is_nonce_used(agent1.address, nonce):
        nonce = randrange(0, 10000000)
    hashed_data = get_single_hash(
        from_hash, to_hash, token_id, _from_value, _to_value, value_eth, nonce
    )
    assert (
        storage_contract.getSingleHash(
            agent1.address,
            agent2.address,
            token_id,
            _from_value,
            _to_value,
            value_eth,
            nonce,
        )
        == hashed_data
    )


def test_owner(w3, storage_contract):
    """Test the owner is set correctly."""
    owner = w3.eth.accounts[0]
    assert storage_contract.owner() == owner


def test_balance_of(w3, storage_contract, assert_tx_failed, get_logs):
    """Test the balance for an id."""
    operator = w3.eth.accounts[1]
    balance = storage_contract.balanceOf(operator, SINGLE_TOKEN_ID)
    assert balance == SINGLE_TOKEN_QUANTITY
    balance = storage_contract.balanceOf(ZERO_ADDRESS, SINGLE_TOKEN_ID)
    assert balance == 0


def test_balance_of_batch(w3, storage_contract, assert_tx_failed):
    """Test the balances for a set of ids."""
    owner, operator = w3.eth.accounts[:2]
    balances = storage_contract.balanceOfBatch([operator] * 10, BATCH_TOKEN_IDS)
    assert balances == BATCH_TOKEN_QUANTITIES
    balances = storage_contract.balanceOfBatch([owner] * 10, BATCH_TOKEN_IDS)
    assert balances == [0] * 10


def test_safe_transfer_from(w3, storage_contract, assert_tx_failed, get_logs):
    """Test the safe transfer from function from the smart contract."""
    operator, agent = w3.eth.accounts[1:3]
    data = keccak256(b"hello")
    # agent cannot transfer to zero address
    assert_tx_failed(
        lambda: storage_contract.safeTransferFrom(
            agent,
            ZERO_ADDRESS,
            SINGLE_TOKEN_ID,
            SINGLE_TOKEN_QUANTITY,
            data,
            transact={"from": agent},
        )
    )

    # agent has no tokens so cannot transfer
    assert_tx_failed(
        lambda: storage_contract.safeTransferFrom(
            agent,
            operator,
            SINGLE_TOKEN_ID,
            SINGLE_TOKEN_QUANTITY,
            data,
            transact={"from": agent},
        )
    )

    # operator can transfer
    tx_hash = storage_contract.safeTransferFrom(
        operator, agent, SINGLE_TOKEN_ID, 10, data, transact={"from": operator}
    )
    logs = get_logs(tx_hash, storage_contract, "TransferSingle")
    assert len(logs) > 0
    args = logs[0].args
    assert args._from == operator
    assert args._to == agent
    assert args._id == SINGLE_TOKEN_ID
    assert args._value == 10
    balance = storage_contract.balanceOf(operator, SINGLE_TOKEN_ID)
    assert balance == SINGLE_TOKEN_QUANTITY - 10


def test_safe_transfer_batch(w3, storage_contract, assert_tx_failed, get_logs):
    """Test the safe transfer batch function from the smart contract."""
    operator, agent = w3.eth.accounts[1:3]
    data = keccak256(b"hello")
    # agent cannot transfer to zero address
    assert_tx_failed(
        lambda: storage_contract.safeBatchTransferFrom(
            agent,
            ZERO_ADDRESS,
            BATCH_TOKEN_IDS,
            BATCH_TOKEN_QUANTITIES,
            data,
            transact={"from": agent},
        )
    )

    # agent has no tokens so cannot transfer
    assert_tx_failed(
        lambda: storage_contract.safeBatchTransferFrom(
            agent,
            operator,
            BATCH_TOKEN_IDS,
            BATCH_TOKEN_QUANTITIES,
            data,
            transact={"from": agent},
        )
    )

    batch_tokens_transfer_quantities = [2, 3, 2, 1, 2, 1, 7, 2, 4, 1]
    expected_token_quantities = BATCH_TOKEN_QUANTITIES
    for i in range(10):
        expected_token_quantities[i] -= batch_tokens_transfer_quantities[i]
    # operator can transfer
    tx_hash = storage_contract.safeBatchTransferFrom(
        operator,
        agent,
        BATCH_TOKEN_IDS,
        batch_tokens_transfer_quantities,
        data,
        transact={"from": operator},
    )
    logs = get_logs(tx_hash, storage_contract, "TransferBatch")
    assert len(logs) > 0
    args = logs[0].args
    logger.info(args)
    assert args._from == operator
    assert args._to == agent
    assert args._ids == BATCH_TOKEN_IDS
    assert args._values == batch_tokens_transfer_quantities
    balances = storage_contract.balanceOfBatch([operator] * 10, BATCH_TOKEN_IDS)
    assert balances == BATCH_TOKEN_QUANTITIES


def test_create_mint_single(w3, storage_contract, assert_tx_failed, get_logs):
    """Test the create single function of the contract."""
    owner, operator = w3.eth.accounts[:2]
    new_id = generate_id(FT, 12)
    storage_contract.createSingle(
        operator,
        new_id,
        "http://serverWithTheJsonDetailsOfTheItem",
        transact={"from": owner},
    )

    storage_contract.mint(
        operator, new_id, SINGLE_TOKEN_QUANTITY, transact={"from": owner}
    )

    balance = storage_contract.balanceOf(operator, new_id)
    logger.info(balance)
    assert balance == SINGLE_TOKEN_QUANTITY


def test_mint_nft_error(w3, storage_contract, assert_tx_failed):
    """Test that the minting will fail if we mint an NFT with a quantity more than 1."""
    owner = w3.eth.accounts[0]
    operator = w3.eth.accounts[1]
    _id = generate_id(NFT, 10)
    _quantity = 50

    storage_contract.createSingle(
        operator,
        _id,
        "http://serverWithTheJsonDetailsOfTheItem",
        transact={"from": owner},
    )

    assert_tx_failed(
        lambda: storage_contract.mint(
            operator, _id, _quantity, transact={"from": owner}
        )
    )


def test_burn_single(w3, storage_contract, assert_tx_failed, get_logs):
    """Test the burn functionality of the smart contract."""
    operator = w3.eth.accounts[1]
    tx_hash = storage_contract.burn(
        SINGLE_TOKEN_ID, BURN_QUANTITY, transact={"from": operator}
    )
    logs = get_logs(tx_hash, storage_contract, "TransferSingle")
    assert len(logs) > 0
    args = logs[0].args
    assert len(logs) > 0
    assert args._from == operator
    assert args._to == ZERO_ADDRESS
    assert args._id == SINGLE_TOKEN_ID
    assert args._value == 1
    balance = storage_contract.balanceOf(operator, SINGLE_TOKEN_ID)
    assert balance == SINGLE_TOKEN_QUANTITY - 1


def test_create_mint_batch(w3, storage_contract, assert_tx_failed, get_logs):
    """Test the create and mint functionality of the smart contract."""
    owner, operator = w3.eth.accounts[:2]
    new_batch_token_ids = []
    for i in range(100, 110):
        new_batch_token_ids.append(generate_id(FT, i))
    new_batch_token_quantities = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]

    storage_contract.createBatch(
        operator, new_batch_token_ids, transact={"from": owner}
    )

    assert_tx_failed(
        lambda: storage_contract.createBatch(
            operator, new_batch_token_ids, transact={"from": operator}
        )
    )

    storage_contract.mintBatch(
        operator,
        new_batch_token_ids,
        new_batch_token_quantities,
        transact={"from": owner},
    )

    assert_tx_failed(
        lambda: storage_contract.mintBatch(
            operator,
            new_batch_token_ids,
            new_batch_token_quantities,
            transact={"from": operator},
        )
    )

    balances = storage_contract.balanceOfBatch([operator] * 10, new_batch_token_ids)
    assert balances == new_batch_token_quantities


def test_create_mint_mixed(w3, storage_contract, get_logs, assert_tx_failed):
    """Test the creation of different type of tokens."""
    owner = w3.eth.accounts[0]
    operator = w3.eth.accounts[1]
    _ids = []
    _quantities = []
    for i in range(10):
        token_id = randrange(1, 3)
        _ids.append(generate_id(token_id=token_id, item_id=i))
        if token_id == 1:
            _quantities.append(1)
        else:
            _quantities.append(randrange(0, 10))

    storage_contract.createBatch(operator, _ids, transact={"from": owner})

    assert_tx_failed(
        lambda: storage_contract.createBatch(owner, _ids, transact={"from": operator})
    )

    storage_contract.mintBatch(operator, _ids, _quantities, transact={"from": owner})

    assert_tx_failed(
        lambda: storage_contract.mintBatch(
            owner, _ids, _quantities, transact={"from": operator}
        )
    )

    balances = storage_contract.balanceOfBatch([operator] * 10, _ids)
    assert balances == _quantities


def test_burn_batch(w3, storage_contract, get_logs):
    """Test the burn batch functionality of the smart contract."""
    operator = w3.eth.accounts[1]
    quantities_to_burn = [2, 3, 4, 4, 5, 2, 3, 4, 4, 5]
    tx_hash = storage_contract.burnBatch(
        BATCH_TOKEN_IDS, quantities_to_burn, transact={"from": operator}
    )
    for i in range(10):
        BATCH_TOKEN_QUANTITIES[i] -= quantities_to_burn[i]
    logs = get_logs(tx_hash, storage_contract, "TransferBatch")
    assert len(logs) > 0
    args = logs[0].args
    assert args._from == operator
    assert args._to == ZERO_ADDRESS
    assert args._ids == BATCH_TOKEN_IDS
    assert args._values == quantities_to_burn
    balances = storage_contract.balanceOfBatch([operator] * 10, BATCH_TOKEN_IDS)
    assert balances == BATCH_TOKEN_QUANTITIES


def test_set_approval_for_all(w3, storage_contract):
    """Test the Approval functionality."""
    agent = w3.eth.accounts[2]
    owner = w3.eth.accounts[0]
    storage_contract.setApprovalForAll(owner, True, transact={"from": agent})
    assert storage_contract.isApprovedForAll(
        agent, owner
    ), "This is not an approved address."


def test_positive_trade(w3, storage_contract, get_logs):
    """Test the trade functionality of the smart contract."""
    # create entities
    owner = w3.eth.accounts[0]
    agent1 = w3.eth.account.from_key(private_key=PRIVATE_KEY_1)
    agent2 = w3.eth.account.from_key(private_key=PRIVATE_KEY_2)

    # fund agent1 and agent2 with ether
    w3.eth.sendTransaction(
        {"to": agent1.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent1_pre_trade_balance = w3.eth.getBalance(agent1.address)
    logger.info("[{}]: {}".format(agent1.address, agent1_pre_trade_balance))
    w3.eth.sendTransaction(
        {"to": agent2.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent2_pre_trade_balance = w3.eth.getBalance(agent2.address)
    logger.info("[{}]: {}".format(agent2.address, agent2_pre_trade_balance))

    # fund agent1 and agent2 with tokens
    new_token_id = generate_id(FT, 86)
    new_token_quantity = 5
    storage_contract.createSingle(
        agent1.address,
        new_token_id,
        "http://serverWithTheJsonDetailsOfTheItem",
        transact={"from": owner},
    )

    storage_contract.mint(
        agent1.address, new_token_id, new_token_quantity, transact={"from": owner}
    )

    # prepare terms of trade
    from_hash = storage_contract.getAddress(agent1.address)
    to_hash = storage_contract.getAddress(agent2.address)
    _from_value = 2
    _to_value = 0
    value_eth = 45
    nonce = randrange(0, 10000000)
    while storage_contract.is_nonce_used(agent1.address, nonce):
        nonce = randrange(0, 10000000)
    data = b"hello"
    hashed_data = get_single_hash(
        from_hash, to_hash, new_token_id, _from_value, _to_value, value_eth, nonce
    )

    # agent2 to sign data
    signature_object = agent2.signHash(hashed_data)
    signature = bytes(signature_object["signature"])
    assert (
        w3.eth.account.recoverHash(hashed_data, signature=signature) == agent2.address
    )

    # agent1 to submit transaction
    tx_hash = storage_contract.trade(
        agent1.address,
        agent2.address,
        new_token_id,
        _from_value,
        _to_value,
        value_eth,
        nonce,
        signature,
        data,
        transact={"value": value_eth, "from": agent1.address},
    )

    # assert correctness of logs
    logs = get_logs(tx_hash, storage_contract, "TransferSingle")
    assert len(logs) > 0
    logger.info(logs)
    args = logs[0].args
    logger.info(args)
    assert args._from == agent1.address
    assert args._to == agent2.address
    assert args._id == new_token_id
    assert args._value == _from_value

    # assert correctness of final eth balances
    assert w3.eth.getBalance(agent1.address) == agent1_pre_trade_balance - value_eth
    assert w3.eth.getBalance(agent2.address) == agent2_pre_trade_balance + value_eth

    # assert correctness of final token balances
    balance = storage_contract.balanceOf(agent1.address, new_token_id)
    assert balance == (new_token_quantity - _from_value)


def test_negative_trade(w3, storage_contract, get_logs):
    """Test the trade functionality of the smart contract."""
    # create entities
    owner = w3.eth.accounts[0]
    agent1 = w3.eth.account.from_key(private_key=PRIVATE_KEY_1)
    agent2 = w3.eth.account.from_key(private_key=PRIVATE_KEY_2)

    # fund agent1 and agent2 with ether
    w3.eth.sendTransaction(
        {"to": agent1.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent1_pre_trade_balance = w3.eth.getBalance(agent1.address)
    logger.info("[{}]: {}".format(agent1.address, agent1_pre_trade_balance))
    w3.eth.sendTransaction(
        {"to": agent2.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent2_pre_trade_balance = w3.eth.getBalance(agent2.address)
    logger.info("[{}]: {}".format(agent2.address, agent2_pre_trade_balance))

    # fund agent1 and agent2 with tokens
    new_token_id = generate_id(FT, 86)
    new_token_quantity = 5
    storage_contract.createSingle(
        agent2.address,
        new_token_id,
        "http://serverWithTheJsonDetailsOfTheItem",
        transact={"from": owner},
    )

    storage_contract.mint(
        agent2.address, new_token_id, new_token_quantity, transact={"from": owner}
    )

    # prepare terms of trade
    from_hash = storage_contract.getAddress(agent1.address)
    to_hash = storage_contract.getAddress(agent2.address)
    _from_value = 0
    _to_value = 5
    value_eth = 1
    nonce = randrange(0, 10000000)
    while storage_contract.is_nonce_used(agent1.address, nonce):
        nonce = randrange(0, 10000000)
    data = b"hello"
    hashed_data = get_single_hash(
        from_hash, to_hash, new_token_id, _from_value, _to_value, value_eth, nonce
    )

    # agent2 to sign data
    signature_object = agent2.signHash(hashed_data)
    signature = bytes(signature_object["signature"])
    assert (
        w3.eth.account.recoverHash(hashed_data, signature=signature) == agent2.address
    )

    # agent1 to submit transaction
    tx_hash = storage_contract.trade(
        agent1.address,
        agent2.address,
        new_token_id,
        _from_value,
        _to_value,
        value_eth,
        nonce,
        signature,
        data,
        transact={"value": 1, "from": agent1.address},
    )

    # assert correctness of logs
    logs = get_logs(tx_hash, storage_contract, "TransferSingle")
    assert len(logs) > 0
    logger.info(logs)
    args = logs[1].args
    logger.info(args)
    assert args._from == agent2.address
    assert args._to == agent1.address
    assert args._id == new_token_id
    assert args._value == _to_value

    # assert correctness of final eth balances
    assert w3.eth.getBalance(agent1.address) == agent1_pre_trade_balance - value_eth
    assert w3.eth.getBalance(agent2.address) == agent2_pre_trade_balance + value_eth

    # assert correctness of final token balances
    balance = storage_contract.balanceOf(agent2.address, new_token_id)
    assert balance == (new_token_quantity - _to_value)


def test_failed_single_trade(w3, storage_contract, get_logs, assert_tx_failed):
    """Test the case that negative and positive values are both > 0."""
    # create entities
    owner = w3.eth.accounts[0]
    agent1 = w3.eth.account.from_key(private_key=PRIVATE_KEY_1)
    agent2 = w3.eth.account.from_key(private_key=PRIVATE_KEY_2)

    # fund agent1 and agent2 with ether
    w3.eth.sendTransaction(
        {"to": agent1.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent1_pre_trade_balance = w3.eth.getBalance(agent1.address)
    logger.info("[{}]: {}".format(agent1.address, agent1_pre_trade_balance))
    w3.eth.sendTransaction(
        {"to": agent2.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent2_pre_trade_balance = w3.eth.getBalance(agent2.address)
    logger.info("[{}]: {}".format(agent2.address, agent2_pre_trade_balance))

    # fund agent1 and agent2 with tokens
    new_token_id = generate_id(FT, 86)
    new_token_quantity = 5

    storage_contract.createSingle(
        agent1.address,
        new_token_id,
        "http://serverWithTheJsonDetailsOfTheItem",
        transact={"from": owner},
    )

    storage_contract.mint(
        agent1.address, new_token_id, new_token_quantity, transact={"from": owner}
    )

    # prepare terms of trade
    from_hash = storage_contract.getAddress(agent1.address)
    to_hash = storage_contract.getAddress(agent2.address)
    _from_value = 2
    _to_value = 5
    value_eth = 1
    nonce = randrange(0, 10000000)
    while storage_contract.is_nonce_used(agent1.address, nonce):
        nonce = randrange(0, 10000000)
    data = b"hello"
    hashed_data = get_single_hash(
        from_hash, to_hash, new_token_id, _from_value, _to_value, value_eth, nonce
    )

    # agent2 to sign data
    signature_object = agent2.signHash(hashed_data)
    signature = bytes(signature_object["signature"])
    assert (
        w3.eth.account.recoverHash(hashed_data, signature=signature) == agent2.address
    )

    # assert tx fails (due to positive from and to value)
    assert_tx_failed(
        lambda: storage_contract.trade(
            agent1.address,
            agent2.address,
            new_token_id,
            _from_value,
            _to_value,
            value_eth,
            nonce,
            signature,
            data,
            transact={"value": 1, "from": agent1.address},
        )
    )


def test_tradeBatch(w3, storage_contract, get_logs):
    """Test the tradeBatch functionality of the smart contract."""
    # create entities
    owner = w3.eth.accounts[0]
    agent1 = w3.eth.account.from_key(private_key=PRIVATE_KEY_1)
    agent2 = w3.eth.account.from_key(private_key=PRIVATE_KEY_2)

    # fund agent1 and agent2 with ether
    w3.eth.sendTransaction(
        {"to": agent1.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent1_pre_trade_balance = w3.eth.getBalance(agent1.address)
    logger.info("[{}]: {}".format(agent1.address, agent1_pre_trade_balance))
    w3.eth.sendTransaction(
        {"to": agent2.address, "from": w3.eth.coinbase, "value": 10 ** 9 * 2}
    )
    agent2_pre_trade_balance = w3.eth.getBalance(agent2.address)
    logger.info("[{}]: {}".format(agent2.address, agent2_pre_trade_balance))

    # fund agent1 and agent2 with tokens
    new_batch_token_ids = []
    for i in range(100, 110):
        new_batch_token_ids.append(generate_id(FT, i))
    new_batch_token_quantities = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]

    storage_contract.createBatch(
        agent1.address, new_batch_token_ids, transact={"from": owner}
    )

    storage_contract.mintBatch(
        agent1.address,
        new_batch_token_ids,
        new_batch_token_quantities,
        transact={"from": owner},
    )

    storage_contract.createBatch(
        agent2.address, new_batch_token_ids, transact={"from": owner}
    )

    storage_contract.mintBatch(
        agent2.address,
        new_batch_token_ids,
        new_batch_token_quantities,
        transact={"from": owner},
    )

    # prepare terms of trade
    from_hash = storage_contract.getAddress(agent1.address)
    to_hash = storage_contract.getAddress(agent2.address)
    _from_values = [2, 0, 2, 0, 1, 2, 3, 5, 2, 3]
    _to_values = [0, 1, 0, 2, 0, 0, 0, 0, 0, 0]
    value_eth = 1
    nonce = randrange(0, 10000000)
    while storage_contract.is_nonce_used(agent1.address, nonce):
        nonce = randrange(0, 10000000)
    data = b"hello"
    hashed_data = get_hash(
        from_hash,
        to_hash,
        new_batch_token_ids,
        _from_values,
        _to_values,
        value_eth,
        nonce,
    )

    # agent2 to sign data
    signature_dict = agent2.signHash(hashed_data)
    signature = bytes(signature_dict["signature"])
    assert (
        w3.eth.account.recoverHash(hashed_data, signature=signature) == agent2.address
    )

    # agent1 to submit transaction
    tx_hash = storage_contract.tradeBatch(
        agent1.address,
        agent2.address,
        new_batch_token_ids,
        _from_values,
        _to_values,
        value_eth,
        nonce,
        signature,
        data,
        transact={"value": value_eth, "from": agent1.address},
    )

    # assert correctness of logs
    logs = get_logs(tx_hash, storage_contract, "TransferBatch")
    assert len(logs) > 0
    logger.info(logs)
    args = logs[0].args
    logger.info(args)
    assert args._from == agent1.address
    assert args._to == agent2.address
    assert args._ids == new_batch_token_ids
    assert args._values == _from_values

    # assert correctness of final eth balances
    assert w3.eth.getBalance(agent2.address) == value_eth + agent2_pre_trade_balance
    assert w3.eth.getBalance(agent1.address) == agent1_pre_trade_balance - value_eth

    # assert correctness of final token balances
    balances = storage_contract.balanceOfBatch(
        [agent1.address] * 10, new_batch_token_ids
    )
    for i in range(10):
        new_batch_token_quantities[i] -= _from_values[i]
        new_batch_token_quantities[i] += _to_values[i]
    assert balances == new_batch_token_quantities


def get_hash(_from, _to, _ids, _from_values, _to_values, _value_eth, _nonce) -> bytes:
    """Generate a hash mirroring the way we are creating this in the contract."""
    aggregate_hash = keccak256(
        b"".join(
            [
                _ids[0].to_bytes(32, "big"),
                _from_values[0].to_bytes(32, "big"),
                _to_values[0].to_bytes(32, "big"),
            ]
        )
    )
    for i in range(len(_ids)):
        if not i == 0:
            aggregate_hash = keccak256(
                b"".join(
                    [
                        aggregate_hash,
                        _ids[i].to_bytes(32, "big"),
                        _from_values[i].to_bytes(32, "big"),
                        _to_values[i].to_bytes(32, "big"),
                    ]
                )
            )
    m_list = []
    m_list.append(_from)
    m_list.append(_to)
    m_list.append(aggregate_hash)
    m_list.append(_value_eth.to_bytes(32, "big"))
    m_list.append(_nonce.to_bytes(32, "big"))
    return keccak256(b"".join(m_list))


def get_hash_old(
    _from, _to, _ids, _from_values, _to_values, _value_eth, _nonce
) -> bytes:
    """Generate a hash mirroring the way we are creating this in the contract."""
    m_list = []
    m_list.append(_from)
    m_list.append(_to)
    m_list.extend(_id.to_bytes(32, "big") for _id in _ids)
    m_list.extend(_from_value.to_bytes(32, "big") for _from_value in _from_values)
    m_list.extend(_to_value.to_bytes(32, "big") for _to_value in _to_values)
    m_list.append(_value_eth.to_bytes(32, "big"))
    m_list.append(_nonce.to_bytes(32, "big"))
    return keccak256(b"".join(m_list))


def get_single_hash(
    _from, _to, _id, _from_value, _to_value, _value_eth, _nonce
) -> bytes:
    """Generate a hash mirroring the way we are creating this in the contract."""
    return keccak256(
        b"".join(
            [
                _from,
                _to,
                _id.to_bytes(32, "big"),
                _from_value.to_bytes(32, "big"),
                _to_value.to_bytes(32, "big"),
                _value_eth.to_bytes(32, "big"),
                _nonce.to_bytes(32, "big"),
            ]
        )
    )


def decode_id(_id):
    """Decode the id of a token to find if it is NFT or FT."""
    # x >> y: returns x with the bits shifted to the right by y places, which is equivalent to dividing x by 2**y.
    decoded_token_id = _id >> 128
    decoded_index = _id % 2 ** 128
    logger.info(decoded_token_id)
    return decoded_index, decoded_token_id
