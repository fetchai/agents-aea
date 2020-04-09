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

"""This module contains the p2p noise connection."""

import asyncio
import logging
import os
import subprocess
import errno
import struct
import posix
from pathlib import Path
from typing import Optional, List, Union, IO, AnyStr

from asyncio import AbstractEventLoop, CancelledError

from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.mail.base import Address, Envelope

logger = logging.getLogger(__name__)

# TOFIX(LR) make it async, if still relevent
# TOFIX(LR) add return type
def _golang_get_deps(src: str) :  
  cmd = [
    'go',
    'get',
    '-v',
    '-d',
    '.'
  ]

  try:
    logger.debug(cmd)
    proc = subprocess.Popen(cmd, cwd=os.path.dirname(src))
  except Exception as e:
    logger.error('While executing go get : {}'.format(str(e)))
    raise e

  return proc 

# TOFIX(LR) add types
def _golang_run(src: str, args = [], env = {}):
  cmd = [
    'go',
    'run',
    src
  ]

  cmd.extend(args)

  try:
    print(cmd)
    proc = subprocess.Popen(cmd, env=env)
  except Exception as e:
    print('While executing go run {} {} : {}'.format(src, args, str(e)))
    raise

  return proc
 
# TOFIX(LR) NOT thread safe
class NoiseNode():
  r"""Noise p2p node as a subprocess with named pipes interface
  """

  def __init__(
    self,
    identity   : Address,
    entry_addr: str,
    entry_port: int,
    # TOFIX(LR) entry peer should be optional, for genesis peer 
    source : Path, # TOFIX(LR) unionize with str?
    clargs : Optional[List[str]] = [],
    loop: Optional[AbstractEventLoop] = None,
  ):
    """
    """
    # node id in the p2p network
    self.identity = identity

    # entry peer
    # TOFIX(LR) make it a list
    self.entry_addr = entry_addr
    self.entry_port = entry_port
    
    # node startup
    self.source = source
    self.clargs = clargs
    
    # async loop
    # TOFIX(LR) new_loop or get_loop?
    self._loop = loop if loop is not None else asyncio.get_event_loop()

    # named pipes (fifos)
    self.NOISE_TO_AEA_PATH  = '/tmp/{}-noise_to_aea'.format(self.identity)
    self.AEA_TO_NOISE_PATH = '/tmp/{}-aea_to_noise'.format(self.identity)
    self._noise_to_aea = None
    self._aea_to_noise = None
    self._connection_attempts = 3
    
    #
    self.proc = None

  async def start(self) -> None:
    # get source deps
    proc = _golang_get_deps(self.source)
    proc.wait()
    # TOFIX(LR) make it async
    
    # setup fifos
    in_path  = self.NOISE_TO_AEA_PATH
    out_path = self.AEA_TO_NOISE_PATH
    print("[py] creating pipes ({}, {})...".format(in_path, out_path))
    if os.path.exists(in_path):
      os.remove(in_path)
    if os.path.exists(out_path):
      os.remove(out_path)
    os.mkfifo(in_path)
    os.mkfifo(out_path)

    env = os.environ
    env["ID"] = self.identity
    env["NOISE_TO_AEA"] = in_path
    env["AEA_TO_NOISE"] = out_path
    
    # run node
    self.proc = _golang_run(self.source, self.clargs, env)
    
    await self._connect()
    
  async def _connect(self) -> None:
    if self._connection_attempts == 1:
      logger.error("couldn't connect to noise p2p process")
      raise Exception("couldn't connect to noise p2p process")
      # TOFIX(LR) use proper exception
    self._connection_attempts -= 1

    print("[py] attempt opening pipes {}, {}...".format(self.NOISE_TO_AEA_PATH, self.AEA_TO_NOISE_PATH))
    self._noise_to_aea = posix.open(self.NOISE_TO_AEA_PATH, posix.O_RDONLY | os.O_NONBLOCK)
    #self._noise_to_aea = posix.open(self.NOISE_TO_AEA_PATH, posix.O_RDONLY)
    print(self._noise_to_aea)
    try:
      self._aea_to_noise = posix.open(self.AEA_TO_NOISE_PATH, posix.O_WRONLY | os.O_NONBLOCK)
    except OSError as e:
      if e.errno == errno.ENXIO:
        await asyncio.sleep(1)
        await self._connect()
        return
      else:
        raise e
    print("[py] connected to pipes {}, {}...".format(self.NOISE_TO_AEA_PATH, self.AEA_TO_NOISE_PATH))
    #
    self._in_queue = asyncio.Queue()
    # starting receiving msgs
    self._read_messages()
    self._loop.add_reader(self._noise_to_aea, self._read_messages, self)
  
  async def send(self, data: bytes) -> None:
    size = struct.pack("!I", len(data))
    posix.write(self._aea_to_noise, size)
    posix.write(self._aea_to_noise, data)

    await asyncio.sleep(0)
    # TOFIX(LR) hack
    #  could use asyncio add_writer 
    
  def _read_messages(self) -> None:
    # TOFIX(LR) still need to check if all expected bytes are available
    print('[py] looking for messages ...')
    try:
      while(True):
        size = os.read(self._noise_to_aea, 4)
        size = struct.unpack("!I", size)[0]
        print('[py] recved size: {}'.format(size))
        data = os.read(self._noise_to_aea, size)
        print('[py] recved data: {}'.format(data))
    # TOFIX(LR) needs to check if there is more messages
        #asyncio.run_coroutine_threadsafe(
        self._in_queue.put_nowait(data), self._loop
        #).result() # TOFIX(LR) check race conditions
    except OSError as e:
      if e.errno == errno.EAGAIN:
        print('[py] looking for messages ...done')
        return
      else:
        raise e

  async def receive(self) -> Optional[bytes]:
      #data = self._read_messages()
      #return data
      try:
          assert self._in_queue is not None
          data = await self._in_queue.get()
          if data is None:
              logger.debug("Received None.")
              return None
          logger.debug("Received data: {}".format(data))
          return data
      except CancelledError:
          logger.debug("Receive cancelled.")
          return None
      except Exception as e:
          logger.exception(e)
          return None
  
  def stop(self) -> None:
    # TOFIX(LR) should I send a special message? 
    #  or just rely on the node catching SIGTERM?
    proc.terminate()
    proc.wait()
    assert self.in_queue is not None, "Input queue not initialized."
    self.in_queue.put_nowait(None)


