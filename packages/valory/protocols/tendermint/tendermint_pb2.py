# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: tendermint.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x10tendermint.proto\x12\x1c\x61\x65\x61.valory.tendermint.v0_1_0"\xb3\x06\n\x11TendermintMessage\x12S\n\x05\x65rror\x18\x05 \x01(\x0b\x32\x42.aea.valory.tendermint.v0_1_0.TendermintMessage.Error_PerformativeH\x00\x12W\n\x07request\x18\x06 \x01(\x0b\x32\x44.aea.valory.tendermint.v0_1_0.TendermintMessage.Request_PerformativeH\x00\x12Y\n\x08response\x18\x07 \x01(\x0b\x32\x45.aea.valory.tendermint.v0_1_0.TendermintMessage.Response_PerformativeH\x00\x1a\x8e\x01\n\tErrorCode\x12[\n\nerror_code\x18\x01 \x01(\x0e\x32G.aea.valory.tendermint.v0_1_0.TendermintMessage.ErrorCode.ErrorCodeEnum"$\n\rErrorCodeEnum\x12\x13\n\x0fINVALID_REQUEST\x10\x00\x1a;\n\x14Request_Performative\x12\r\n\x05query\x18\x01 \x01(\t\x12\x14\n\x0cquery_is_set\x18\x02 \x01(\x08\x1a%\n\x15Response_Performative\x12\x0c\n\x04info\x18\x01 \x01(\t\x1a\x8f\x02\n\x12\x45rror_Performative\x12M\n\nerror_code\x18\x01 \x01(\x0b\x32\x39.aea.valory.tendermint.v0_1_0.TendermintMessage.ErrorCode\x12\x11\n\terror_msg\x18\x02 \x01(\t\x12\x65\n\nerror_data\x18\x03 \x03(\x0b\x32Q.aea.valory.tendermint.v0_1_0.TendermintMessage.Error_Performative.ErrorDataEntry\x1a\x30\n\x0e\x45rrorDataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x42\x0e\n\x0cperformativeb\x06proto3'
)


_TENDERMINTMESSAGE = DESCRIPTOR.message_types_by_name["TendermintMessage"]
_TENDERMINTMESSAGE_ERRORCODE = _TENDERMINTMESSAGE.nested_types_by_name["ErrorCode"]
_TENDERMINTMESSAGE_REQUEST_PERFORMATIVE = _TENDERMINTMESSAGE.nested_types_by_name[
    "Request_Performative"
]
_TENDERMINTMESSAGE_RESPONSE_PERFORMATIVE = _TENDERMINTMESSAGE.nested_types_by_name[
    "Response_Performative"
]
_TENDERMINTMESSAGE_ERROR_PERFORMATIVE = _TENDERMINTMESSAGE.nested_types_by_name[
    "Error_Performative"
]
_TENDERMINTMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY = _TENDERMINTMESSAGE_ERROR_PERFORMATIVE.nested_types_by_name[
    "ErrorDataEntry"
]
_TENDERMINTMESSAGE_ERRORCODE_ERRORCODEENUM = _TENDERMINTMESSAGE_ERRORCODE.enum_types_by_name[
    "ErrorCodeEnum"
]
TendermintMessage = _reflection.GeneratedProtocolMessageType(
    "TendermintMessage",
    (_message.Message,),
    {
        "ErrorCode": _reflection.GeneratedProtocolMessageType(
            "ErrorCode",
            (_message.Message,),
            {
                "DESCRIPTOR": _TENDERMINTMESSAGE_ERRORCODE,
                "__module__": "tendermint_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.tendermint.v0_1_0.TendermintMessage.ErrorCode)
            },
        ),
        "Request_Performative": _reflection.GeneratedProtocolMessageType(
            "Request_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _TENDERMINTMESSAGE_REQUEST_PERFORMATIVE,
                "__module__": "tendermint_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.tendermint.v0_1_0.TendermintMessage.Request_Performative)
            },
        ),
        "Response_Performative": _reflection.GeneratedProtocolMessageType(
            "Response_Performative",
            (_message.Message,),
            {
                "DESCRIPTOR": _TENDERMINTMESSAGE_RESPONSE_PERFORMATIVE,
                "__module__": "tendermint_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.tendermint.v0_1_0.TendermintMessage.Response_Performative)
            },
        ),
        "Error_Performative": _reflection.GeneratedProtocolMessageType(
            "Error_Performative",
            (_message.Message,),
            {
                "ErrorDataEntry": _reflection.GeneratedProtocolMessageType(
                    "ErrorDataEntry",
                    (_message.Message,),
                    {
                        "DESCRIPTOR": _TENDERMINTMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY,
                        "__module__": "tendermint_pb2"
                        # @@protoc_insertion_point(class_scope:aea.valory.tendermint.v0_1_0.TendermintMessage.Error_Performative.ErrorDataEntry)
                    },
                ),
                "DESCRIPTOR": _TENDERMINTMESSAGE_ERROR_PERFORMATIVE,
                "__module__": "tendermint_pb2"
                # @@protoc_insertion_point(class_scope:aea.valory.tendermint.v0_1_0.TendermintMessage.Error_Performative)
            },
        ),
        "DESCRIPTOR": _TENDERMINTMESSAGE,
        "__module__": "tendermint_pb2"
        # @@protoc_insertion_point(class_scope:aea.valory.tendermint.v0_1_0.TendermintMessage)
    },
)
_sym_db.RegisterMessage(TendermintMessage)
_sym_db.RegisterMessage(TendermintMessage.ErrorCode)
_sym_db.RegisterMessage(TendermintMessage.Request_Performative)
_sym_db.RegisterMessage(TendermintMessage.Response_Performative)
_sym_db.RegisterMessage(TendermintMessage.Error_Performative)
_sym_db.RegisterMessage(TendermintMessage.Error_Performative.ErrorDataEntry)

if _descriptor._USE_C_DESCRIPTORS == False:

    DESCRIPTOR._options = None
    _TENDERMINTMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._options = None
    _TENDERMINTMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_options = b"8\001"
    _TENDERMINTMESSAGE._serialized_start = 51
    _TENDERMINTMESSAGE._serialized_end = 870
    _TENDERMINTMESSAGE_ERRORCODE._serialized_start = 338
    _TENDERMINTMESSAGE_ERRORCODE._serialized_end = 480
    _TENDERMINTMESSAGE_ERRORCODE_ERRORCODEENUM._serialized_start = 444
    _TENDERMINTMESSAGE_ERRORCODE_ERRORCODEENUM._serialized_end = 480
    _TENDERMINTMESSAGE_REQUEST_PERFORMATIVE._serialized_start = 482
    _TENDERMINTMESSAGE_REQUEST_PERFORMATIVE._serialized_end = 541
    _TENDERMINTMESSAGE_RESPONSE_PERFORMATIVE._serialized_start = 543
    _TENDERMINTMESSAGE_RESPONSE_PERFORMATIVE._serialized_end = 580
    _TENDERMINTMESSAGE_ERROR_PERFORMATIVE._serialized_start = 583
    _TENDERMINTMESSAGE_ERROR_PERFORMATIVE._serialized_end = 854
    _TENDERMINTMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_start = 806
    _TENDERMINTMESSAGE_ERROR_PERFORMATIVE_ERRORDATAENTRY._serialized_end = 854
# @@protoc_insertion_point(module_scope)
