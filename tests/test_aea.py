from aea.aea import AEA
from aea.mail.base import MailBox
from aea.protocols.base.message import Message
from aea.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from aea.channels.oef.connection import OEFConnection
from aea.channels.local.connection import LocalNode, OEFLocalConnection
from aea.protocols.base.serialization import ProtobufSerializer, JSONSerializer
from queue import Queue
import pytest


def test_initialiseAeA() :

	node = LocalNode()
	public_key_1 = "mailbox1"
	mailbox1 = MailBox(OEFLocalConnection(public_key_1, node))


	myAea = AEA("Agent0", mailbox1)

	assert myAea , "Agent is not inisialised"
	assert myAea.context, "Cannot access the Agent's Context"
	assert myAea.setup()

	#assert myAea.resources()
	
	

