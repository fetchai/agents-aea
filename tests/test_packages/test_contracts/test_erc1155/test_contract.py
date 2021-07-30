# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""The tests module contains the tests of the packages/contracts/erc1155 dir."""

import re
import time
from pathlib import Path
from typing import cast

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAIApi, FetchAICrypto

from aea.test_tools.test_contract import BaseContractTestCase

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract

from tests.conftest import (
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_ADDRESS_TWO,
    ETHEREUM_PRIVATE_KEY_PATH,
    ETHEREUM_PRIVATE_KEY_TWO_PATH,
    ETHEREUM_TESTNET_CONFIG,
    FETCHAI_TESTNET_CONFIG,
    MAX_FLAKY_RERUNS,
    ROOT_DIR,
    UseGanache,
)


@pytest.mark.ledger
class TestERC1155ContractEthereum(BaseContractTestCase, UseGanache):
    """Test the ERC1155 contract on Ethereum."""

    ledger_identifier = EthereumCrypto.identifier
    path_to_contract = Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")

    @classmethod
    def setup(cls):
        """Setup."""
        super().setup(
            ledger_config=ETHEREUM_TESTNET_CONFIG,
            deployer_private_key_path=ETHEREUM_PRIVATE_KEY_PATH,
            item_owner_private_key_path=ETHEREUM_PRIVATE_KEY_TWO_PATH,
        )

        cls.token_ids_a = [
            340282366920938463463374607431768211456,
            340282366920938463463374607431768211457,
            340282366920938463463374607431768211458,
            340282366920938463463374607431768211459,
            340282366920938463463374607431768211460,
            340282366920938463463374607431768211461,
            340282366920938463463374607431768211462,
            340282366920938463463374607431768211463,
            340282366920938463463374607431768211464,
            340282366920938463463374607431768211465,
        ]

        cls.token_id_b = 680564733841876926926749214863536422912

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """
        Finish deploying contract.

        :return: contract address
        """
        contract_address = cls.ledger_api.get_contract_address(
            cls.deployment_tx_receipt
        )

        if contract_address is None:
            raise ValueError("Contract address not found!")  # pragma: nocover

        return contract_address

    def test_generate_token_ids(self):
        """Test the generate_token_ids method of the ERC1155 contract."""
        # setup
        nft_token_type = 1
        nb_tokens = 2
        expected_toke_ids = [
            340282366920938463463374607431768211456,
            340282366920938463463374607431768211457,
        ]

        # operation
        actual_toke_ids = self.contract.generate_token_ids(nft_token_type, nb_tokens)

        # after
        assert actual_toke_ids == expected_toke_ids

    def test_generate_id(self):
        """Test the _generate_id method of the ERC1155 contract."""
        # setup
        ft_token_type = 2
        index = 0
        expected_toke_id = 680564733841876926926749214863536422912

        # operation
        actual_toke_id = self.contract._generate_id(index, ft_token_type)

        # after
        assert actual_toke_id == expected_toke_id

    def test_get_create_batch_transaction(self):
        """Test the get_create_batch_transaction method of the ERC1155 contract."""
        # operation
        tx = self.contract.get_create_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            token_ids=self.token_ids_a,
        )

        # after
        assert len(tx) == 7
        assert all(
            key in tx
            for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to", "data"]
        )
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

    def test_get_create_single_transaction(self):
        """Test the get_create_single_transaction method of the ERC1155 contract."""
        # operation
        tx = self.contract.get_create_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            token_id=self.token_id_b,
        )

        # after
        assert len(tx) == 7
        assert all(
            key in tx
            for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to", "data"]
        )
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

    def test_get_mint_batch_transaction(self):
        """Test the get_mint_batch_transaction method of the ERC1155 contract."""
        # operation
        tx = self.contract.get_mint_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.item_owner_crypto.address,
            token_ids=self.token_ids_a,
            mint_quantities=[1] * len(self.token_ids_a),
        )

        # after
        assert len(tx) == 7
        assert all(
            key in tx
            for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to", "data"]
        )
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

    def test_validate_mint_quantities(self):
        """Test the validate_mint_quantities method of the ERC1155 contract."""
        # Valid NFTs
        self.contract.validate_mint_quantities(
            token_ids=self.token_ids_a, mint_quantities=[1] * len(self.token_ids_a),
        )

        # Valid FTs
        token_id = 680564733841876926926749214863536422912
        mint_quantity = 1
        self.contract.validate_mint_quantities(
            token_ids=[token_id], mint_quantities=[mint_quantity],
        )

        # Invalid NFTs
        token_id = self.token_ids_a[0]
        mint_quantity = 2
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Cannot mint NFT (token_id={token_id}) with mint_quantity more than 1 (found={mint_quantity})"
            ),
        ):
            self.contract.validate_mint_quantities(
                token_ids=[token_id], mint_quantities=[mint_quantity],
            )

        # Invalid: neither NFT nor FT
        token_id = 1020847100762815390390123822295304634368
        mint_quantity = 1
        with pytest.raises(
            ValueError,
            match=re.escape(
                f"The token type must be 1 or 2. Found type=3 for token_id={token_id}"
            ),
        ):
            self.contract.validate_mint_quantities(
                token_ids=[token_id], mint_quantities=[mint_quantity],
            )

    def test_decode_id(self):
        """Test the decode_id method of the ERC1155 contract."""
        # FT
        expected_token_type = 2
        token_id = 680564733841876926926749214863536422912
        actual_token_type = self.contract.decode_id(token_id)
        assert actual_token_type == expected_token_type

        # NFT
        expected_token_type = 1
        token_id = 340282366920938463463374607431768211456
        actual_token_type = self.contract.decode_id(token_id)
        assert actual_token_type == expected_token_type

    def test_get_mint_single_transaction(self):
        """Test the get_mint_single_transaction method of the ERC1155 contract."""
        # operation
        tx = self.contract.get_mint_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.item_owner_crypto.address,
            token_id=self.token_id_b,
            mint_quantity=1,
        )

        # after
        assert len(tx) == 7
        assert all(
            key in tx
            for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to", "data"]
        )
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

    def test_get_balance(self):
        """Test the get_balance method of the ERC1155 contract."""
        # operation
        result = self.contract.get_balance(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            agent_address=self.item_owner_crypto.address,
            token_id=self.token_id_b,
        )

        # after
        assert "balance" in result
        assert result["balance"][self.token_id_b] == 0

    def test_get_balances(self):
        """Test the get_balances method of the ERC1155 contract."""
        # operation
        result = self.contract.get_balances(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            agent_address=self.item_owner_crypto.address,
            token_ids=self.token_ids_a,
        )

        # after
        assert "balances" in result
        assert all(result["balances"][token_id] == 0 for token_id in self.token_ids_a)

    def test_get_hash_single(self):
        """Test the get_hash_single method of the ERC1155 contract."""
        # operation
        result = self.contract.get_hash_single(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            from_address=self.deployer_crypto.address,
            to_address=self.item_owner_crypto.address,
            token_id=self.token_id_b,
            from_supply=0,
            to_supply=10,
            value=1,
            trade_nonce=1,
        )

        # after
        assert isinstance(result, bytes)

    def test_get_hash_batch(self):
        """Test the get_hash_batch method of the ERC1155 contract."""
        # operation
        result = self.contract.get_hash_batch(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            from_address=self.deployer_crypto.address,
            to_address=self.item_owner_crypto.address,
            token_ids=self.token_ids_a,
            from_supplies=[0, 1, 0, 0, 1, 0, 0, 0, 0, 1],
            to_supplies=[0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            value=1,
            trade_nonce=1,
        )

        # after
        assert isinstance(result, bytes)

    def test_generate_trade_nonce(self):
        """Test the generate_trade_nonce method of the ERC1155 contract."""
        # operation
        result = self.contract.generate_trade_nonce(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            agent_address=self.item_owner_crypto.address,
        )

        # after
        assert "trade_nonce" in result
        assert isinstance(result["trade_nonce"], int)

    @pytest.mark.integration
    def test_helper_methods_and_get_transactions(self):
        """Test helper methods and get transactions."""
        expected_a = [
            340282366920938463463374607431768211456,
            340282366920938463463374607431768211457,
            340282366920938463463374607431768211458,
            340282366920938463463374607431768211459,
            340282366920938463463374607431768211460,
            340282366920938463463374607431768211461,
            340282366920938463463374607431768211462,
            340282366920938463463374607431768211463,
            340282366920938463463374607431768211464,
            340282366920938463463374607431768211465,
        ]
        actual = self.contract.generate_token_ids(token_type=1, nb_tokens=10)
        assert expected_a == actual
        expected_b = [
            680564733841876926926749214863536422912,
            680564733841876926926749214863536422913,
        ]
        actual = self.contract.generate_token_ids(token_type=2, nb_tokens=2)
        assert expected_b == actual
        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api, deployer_address=ETHEREUM_ADDRESS_ONE
        )
        assert len(tx) == 6
        data = tx.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [key in tx for key in ["value", "from", "gas", "gasPrice", "nonce"]]
        ), "Error, found: {}".format(tx)
        tx = self.contract.get_create_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=ETHEREUM_ADDRESS_ONE,
            deployer_address=ETHEREUM_ADDRESS_ONE,
            token_ids=expected_a,
        )
        assert len(tx) == 7
        data = tx.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in tx
                for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]
            ]
        ), "Error, found: {}".format(tx)
        tx = self.contract.get_create_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=ETHEREUM_ADDRESS_ONE,
            deployer_address=ETHEREUM_ADDRESS_ONE,
            token_id=expected_b[0],
        )
        assert len(tx) == 7
        data = tx.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in tx
                for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]
            ]
        ), "Error, found: {}".format(tx)
        mint_quantities = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        tx = self.contract.get_mint_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=ETHEREUM_ADDRESS_ONE,
            deployer_address=ETHEREUM_ADDRESS_ONE,
            recipient_address=ETHEREUM_ADDRESS_ONE,
            token_ids=expected_a,
            mint_quantities=mint_quantities,
        )
        assert len(tx) == 7
        data = tx.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in tx
                for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]
            ]
        ), "Error, found: {}".format(tx)
        mint_quantity = 1
        tx = self.contract.get_mint_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=ETHEREUM_ADDRESS_ONE,
            deployer_address=ETHEREUM_ADDRESS_ONE,
            recipient_address=ETHEREUM_ADDRESS_ONE,
            token_id=expected_b[1],
            mint_quantity=mint_quantity,
        )
        assert len(tx) == 7
        data = tx.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in tx
                for key in ["value", "chainId", "gas", "gasPrice", "nonce", "to"]
            ]
        ), "Error, found: {}".format(tx)

    @pytest.mark.integration
    def test_get_single_atomic_swap(self):
        """Test get single atomic swap."""
        from_address = ETHEREUM_ADDRESS_ONE
        to_address = ETHEREUM_ADDRESS_TWO
        token_id = self.contract.generate_token_ids(token_type=2, nb_tokens=1)[0]
        from_supply = 0
        to_supply = 10
        value = 1
        trade_nonce = 1
        tx_hash = self.contract.get_hash_single(
            self.ledger_api,
            self.contract_address,
            from_address,
            to_address,
            token_id,
            from_supply,
            to_supply,
            value,
            trade_nonce,
        )
        assert isinstance(tx_hash, bytes)
        signature = self.deployer_crypto.sign_message(tx_hash)
        tx = self.contract.get_atomic_swap_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            from_address=from_address,
            to_address=to_address,
            token_id=token_id,
            from_supply=from_supply,
            to_supply=to_supply,
            value=value,
            trade_nonce=trade_nonce,
            signature=signature,
        )
        assert len(tx) == 8
        data = tx.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in tx
                for key in [
                    "value",
                    "chainId",
                    "gas",
                    "gasPrice",
                    "nonce",
                    "to",
                    "from",
                ]
            ]
        ), "Error, found: {}".format(tx)

    @pytest.mark.integration
    def test_get_batch_atomic_swap(self):
        """Test get batch atomic swap."""
        from_address = ETHEREUM_ADDRESS_ONE
        to_address = ETHEREUM_ADDRESS_TWO
        token_ids = self.contract.generate_token_ids(token_type=2, nb_tokens=10)
        from_supplies = [0, 1, 0, 0, 1, 0, 0, 0, 0, 1]
        to_supplies = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        value = 1
        trade_nonce = 1
        tx_hash = self.contract.get_hash_batch(
            self.ledger_api,
            self.contract_address,
            from_address,
            to_address,
            token_ids,
            from_supplies,
            to_supplies,
            value,
            trade_nonce,
        )
        assert isinstance(tx_hash, bytes)
        signature = self.deployer_crypto.sign_message(tx_hash)
        tx = self.contract.get_atomic_swap_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            from_address=from_address,
            to_address=to_address,
            token_ids=token_ids,
            from_supplies=from_supplies,
            to_supplies=to_supplies,
            value=value,
            trade_nonce=trade_nonce,
            signature=signature,
        )
        assert len(tx) == 8
        data = tx.pop("data")
        assert len(data) > 0 and data.startswith("0x")
        assert all(
            [
                key in tx
                for key in [
                    "value",
                    "chainId",
                    "gas",
                    "gasPrice",
                    "nonce",
                    "to",
                    "from",
                ]
            ]
        ), "Error, found: {}".format(tx)

    @pytest.mark.integration
    def test_full(self):
        """Setup."""
        # Test tokens IDs
        token_ids = self.contract.generate_token_ids(token_type=2, nb_tokens=10)

        # create
        tx = self.contract.get_create_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            token_ids=token_ids,
        )
        tx_signed = self.deployer_crypto.sign_transaction(tx)
        tx_receipt = self.ledger_api.send_signed_transaction(tx_signed)
        time.sleep(1)
        receipt = self.ledger_api.get_transaction_receipt(tx_receipt)
        assert self.ledger_api.is_transaction_settled(receipt)

        mint_quantities = [10] * len(token_ids)
        # mint
        tx = self.contract.get_mint_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.deployer_crypto.address,
            token_ids=token_ids,
            mint_quantities=mint_quantities,
        )
        tx_signed = self.deployer_crypto.sign_transaction(tx)
        tx_receipt = self.ledger_api.send_signed_transaction(tx_signed)
        time.sleep(1)
        receipt = self.ledger_api.get_transaction_receipt(tx_receipt)
        assert self.ledger_api.is_transaction_settled(receipt)

        tx = self.contract.get_mint_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.item_owner_crypto.address,
            token_ids=token_ids,
            mint_quantities=mint_quantities,
        )
        tx_signed = self.deployer_crypto.sign_transaction(tx)
        tx_receipt = self.ledger_api.send_signed_transaction(tx_signed)
        time.sleep(1)
        receipt = self.ledger_api.get_transaction_receipt(tx_receipt)
        assert self.ledger_api.is_transaction_settled(receipt)

        #  batch trade
        from_address = self.deployer_crypto.address
        to_address = self.item_owner_crypto.address
        from_supplies = [0, 1, 0, 0, 1, 0, 0, 0, 0, 1]
        to_supplies = [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        value = 0
        trade_nonce = 1
        tx_hash = self.contract.get_hash_batch(
            self.ledger_api,
            self.contract_address,
            from_address,
            to_address,
            token_ids,
            from_supplies,
            to_supplies,
            value,
            trade_nonce,
        )
        signature = self.item_owner_crypto.sign_message(
            tx_hash, is_deprecated_mode=True
        )
        tx = self.contract.get_atomic_swap_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            from_address=from_address,
            to_address=to_address,
            token_ids=token_ids,
            from_supplies=from_supplies,
            to_supplies=to_supplies,
            value=value,
            trade_nonce=trade_nonce,
            signature=signature,
        )
        tx_signed = self.deployer_crypto.sign_transaction(tx)
        tx_receipt = self.ledger_api.send_signed_transaction(tx_signed)
        time.sleep(1)
        receipt = self.ledger_api.get_transaction_receipt(tx_receipt)
        assert self.ledger_api.is_transaction_settled(receipt)


