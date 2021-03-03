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
"""This module contains the tests of the yoti connection module."""
import asyncio
import logging
from typing import cast
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest

from aea.mail.base import Envelope
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue

from packages.fetchai.connections.yoti import connection as yoti_connection
from packages.fetchai.connections.yoti.connection import YotiConnection
from packages.fetchai.protocols.yoti.dialogues import YotiDialogue
from packages.fetchai.protocols.yoti.dialogues import YotiDialogues as BaseYotiDialogues
from packages.fetchai.protocols.yoti.message import YotiMessage


SKILL_ID = "some/skill:0.1.0"


class FakeYotiClientOk:
    """Test yoti client."""

    def __init__(self, *args, **kwargs):
        """Init client."""

    def callable(self, *args):
        """Some callable."""
        m = Mock()
        m.sources = []
        m.verifiers = []
        return m

    def get_activity_details(self, *args):
        """Get activity details."""
        activity_details = Mock()
        activity_details.profile.attributes = {}
        activity_details.profile.a = self.callable
        return activity_details


class FakeYotiClientBadProfile(FakeYotiClientOk):
    """Get a bad profile."""

    def get_activity_details(self, *args):
        """Get activity details."""
        activity_details = Mock()
        activity_details.profile = None
        return activity_details


class YotiDialogues(BaseYotiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The yoti connection maintains the dialogue on behalf of the yoti server
            return YotiDialogue.Role.AGENT

        BaseYotiDialogues.__init__(
            self,
            self_address=SKILL_ID,
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


mock_conf = Mock()
mock_conf.public_id = YotiConnection.connection_id
mock_conf.config = {"yoti_client_sdk_id": "1", "yoti_key_file_path": 1}


@pytest.mark.asyncio
async def test_yoti_profile_ok():
    """Test mesasge processed ok."""
    with patch.object(yoti_connection, "YotiClient", FakeYotiClientOk):
        con = YotiConnection(
            configuration=mock_conf, data_dir=MagicMock(), logger=logging.getLogger()
        )
        await con.connect()
        assert con.is_connected

        dialogues = YotiDialogues()

        message, _ = dialogues.create(
            str(con.connection_id),
            performative=YotiMessage.Performative.GET_PROFILE,
            token=str(uuid4()),
            dotted_path="",
        )
        envelope = Envelope(to=str(con.connection_id), sender=SKILL_ID, message=message)
        await con.send(envelope)
        resp_envelope = await asyncio.wait_for(con.receive(), timeout=1)
        assert (
            cast(YotiMessage, resp_envelope.message.performative)
            == YotiMessage.Performative.PROFILE
        )

        message, _ = dialogues.create(
            str(con.connection_id),
            performative=YotiMessage.Performative.GET_PROFILE,
            token=str(uuid4()),
            dotted_path="a",
            args=("1",),
        )
        envelope = Envelope(to=str(con.connection_id), sender=SKILL_ID, message=message)
        await con.send(envelope)
        resp_envelope = await asyncio.wait_for(con.receive(), timeout=1)
        assert (
            cast(YotiMessage, resp_envelope.message.performative)
            == YotiMessage.Performative.PROFILE
        )

        await con.disconnect()
        assert con.is_disconnected


@pytest.mark.asyncio
async def test_yoti_profile_error_on_handle():
    """Test error message on bad provile."""
    with patch.object(
        yoti_connection, "YotiClient", FakeYotiClientBadProfile,
    ):
        con = YotiConnection(
            configuration=mock_conf, data_dir=MagicMock(), logger=logging.getLogger()
        )
        await con.connect()
        dialogues = YotiDialogues()

        message, _ = dialogues.create(
            str(con.connection_id),
            performative=YotiMessage.Performative.GET_PROFILE,
            token=str(uuid4()),
            dotted_path="",
        )
        envelope = Envelope(to=str(con.connection_id), sender=SKILL_ID, message=message)
        await con.send(envelope)
        resp_envelope = await asyncio.wait_for(con.receive(), timeout=1)
        assert (
            cast(YotiMessage, resp_envelope.message.performative)
            == YotiMessage.Performative.ERROR
        )
        await con.disconnect()


def test_empty_config():
    """Test no sdk or token provided."""
    mock_conf = Mock()
    mock_conf.public_id = YotiConnection.connection_id
    mock_conf.config = {}
    with pytest.raises(ValueError, match="Missing configuration."):
        YotiConnection(configuration=mock_conf, data_dir=MagicMock())


class TestMisc:
    """Misc tests."""

    def setup(self):
        """Setup test case."""
        with patch.object(yoti_connection, "YotiClient", FakeYotiClientOk):
            self.con = YotiConnection(
                configuration=mock_conf,
                data_dir=MagicMock(),
                logger=logging.getLogger(),
            )
        self.dialogues = YotiDialogues()
        self.message, self.dialogue = self.dialogues.create(
            str(self.con.connection_id),
            performative=YotiMessage.Performative.GET_PROFILE,
            token=str(uuid4()),
            dotted_path="a",
            args=tuple(),
        )
        self.envelope = Envelope(
            to=str(self.con.connection_id), sender=SKILL_ID, message=self.message
        )

    def test_yoti_no_response_from_handler(self):
        """Test yoti handler returns no response."""
        with patch.object(self.con, "get_profile", return_value=None):
            self.con.dispatch(self.envelope)

    def test_no_handler(self):
        """Test bad peroformative for get handler."""
        with pytest.raises(Exception, match="Performative not recognized."):
            self.con.get_handler("some")

    def test_get_no_profile_data(self):
        """Test no profile data returned."""
        with patch.object(self.con._client, "get_activity_details", return_value=None):
            resp = self.con.get_profile(self.message, self.dialogue)

        assert resp
        assert resp.error_code == 500
        assert resp.error_msg == "No activity_details returned"

    def test_get_attribute(self):
        """Test get not callable attribute of profile."""
        activity_details = Mock()
        activity_details.profile.attributes = {}
        activity_details.profile.a.sources = []
        activity_details.profile.a.verifiers = []

        with patch.object(
            self.con._client, "get_activity_details", return_value=activity_details
        ):
            resp = self.con.get_profile(self.message, self.dialogue)

        assert resp
        assert resp.performative == YotiMessage.Performative.PROFILE
