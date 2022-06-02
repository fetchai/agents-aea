# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
"""This module contains a test for aea.context."""
import os
from unittest.mock import Mock

from aea_ledger_fetchai import FetchAICrypto

from aea.context.base import AgentContext
from aea.identity.base import Identity


def test_agent_context():
    """Test the agent context."""
    agent_name = "name"
    address = "address"
    addresses = {FetchAICrypto.identifier: address}
    public_key = "public_key"
    public_keys = {FetchAICrypto.identifier: public_key}
    identity = Identity(
        agent_name,
        addresses=addresses,
        public_keys=public_keys,
        default_address_key=FetchAICrypto.identifier,
    )
    connection_status = "connection_status_stub"
    outbox = "outbox_stub"
    decision_maker_message_queue = "decision_maker_message_queue_stub"
    decision_maker_handler_context = "decision_maker_handler_context_stub"
    task_manager = "task_manager_stub"
    default_connection = "default_connection_stub"
    default_routing = "default_routing_stub"
    search_service_address = "search_service_address_stub"
    decision_maker_address = "decision_maker_address_stub"
    value = "some_value"
    kwargs = {"some_key": value}
    default_ledger_id = "fetchai"
    currency_denominations = {}
    data_dir = os.getcwd()

    send_to_skill = Mock()

    def storage_callable_():
        pass

    ac = AgentContext(
        identity=identity,
        connection_status=connection_status,
        outbox=outbox,
        decision_maker_message_queue=decision_maker_message_queue,
        decision_maker_handler_context=decision_maker_handler_context,
        task_manager=task_manager,
        default_ledger_id=default_ledger_id,
        currency_denominations=currency_denominations,
        default_connection=default_connection,
        default_routing=default_routing,
        search_service_address=search_service_address,
        decision_maker_address=decision_maker_address,
        storage_callable=storage_callable_,
        data_dir=data_dir,
        send_to_skill=send_to_skill,
        **kwargs
    )

    assert ac.data_dir == data_dir
    assert ac.shared_state == {}
    assert ac.identity == identity
    assert ac.agent_name == identity.name
    assert ac.address == identity.address
    assert ac.addresses == identity.addresses
    assert ac.public_key == identity.public_key
    assert ac.public_keys == identity.public_keys
    assert ac.connection_status == connection_status
    assert ac.outbox == outbox
    assert ac.decision_maker_message_queue == decision_maker_message_queue
    assert ac.decision_maker_handler_context == decision_maker_handler_context
    assert ac.task_manager == task_manager
    assert ac.default_ledger_id == default_ledger_id
    assert ac.currency_denominations == currency_denominations
    assert ac.default_connection == default_connection
    assert ac.default_routing == default_routing
    assert ac.search_service_address == search_service_address
    assert ac.namespace.some_key == value
    assert ac.decision_maker_address == decision_maker_address
    assert ac.storage == storage_callable_()

    ac.send_to_skill("test")
    send_to_skill.assert_called()