def GET_NOISE_NODE_SOURCE() -> Path:
  src = os.path.join(os.path.abspath(os.path.dirname(__file__)), "pipe_from_env.go")
  return src  
  
def GET_NOISE_NODE_CLARGS() -> List[str]:
  return []


class P2PNoiseConnection(Connection):
    r"""A noise p2p library connection.

    This connection uses two files to communicate: one for the incoming messages and
    the other for the outgoing messages. Each line contains an encoded envelope.

    The format of each line is the following:

        TO,SENDER,PROTOCOL_ID,ENCODED_MESSAGE

    e.g.:

        recipient_agent,sender_agent,default,{"type": "bytes", "content": "aGVsbG8="}

    The connection detects new messages by watchdogging the input file looking for new lines.

    To post a message on the input file, you can use e.g.

        echo "..." >> input_file

    or:

        #>>> fp = open("input_file", "ab+")
        #>>> fp.write(b"...\n")

    It is discouraged adding a message with a text editor since the outcome depends on the actual text editor used.
    """
    # TOFIX(LR) add local node ip address and port number
    def __init__(
        self,
        address   : Address,
        noise_addr: str, 
        noise_port: int,
        # TOFIX(LR): make it a list of entry peers, and attempt joining the p2p network in a random ordering
        **kwargs
    ):
        """
        Initialize a p2p noise connection.

        :param address: agent address, will be used as an identity in noise.
        :param noise_addr: noise entry peer ip address.
        :param noise_port: noise entry peer port number.
        """
        if kwargs.get("configuration") is None and kwargs.get("connection_id") is None:
            kwargs["connection_id"] = PublicId("fetchai", "p2p-noise", "0.1.0")
        super().__init__(**kwargs)

        # noise local node
        # TOFIX(LR) noise_node startup config will depends on how code will be shipped
        self.node = NoiseNode(address, noise_addr, noise_port, 
                              GET_NOISE_NODE_SOURCE(), GET_NOISE_NODE_CLARGS(), 
                              self._loop)


    async def connect(self) -> None:
        """Set up the connection."""
        if self.connection_status.is_connected:
            return
        await self.node.start()
        self.connection_status.is_connected = True


    async def disconnect(self) -> None:
        """
        Disconnect from the channel.

        """
        await self.node.stop()
    
    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        data = await self.node.receive()
        if data is not None:
          return Envelope.decode(data)
        else:
          return None

    async def send(self, envelope: Envelope):
        """
        Send messages.

        :return: None
        """
        await self.node.send(envelope.encode())

    @classmethod
    def from_config(
        cls, address: Address, configuration: ConnectionConfig
    ) -> "Connection":
        """
        Get the stub connection from the connection configuration.

        :param address: the address of the agent.
        :param configuration: the connection configuration object.
        :return: the connection object
        """
        noise_addr = str(configuration.config.get("noise_addr"))
        noise_port = int(configuration.config.get("noise_port"))
        restricted_to_protocols_names = {
            p.name for p in configuration.restricted_to_protocols
        }
        excluded_protocols_names = {p.name for p in configuration.excluded_protocols}
        # TOFIX(LR) add local node ip address and port number
        return P2PNoiseConnection(
            address,
            noise_addr,
            noise_port,
            connection_id=configuration.public_id,
            restricted_to_protocols=restricted_to_protocols_names,
            excluded_protocols=excluded_protocols_names,
        )
