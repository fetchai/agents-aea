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

"""This module contains the tests of the messages module."""

from unittest import mock

import pytest

from packages.fetchai.protocols.tac.message import TACMessage
from packages.fetchai.protocols.tac.serialization import TACSerializer, _from_dict_to_pairs


def test_tac_message_instantiation():
    """Test instantiation of the tac message."""
    assert TACMessage(type=TACMessage.Type.REGISTER,
                      agent_name='some_name')
    assert TACMessage(type=TACMessage.Type.UNREGISTER)
    assert TACMessage(type=TACMessage.Type.TRANSACTION,
                      tx_id='some_id',
                      tx_sender_addr='some_address',
                      tx_counterparty_addr='some_other_address',
                      amount_by_currency_id={'FET': 10},
                      tx_sender_fee=10,
                      tx_counterparty_fee=10,
                      quantities_by_good_id={'good_1': 0, 'good_2': 10},
                      tx_nonce=1,
                      tx_sender_signature=b'some_signature',
                      tx_counterparty_signature=b'some_other_signature')
    assert TACMessage(type=TACMessage.Type.GET_STATE_UPDATE)
    assert TACMessage(type=TACMessage.Type.CANCELLED)
    assert TACMessage(type=TACMessage.Type.GAME_DATA,
                      amount_by_currency_id={'FET': 10},
                      exchange_params_by_currency_id={'FET': 10.0},
                      quantities_by_good_id={'good_1': 20, 'good_2': 15},
                      utility_params_by_good_id={'good_1': 30.0, 'good_2': 50.0},
                      tx_fee=20,
                      agent_addr_to_name={'agent_1': 'Agent one', 'agent_2': 'Agent two'},
                      good_id_to_name={'good_1': 'First good', 'good_2': 'Second good'},
                      version_id='game_version_1')
    assert TACMessage(type=TACMessage.Type.TRANSACTION_CONFIRMATION,
                      tx_id='some_id',
                      amount_by_currency_id={'FET': 10},
                      quantities_by_good_id={'good_1': 20, 'good_2': 15})
    assert TACMessage(type=TACMessage.Type.TAC_ERROR,
                      error_code=TACMessage.ErrorCode.GENERIC_ERROR)
    assert str(TACMessage.Type.REGISTER) == 'register'


def test_tac_serialization():
    """Test that the serialization for the tac message works."""
    msg = TACMessage(type=TACMessage.Type.REGISTER,
                     agent_name='some_name')
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TACMessage(type=TACMessage.Type.UNREGISTER)
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TACMessage(type=TACMessage.Type.TRANSACTION,
                     tx_id='some_id',
                     tx_sender_addr='some_address',
                     tx_counterparty_addr='some_other_address',
                     amount_by_currency_id={'FET': -10},
                     tx_sender_fee=10,
                     tx_counterparty_fee=10,
                     quantities_by_good_id={'good_1': 0, 'good_2': 10},
                     tx_nonce=1,
                     tx_sender_signature=b'some_signature',
                     tx_counterparty_signature=b'some_other_signature')
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TACMessage(type=TACMessage.Type.GET_STATE_UPDATE)
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TACMessage(type=TACMessage.Type.CANCELLED)
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TACMessage(type=TACMessage.Type.GAME_DATA,
                     amount_by_currency_id={'FET': 10},
                     exchange_params_by_currency_id={'FET': 10.0},
                     quantities_by_good_id={'good_1': 20, 'good_2': 15},
                     utility_params_by_good_id={'good_1': 30.0, 'good_2': 50.0},
                     tx_fee=20,
                     agent_addr_to_name={'agent_1': 'Agent one', 'agent_2': 'Agent two'},
                     good_id_to_name={'good_1': 'First good', 'good_2': 'Second good'},
                     version_id='game_version_1')
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    msg = TACMessage(type=TACMessage.Type.TRANSACTION_CONFIRMATION,
                     tx_id='some_id',
                     amount_by_currency_id={'FET': 10},
                     quantities_by_good_id={'good_1': 20, 'good_2': 15})
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg

    with pytest.raises(ValueError, match="Type not recognized."):
        with mock.patch('packages.fetchai.protocols.tac.message.TACMessage.Type') as mocked_type:
            mocked_type.TRANSACTION_CONFIRMATION.value = "unknown"
            TACSerializer().encode(msg)

    msg = TACMessage(type=TACMessage.Type.TAC_ERROR,
                     error_code=TACMessage.ErrorCode.GENERIC_ERROR,
                     info={'msg': "This is info msg."})
    msg_bytes = TACSerializer().encode(msg)
    actual_msg = TACSerializer().decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_from_dict_to_pairs():
    """Test the helper function _from_dict_to_pairs."""
    with pytest.raises(ValueError):
        test_items_dict = {"Test": b'UnsupportedType'}
        _from_dict_to_pairs(test_items_dict)
