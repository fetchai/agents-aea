from aea.mail.base import Envelope, MailBox, InBox, OutBox

from aea.protocols.base.message import Message
from aea.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from aea.channels.oef.connection import OEFConnection
from aea.channels.local.connection import LocalNode, OEFLocalConnection
from aea.protocols.base.serialization import ProtobufSerializer, JSONSerializer
from queue import Queue
import pytest


def test_envelope_initialisaztion() : 
	msg = Message(content='hello')
	message_bytes = ProtobufSerializer().encode(msg)
	envelope = Envelope(to="Agent1", sender="Agent0", protocol_id="my_own_protocol", message=message_bytes)
	
	envelope.to = "Agent1"
	envelope.sender = "Agent0"
	envelope.protocol_id = "my_own_protocol"
	envelope.message = b"hello"
	
	assert envelope

def test_envelope_empty_receiver() : 
	to_adr = []
	msg = Message(content="hello")
	message_bytes = ProtobufSerializer().encode(msg)
	envelope = Envelope(to=to_adr, sender="Agent0", protocol_id="my_own_protocol", message=message_bytes)
	assert (envelope)

def test_inbox_empty():
	my_queue = Queue() 
	_inbox = InBox(my_queue)
	assert(_inbox.empty())

def test_inbox_nowait() : 
	msg = Message(content="hello")
	message_bytes = ProtobufSerializer().encode(msg)
	my_queue = Queue()
	my_queue.put(message_bytes)
	_inbox = InBox(my_queue)
	assert(_inbox.get_nowait())

#Test thet the outbox queue is empty
def test_outbox_empty() :
	my_queue = Queue()
	_outbox = OutBox(my_queue)
	assert(_outbox.empty())


''' Testing the mailBox()'''
#It creates a new thread for the connection ( So interupt after passing all tests)
def test_mailBox() : 
	node = LocalNode()

	public_key_1 = "mailbox1"
	mailbox1 = MailBox(OEFLocalConnection(public_key_1, node))
	mailbox1.connect()
	assert (mailbox1.is_connected,"Mailbox cannot connect to the specific Connection (OEFLocalConnection)")
	mailbox1.disconnect()

	
	
		



