# -*- coding: utf-8 -*-

"""
This module contains the support resources for the t_protocol_no_ct protocol.

It was created with protocol buffer compiler version `libprotoc 3.13.0` and aea version `1.1.1`.
"""

from tests.data.generator.t_protocol_no_ct.message import TProtocolNoCtMessage
from tests.data.generator.t_protocol_no_ct.serialization import TProtocolNoCtSerializer


TProtocolNoCtMessage.serializer = TProtocolNoCtSerializer
