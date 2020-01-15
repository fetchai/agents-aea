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

"""This module contains the tests for the FIPA protocol."""
import logging
from typing import cast, Tuple
from unittest import mock

import pytest

from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description, Query, Constraint, ConstraintType
from aea.mail.base import Envelope
from packages.fetchai.protocols.fipa.dialogues import FIPADialogues, FIPADialogue
from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer

logger = logging.getLogger(__name__)


# def test_fipa_cfp_serialization():
#     """Test that the serialization for the 'fipa' protocol works."""
#     query = Query([Constraint('something', ConstraintType('>', 1))])
#
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=0,
#                       performative=FIPAMessage.Performative.CFP,
#                       query=query)
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#
#     actual_msg = FIPASerializer().decode(actual_envelope.message)
#     expected_msg = msg
#     assert expected_msg == actual_msg
#
#     msg.set("query", "not_supported_query")
#     with pytest.raises(ValueError, match="Query type not supported:"):
#         FIPASerializer().encode(msg)
#
#
# def test_fipa_cfp_serialization_bytes():
#     """Test that the serialization - deserialization for the 'fipa' protocol works."""
#     query = b'Hello'
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=0,
#                       performative=FIPAMessage.Performative.CFP,
#                       query=query)
#     msg.counterparty = "sender"
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#
#     actual_msg = FIPASerializer().decode(actual_envelope.message)
#     actual_msg.counterparty = "sender"
#     expected_msg = msg
#     assert expected_msg == actual_msg
#
#     deserialised_msg = FIPASerializer().decode(envelope.message)
#     deserialised_msg.counterparty = "sender"
#     assert msg.get("performative") == deserialised_msg.get("performative")
#
#
# def test_fipa_propose_serialization():
#     """Test that the serialization for the 'fipa' protocol works."""
#     proposal = [
#         Description({"foo1": 1, "bar1": 2}),
#         Description({"foo2": 1, "bar2": 2}),
#     ]
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=0,
#                       performative=FIPAMessage.Performative.PROPOSE,
#                       proposal=proposal)
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#
#     actual_msg = FIPASerializer().decode(actual_envelope.message)
#     expected_msg = msg
#
#     p1 = actual_msg.get("proposal")
#     p2 = expected_msg.get("proposal")
#     assert p1[0].values == p2[0].values
#     assert p1[1].values == p2[1].values
#
#
# def test_fipa_accept_serialization():
#     """Test that the serialization for the 'fipa' protocol works."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=0,
#                       performative=FIPAMessage.Performative.ACCEPT)
#     msg.counterparty = "sender"
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#
#     actual_msg = FIPASerializer().decode(actual_envelope.message)
#     actual_msg.counterparty = "sender"
#     expected_msg = msg
#     assert expected_msg == actual_msg
#
#
# def test_performative_match_accept():
#     """Test the serialization - deserialization of the match_accept performative."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=1,
#                       performative=FIPAMessage.Performative.MATCH_ACCEPT)
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     msg.counterparty = "sender"
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#     deserialised_msg = FIPASerializer().decode(envelope.message)
#     assert msg.get("performative") == deserialised_msg.get("performative")
#
#
# def test_performative_accept_with_inform():
#     """Test the serialization - deserialization of the accept_with_address performative."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=1,
#                       performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
#                       info={"address": "dummy_address"})
#
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#     deserialised_msg = FIPASerializer().decode(envelope.message)
#     assert msg.get("performative") == deserialised_msg.get("performative")
#
#
# def test_performative_match_accept_with_inform():
#     """Test the serialization - deserialization of the match_accept_with_address performative."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=1,
#                       performative=FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM,
#                       info={"address": "dummy_address", "signature": "my_signature"})
#
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#     deserialised_msg = FIPASerializer().decode(envelope.message)
#     assert msg.get("performative") == deserialised_msg.get("performative")
#
#
# def test_performative_inform():
#     """Test the serialization-deserialization of the inform performative."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=1,
#                       performative=FIPAMessage.Performative.INFORM,
#                       info={"foo": "bar"})
#
#     msg_bytes = FIPASerializer().encode(msg)
#     envelope = Envelope(to="receiver",
#                         sender="sender",
#                         protocol_id=FIPAMessage.protocol_id,
#                         message=msg_bytes)
#     envelope_bytes = envelope.encode()
#
#     actual_envelope = Envelope.decode(envelope_bytes)
#     expected_envelope = envelope
#     assert expected_envelope == actual_envelope
#     deserialised_msg = FIPASerializer().decode(envelope.message)
#     assert msg.get("performative") == deserialised_msg.get("performative")
#
#
# def test_unknown_performative():
#     """Test that we raise an exception when the performative is unknown during check_consistency."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=1,
#                       performative=FIPAMessage.Performative.ACCEPT)
#     with mock.patch.object(FIPAMessage.Performative, "__eq__", return_value=False):
#         assert not msg.check_consistency()
#
#
# def test_performative_string_value():
#     """Test the string value of the performatives."""
#     assert str(FIPAMessage.Performative.CFP) == "cfp",\
#         "The str value must be cfp"
#     assert str(FIPAMessage.Performative.PROPOSE) == "propose",\
#         "The str value must be propose"
#     assert str(FIPAMessage.Performative.DECLINE) == "decline",\
#         "The str value must be decline"
#     assert str(FIPAMessage.Performative.ACCEPT) == "accept",\
#         "The str value must be accept"
#     assert str(FIPAMessage.Performative.MATCH_ACCEPT) == "match_accept",\
#         "The str value must be match_accept"
#     assert str(FIPAMessage.Performative.ACCEPT_W_INFORM) == "accept_w_inform", \
#         "The str value must be accept_w_inform"
#     assert str(FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM) == "match_accept_w_inform", \
#         "The str value must be match_accept_w_inform"
#     assert str(FIPAMessage.Performative.INFORM) == "inform", \
#         "The str value must be inform"
#
#
# def test_fipa_encoding_unknown_performative():
#     """Test that we raise an exception when the performative is unknown during encoding."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=1,
#                       performative=FIPAMessage.Performative.ACCEPT)
#
#     with pytest.raises(ValueError, match="Performative not valid:"):
#         with mock.patch.object(FIPAMessage.Performative, "__eq__", return_value=False):
#             FIPASerializer().encode(msg)
#
#
# def test_fipa_decoding_unknown_performative():
#     """Test that we raise an exception when the performative is unknown during decoding."""
#     msg = FIPAMessage(message_id=0,
#                       dialogue_reference=(str(0), ''),
#                       target=1,
#                       performative=FIPAMessage.Performative.ACCEPT)
#
#     encoded_msg = FIPASerializer().encode(msg)
#     with pytest.raises(ValueError, match="Performative not valid:"):
#         with mock.patch.object(FIPAMessage.Performative, "__eq__", return_value=False):
#             FIPASerializer().decode(encoded_msg)


