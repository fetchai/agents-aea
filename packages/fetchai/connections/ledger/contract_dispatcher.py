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

"""This module contains the implementation of the contract API request dispatcher."""
import inspect
import logging
from collections.abc import Mapping
from typing import Any, Callable, Optional, Union, cast

from aea.common import JSONLike
from aea.contracts import Contract, contract_registry
from aea.crypto.base import LedgerApi
from aea.crypto.registries import Registry
from aea.exceptions import AEAException
from aea.helpers.transaction.base import RawMessage, RawTransaction, State
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import Dialogues as BaseDialogues

from packages.fetchai.connections.ledger.base import CONNECTION_ID, RequestDispatcher
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.contract_api.dialogues import ContractApiDialogue
from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)


_default_logger = logging.getLogger(
    "aea.packages.fetchai.connections.ledger.contract_dispatcher"
)


class ContractApiDialogues(BaseContractApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The ledger connection maintains the dialogue on behalf of the ledger
            return ContractApiDialogue.Role.LEDGER

        BaseContractApiDialogues.__init__(
            self,
            self_address=str(CONNECTION_ID),
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


class ContractApiRequestDispatcher(RequestDispatcher):
    """Implement the contract API request dispatcher."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the dispatcher."""
        logger = kwargs.pop("logger", None)
        logger = logger if logger is not None else _default_logger

        super().__init__(logger, *args, **kwargs)
        self._contract_api_dialogues = ContractApiDialogues()

    @property
    def dialogues(self) -> BaseDialogues:
        """Get the dialogues."""
        return self._contract_api_dialogues

    @property
    def contract_registry(self) -> Registry[Contract]:
        """Get the contract registry."""
        return contract_registry

    def get_ledger_id(self, message: Message) -> str:
        """Get the ledger id."""
        if not isinstance(message, ContractApiMessage):  # pragma: nocover
            raise ValueError("argument is not a ContractApiMessage instance.")
        message = cast(ContractApiMessage, message)
        return message.ledger_id

    def get_error_message(
        self, e: Exception, api: LedgerApi, message: Message, dialogue: BaseDialogue,
    ) -> ContractApiMessage:
        """
        Build an error message.

        :param e: the exception.
        :param api: the Ledger API.
        :param message: the request message.
        :param dialogue: the dialogue
        :return: an error message response.
        """
        response = cast(
            ContractApiMessage,
            dialogue.reply(
                performative=ContractApiMessage.Performative.ERROR,
                target_message=message,
                code=500,
                message=str(e),
                data=b"",
            ),
        )
        return response

    def dispatch_request(
        self,
        ledger_api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
        response_builder: Callable[
            [Union[bytes, JSONLike], ContractApiDialogue], ContractApiMessage
        ],
    ) -> ContractApiMessage:
        """
        Dispatch a request to a user-defined contract method.

        :param ledger_api: the ledger apis.
        :param message: the contract API request message.
        :param dialogue: the contract API dialogue.
        :param response_builder: callable that from bytes builds a contract API message.
        :return: the response message.
        """
        contract = self.contract_registry.make(message.contract_id)
        try:
            data = self._get_data(ledger_api, message, contract)
            response = response_builder(data, dialogue)
        except AEAException as e:
            self.logger.error(f"Exception during contract request: {str(e)}")
            response = self.get_error_message(e, ledger_api, message, dialogue)
        except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
            self.logger.error(
                f"An error occurred while processing the contract api request: '{str(e)}'."
            )
            response = self.get_error_message(e, ledger_api, message, dialogue)
        return response

    def get_state(
        self,
        ledger_api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_state'.

        :param ledger_api: the API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: the contract api message
        """

        def build_response(
            data: Union[bytes, JSONLike], dialogue: ContractApiDialogue
        ) -> ContractApiMessage:
            if not isinstance(data, Mapping):
                raise ValueError(
                    f"Invalid state type, got={type(data)}, expected={JSONLike}."
                )
            return cast(
                ContractApiMessage,
                dialogue.reply(
                    performative=ContractApiMessage.Performative.STATE,
                    state=State(message.ledger_id, data),
                ),
            )

        return self.dispatch_request(ledger_api, message, dialogue, build_response)

    def get_deploy_transaction(
        self,
        ledger_api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_raw_transaction'.

        :param ledger_api: the API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: the contract api message
        """

        def build_response(
            tx: Union[bytes, JSONLike], dialogue: ContractApiDialogue
        ) -> ContractApiMessage:
            if not isinstance(tx, Mapping):
                raise ValueError(
                    f"Invalid transaction type, got={type(tx)}, expected={JSONLike}."
                )
            return cast(
                ContractApiMessage,
                dialogue.reply(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    raw_transaction=RawTransaction(message.ledger_id, tx),
                ),
            )

        return self.dispatch_request(ledger_api, message, dialogue, build_response)

    def get_raw_transaction(
        self,
        ledger_api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_raw_transaction'.

        :param ledger_api: the API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: the contract api message
        """

        def build_response(
            tx: Union[bytes, JSONLike], dialogue: ContractApiDialogue
        ) -> ContractApiMessage:
            if isinstance(tx, bytes):
                raise ValueError(
                    f"Invalid transaction type, got={type(tx)}, expected={JSONLike}."
                )
            return cast(
                ContractApiMessage,
                dialogue.reply(
                    performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                    raw_transaction=RawTransaction(message.ledger_id, tx),
                ),
            )

        return self.dispatch_request(ledger_api, message, dialogue, build_response)

    def get_raw_message(
        self,
        ledger_api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_raw_message'.

        :param ledger_api: the ledger API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: the contract api message
        """

        def build_response(
            rm: Union[bytes, JSONLike], dialogue: ContractApiDialogue
        ) -> ContractApiMessage:
            if not isinstance(rm, bytes):
                raise ValueError(
                    f"Invalid message type, got={type(rm)}, expected=bytes."
                )
            return cast(
                ContractApiMessage,
                dialogue.reply(
                    performative=ContractApiMessage.Performative.RAW_MESSAGE,
                    raw_message=RawMessage(message.ledger_id, rm),
                ),
            )

        return self.dispatch_request(ledger_api, message, dialogue, build_response)

    def _get_data(
        self, api: LedgerApi, message: ContractApiMessage, contract: Contract,
    ) -> Union[bytes, JSONLike]:
        """Get the data from the contract method, either from the stub or from the callable specified by the message."""
        # first, check if the custom handler for this type of request has been implemented.
        data = self._call_stub(api, message, contract)
        if data is not None:
            return data

        # then, check if there is the handler for the provided callable.
        data = self._validate_and_call_callable(api, message, contract)
        return data

    @staticmethod
    def _call_stub(
        ledger_api: LedgerApi, message: ContractApiMessage, contract: Contract
    ) -> Optional[Union[bytes, JSONLike]]:
        """Try to call stub methods associated to the contract API request performative."""
        try:
            method: Callable = getattr(contract, message.performative.value)
            if message.performative in [
                ContractApiMessage.Performative.GET_STATE,
                ContractApiMessage.Performative.GET_RAW_MESSAGE,
                ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ]:
                args, kwargs = (
                    [ledger_api, message.contract_address],
                    message.kwargs.body,
                )
            elif message.performative in [  # pragma: nocover
                ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ]:
                args, kwargs = [ledger_api], message.kwargs.body
            else:  # pragma: nocover
                raise AEAException(f"Unexpected performative: {message.performative}")
            data = method(*args, **kwargs)
            return data
        except (AttributeError, NotImplementedError):
            return None

    @staticmethod
    def _validate_and_call_callable(
        api: LedgerApi, message: ContractApiMessage, contract: Contract
    ) -> Union[bytes, JSONLike]:
        """
        Validate a Contract callable, given the performative.

        In particular:
        - if the performative is either 'get_state' or 'get_raw_transaction', the signature
          must accept ledger api as first argument and contract address as second argument,
          plus keyword arguments.
        - if the performative is either 'get_deploy_transaction' or 'get_raw_message', the signature
          must accept ledger api as first argument, plus keyword arguments.

        :param api: the ledger api object.
        :param message: the contract api request.
        :param contract: the contract instance.
        :return: the data generated by the method.
        """
        try:
            method_to_call = getattr(contract, message.callable)
        except AttributeError:
            raise AEAException(
                f"Cannot find {message.callable} in contract {type(contract)}"
            )
        full_args_spec = inspect.getfullargspec(method_to_call)
        if message.performative in [
            ContractApiMessage.Performative.GET_STATE,
            ContractApiMessage.Performative.GET_RAW_MESSAGE,
            ContractApiMessage.Performative.GET_RAW_TRANSACTION,
        ]:
            if len(full_args_spec.args) < 2:
                raise AEAException(
                    f"Expected two or more positional arguments, got {len(full_args_spec.args)}"
                )
            return method_to_call(api, message.contract_address, **message.kwargs.body)
        if message.performative in [
            ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
        ]:
            if len(full_args_spec.args) < 1:
                raise AEAException(
                    f"Expected one or more positional arguments, got {len(full_args_spec.args)}"
                )
            return method_to_call(api, **message.kwargs.body)
        raise AEAException(  # pragma: nocover
            f"Unexpected performative: {message.performative}"
        )