class TestCosmWasmContract(BaseContractTestCase):
    """Test the cosmwasm contract."""

    ledger_identifier = FetchAICrypto.identifier
    path_to_contract = Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")
    fund_from_faucet = True

    @classmethod
    def setup(cls):
        """Setup."""
        # Test tokens IDs
        super().setup(ledger_config=FETCHAI_TESTNET_CONFIG)
        cls.token_ids_a = [
            340282366920938463463374607431768211456,
            340282366920938463463374607431768211457,
            340282366920938463463374607431768211458,
            340282366920938463463374607431768211459,
            340282366920938463463374607431768211460,
            340282366920938463463374607431768211461,
            340282366920938463463374607431768211462,
            340282366920938463463374607431768211463,
            340282366920938463463374607431768211464,
            340282366920938463463374607431768211465,
        ]

        cls.token_id_b = 680564733841876926926749214863536422912

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """
        Finish deploying contract.

        :return: contract address
        """
        code_id = cast(FetchAIApi, cls.ledger_api).get_code_id(
            cls.deployment_tx_receipt
        )

        assert code_id is not None
        assert code_id == cast(FetchAIApi, cls.ledger_api).get_last_code_id()

        # Init contract
        tx = cast(ERC1155Contract, cls.contract).get_deploy_transaction(
            ledger_api=cls.ledger_api,
            deployer_address=cls.deployer_crypto.address,
            code_id=code_id,
            init_msg={},
            tx_fee=0,
            amount=0,
            label="ERC1155",
            gas=1000000,
        )

        if tx is None:
            raise ValueError("Deploy transaction not found!")  # pragma: nocover
        
        tx_receipt = cls.sign_send_confirm_receipt_transaction(
            tx, cls.ledger_api, cls.deployer_crypto
        )

        contract_address = cls.ledger_api.get_contract_address(tx_receipt)

        if contract_address is None:
            raise ValueError("Contract address not found!")  # pragma: nocover

        if contract_address != cast(
            FetchAIApi, cls.ledger_api
        ).get_last_contract_address(code_id):
            raise ValueError("Contract address not valid!")  # pragma: nocover

        return contract_address

    @pytest.mark.integration
    @pytest.mark.ledger
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_create_and_mint_and_balances(self):
        """Test cosmwasm contract create, mint and balances functionalities."""
        # Create single token
        tx = self.contract.get_create_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            token_id=self.token_id_b,
        )
        assert len(tx) == 6
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

        # Create batch of tokens
        tx = self.contract.get_create_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            token_ids=self.token_ids_a,
        )
        assert len(tx) == 6
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

        # Mint single token
        tx = self.contract.get_mint_single_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.item_owner_crypto.address,
            token_id=self.token_id_b,
            mint_quantity=1,
        )
        assert len(tx) == 6
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

        # Get balance of single token
        res = self.contract.get_balance(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            agent_address=self.item_owner_crypto.address,
            token_id=self.token_id_b,
        )
        assert "balance" in res
        assert res["balance"][self.token_id_b] == 1

        # Mint batch of tokens
        tx = self.contract.get_mint_batch_transaction(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            deployer_address=self.deployer_crypto.address,
            recipient_address=self.item_owner_crypto.address,
            token_ids=self.token_ids_a,
            mint_quantities=[1] * len(self.token_ids_a),
        )
        assert len(tx) == 6
        self.sign_send_confirm_receipt_transaction(
            tx, self.ledger_api, self.deployer_crypto
        )

        # Get balances of multiple tokens
        res = self.contract.get_balances(
            ledger_api=self.ledger_api,
            contract_address=self.contract_address,
            agent_address=self.item_owner_crypto.address,
            token_ids=self.token_ids_a,
        )
        assert "balances" in res
        assert res["balances"] == {token_id: 1 for token_id in self.token_ids_a}

    @pytest.mark.integration
    @pytest.mark.ledger
    def test_cosmwasm_unimplemented_exception_single_atomic_swap(self):
        """Test unimplemented exception single atomic swap."""
        pytest.raises(
            NotImplementedError,
            self.contract.get_atomic_swap_single_transaction,
            self.ledger_api,
            contract_address=None,
            from_address=None,
            to_address=None,
            token_id=0,
            from_supply=0,
            to_supply=0,
            value=0,
            trade_nonce=0,
            signature="",
        )

    @pytest.mark.integration
    @pytest.mark.ledger
    def test_cosmwasm_unimplemented_exception_batch_atomic_swap(self):
        """Test unimplemented exception batch atomic swap."""
        pytest.raises(
            NotImplementedError,
            self.contract.get_atomic_swap_batch_transaction,
            self.ledger_api,
            contract_address=None,
            from_address=None,
            to_address=None,
            token_ids=[0],
            from_supplies=[0],
            to_supplies=[0],
            value=0,
            trade_nonce=0,
            signature="",
        )