class Test_dialogues:
    """Tests dialogues model from the packages protocols fipa."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.dialogues = FIPADialogues()

    # def test_dialogues(self):
    #     """Test the dialogues model."""
    #     result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter",
    #                                                   dialogue_opponent_addr="opponent",
    #                                                   is_seller=True)
    #     assert isinstance(result, FIPADialogue)
    #     result = self.dialogues.create_opponent_initiated(dialogue_opponent_addr="opponent",
    #                                                       dialogue_reference=(str(0), ''),
    #                                                       is_seller=False)
    #     assert isinstance(result, FIPADialogue)
    #     assert result.role == FIPADialogue.AgentRole.BUYER
    #     assert self.dialogues.dialogue_stats is not None
    #     self.dialogues.dialogue_stats.add_dialogue_endstate(FIPADialogue.EndState.SUCCESSFUL, is_self_initiated=True)
    #     self.dialogues.dialogue_stats.add_dialogue_endstate(FIPADialogue.EndState.DECLINED_CFP, is_self_initiated=False)
    #     assert self.dialogues.dialogue_stats.self_initiated == {FIPADialogue.EndState.SUCCESSFUL: 1,
    #                                                             FIPADialogue.EndState.DECLINED_PROPOSE: 0,
    #                                                             FIPADialogue.EndState.DECLINED_ACCEPT: 0,
    #                                                             FIPADialogue.EndState.DECLINED_CFP: 0}
    #     assert self.dialogues.dialogue_stats.other_initiated == {FIPADialogue.EndState.SUCCESSFUL: 0,
    #                                                              FIPADialogue.EndState.DECLINED_PROPOSE: 0,
    #                                                              FIPADialogue.EndState.DECLINED_ACCEPT: 0,
    #                                                              FIPADialogue.EndState.DECLINED_CFP: 1}
    #     assert self.dialogues.dialogues_as_seller is not None


    def test_dialogues_is_belonging_to_other_initiated_dialogue_label(self):
        """Test if the given dialogue belongs to an other initiated dialogue."""

        """Initialise a dialogue."""
        client_dialogue = self.dialogues.create_self_initiated(dialogue_opponent_addr="seller",
                                                               dialogue_starter_addr="client",
                                                               is_seller=True)

        """Register the dialogue to the dictionary of dialogues."""
        self.dialogues.dialogues[client_dialogue.dialogue_label] = cast(FIPADialogue, client_dialogue)

        """Send a message to the seller."""
        cfp_msg = FIPAMessage(message_id=1,
                              dialogue_reference=client_dialogue.dialogue_label.dialogue_reference,
                              target=0,
                              performative=FIPAMessage.Performative.CFP,
                              query=None)
        """Extends the outgoing list of messages."""
        client_dialogue.outgoing_extend(cfp_msg)

        """Creates a new dialogue for the seller side based on the income message."""
        seller_dialogue = self.dialogues.create_opponent_initiated(dialogue_opponent_addr="client",
                                                                   dialogue_reference=cfp_msg.dialogue_reference,
                                                                   is_seller=True)

        """Register the dialogue to the dictionary of dialogues."""
        self.dialogues.dialogues[seller_dialogue.dialogue_label] = cast(FIPADialogue, seller_dialogue)

        """Extend the incoming list of messages."""
        seller_dialogue.incoming_extend(cfp_msg)

        """Checks if the message we received is permitted for a new dialogue or if it is a registered dialogue."""
        assert self.dialogues.is_permitted_for_new_dialogue(seller_dialogue.last_incoming_message), \
            "Should be permitted since the first incoming msg is CFP"

        """Generate a proposal message to send to the client."""
        proposal = [
            Description({"foo1": 1, "bar1": 2}),
            Description({"foo2": 1, "bar2": 2}),
        ]
        proposal_msg = FIPAMessage(message_id=2,
                                 dialogue_reference=seller_dialogue.dialogue_label.dialogue_reference,
                                 target=1,
                                 performative=FIPAMessage.Performative.PROPOSE,
                                 proposal=proposal)

        proposal_msg.counterparty = "client"

        """Extends the outgoing list of messages."""
        seller_dialogue.outgoing_extend(proposal_msg)

        """Client received the message and we extend the incoming messages list."""
        client_dialogue.incoming_extend(proposal_msg)
        assert not self.dialogues.is_permitted_for_new_dialogue(client_dialogue.last_incoming_message),\
            "Should not be permitted since we registered the cfp message."

        response = self.dialogues.is_belonging_to_registered_dialogue(proposal_msg, agent_addr="opponent")
        assert response, "We expect the response from the function to be true."

#     def test_dialogues_is_belonging_to_self_initiated_dialogue_label(self):
#         """Test if the given dialogue belongs to self initiated dialogue."""
#         result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter", dialogue_opponent_addr="opponent",
#                                                       is_seller=False)
#         result.outgoing_extend(self.second_msg)
#         self_initiated_dialogue_label = DialogueLabel((str(0), ''), "opponent", "starter")
#         self.dialogues.dialogues[self_initiated_dialogue_label] = cast(FIPADialogue, result)
#         msg = FIPAMessage(message_id=3,
#                           dialogue_reference=(str(0), ''),
#                           target=2,
#                           performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
#                           info={"address": "dummy_address"})
#         msg.counterparty = "opponent"
#         response = self.dialogues.is_belonging_to_registered_dialogue(msg, agent_addr="starter")
#         assert response, "We expect the response from the function to be true"
#
#     def test_dialogues_is_belonging_to_alternative_initiated_dialogue_label(self):
#         """Test if the given dialogue belongs to alternative initiated dialogue label."""
#         result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter",
#                                                       dialogue_opponent_addr="opponent",
#                                                       is_seller=True)
#         result.outgoing_extend(self.second_msg)
#         alt_initiated_dialogue_label = DialogueLabel((str(0), ''), "opponent", "starter")
#         self.dialogues._initiated_dialogues[alt_initiated_dialogue_label] = cast(FIPADialogue, result)
#         msg = FIPAMessage(message_id=3,
#                           dialogue_reference=(str(5), 'starter'),
#                           target=2,
#                           performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
#                           info={"address": "dummy_address"})
#         msg.counterparty = "opponent"
#         response = self.dialogues.is_belonging_to_registered_dialogue(msg, agent_addr="starter")
#         assert response, "We expect the response from the function to be true."
#
#     def test_get_dialogues_other_initiated(self):
#         """Test the returned opponent initiated dialogues."""
#         opponent_result = self.dialogues.create_opponent_initiated(dialogue_opponent_addr="opponent",
#                                                                    dialogue_reference=(str(0), ''), is_seller=True)
#         msg = FIPAMessage(message_id=3,
#                           dialogue_reference=(str(0), ''),
#                           target=2,
#                           performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
#                           info={"address": "dummy_address"})
#
#         msg.counterparty = "opponent"
#         opponent_initiated_dialogue_label = DialogueLabel((str(0), ''), "opponent", "opponent")
#         self.dialogues.dialogues[opponent_initiated_dialogue_label] = cast(FIPADialogue, opponent_result)
#         opponent_retrieved_dialogue = self.dialogues.get_dialogue(fipa_msg=msg, agent_addr="starter")
#         assert opponent_retrieved_dialogue.is_self_initiated
#
#     def test_get_dialogues_self_initiated(self):
#         """Test the returned self initiated dialogues."""
#         result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter", dialogue_opponent_addr="opponent",
#                                                       is_seller=True)
#         result.outgoing_extend(self.second_msg)
#         self_initiated_dialogue_label = DialogueLabel((str(0), ''), "opponent", "starter")
#         self.dialogues.dialogues[self_initiated_dialogue_label] = cast(FIPADialogue, result)
#         msg = FIPAMessage(message_id=3,
#                           dialogue_reference=(str(0), ''),
#                           target=2,
#                           performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
#                           info={"address": "dummy_address"})
#         msg.counterparty = "opponent"
#         retrieved_dialogue = self.dialogues.get_dialogue(fipa_msg=msg, agent_addr="starter")
#         assert retrieved_dialogue.is_self_initiated
#
#     def test_get_dialogues_value_error(self):
#         """Test the value error of the get dialogues function."""
#         msg = FIPAMessage(message_id=3,
#                           dialogue_reference=(str(0), ''),
#                           target=2,
#                           performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
#                           info={"address": "dummy_address"})
#         msg.counterparty = "opponent"
#         with pytest.raises(ValueError, match="Should have found dialogue."):
#             self.dialogues.get_dialogue(fipa_msg=msg, agent_addr="unknown_addr")
#
#     def test_add_dialogue(self):
#         """Test the add functionality of the dialogues."""
#         result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter",
#                                                       dialogue_opponent_addr="opponent",
#                                                       is_seller=False)
#         self.dialogues._add(cast(FIPADialogue, result))
#         assert result in self.dialogues._dialogues_as_buyer.values()
#
#
# class Test_dialogue:
#     """Tests dialogue model from the protocols fipa."""
#
#     @classmethod
#     def setup_class(cls):
#         """Set up the test."""
#         cls.dialogues = FIPADialogues()
#         proposal = [
#             Description({"foo1": 1, "bar1": 2}),
#             Description({"foo2": 1, "bar2": 2}),
#         ]
#         cls.last_msg = FIPAMessage(message_id=2,
#                                    dialogue_reference=(str(0), ''),
#                                    target=1,
#                                    performative=FIPAMessage.Performative.PROPOSE,
#                                    proposal=proposal)
#
#     def test_dialogue_last_outgoing_message(self):
#         """Test the last outgoing message from the dialogue."""
#         result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter", dialogue_opponent_addr="opponent", is_seller=True)
#         assert isinstance(result, FIPADialogue)
#         assert result.is_seller
#
#         result.outgoing_extend(self.last_msg)
#         assert result.last_outgoing_message == self.last_msg, "The last message must be the same with the initialised message"
#
#     def test_the_message_is_valid_as_next_message(self):
#         """Test if the message we are trying to send is a valid one based on the sequence."""
#         result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter",
#                                                       dialogue_opponent_addr="opponent", is_seller=True)
#         result.outgoing_extend(self.last_msg)
#         assert isinstance(result, FIPADialogue)
#         msg = FIPAMessage(message_id=3,
#                           dialogue_reference=(str(0), ''),
#                           target=2,
#                           performative=FIPAMessage.Performative.ACCEPT_W_INFORM,
#                           info={"address": "dummy_address"})
#         response = result.is_valid_next_message(msg)
#         assert response
#
#     def test_assign_final_dialogue(self):
#         """Test the final_dialogue_label."""
#         result = self.dialogues.create_self_initiated(dialogue_starter_addr="starter",
#                                                       dialogue_opponent_addr="opponent", is_seller=True)
#         result.outgoing_extend(self.last_msg)
#         assert isinstance(result, FIPADialogue)
#         dialogue_label = DialogueLabel(dialogue_reference=("3", "0"), dialogue_opponent_addr="opponent",
#                                        dialogue_starter_addr="starter")
#         result.assign_final_dialogue_label(final_dialogue_label=dialogue_label)
#         assert result.dialogue_label.dialogue_starter_reference == dialogue_label.dialogue_starter_reference
