``` proto
syntax = "proto3";

package aea;

message Envelope{
    string to = 1;
    string sender = 2;
    string protocol_id = 3;
    bytes message = 4;
    string uri = 5;
}
```
``` proto
import "google/protobuf/struct.proto";

message DialogueMessage {
    int32 message_id = 1;
    string dialogue_starter_reference = 2;
    string dialogue_responder_reference = 3;
    int32 target = 4;
    bytes content = 5;
}

message Message {
    oneof message {
        google.protobuf.Struct body = 1;
        DialogueMessage dialogue_message = 2;
    }
}
```
``` proto
syntax = "proto3";

package aea.fetchai.default;

message DefaultMessage{

    // Custom Types
    message ErrorCode{
        enum ErrorCodeEnum {
            UNSUPPORTED_PROTOCOL = 0;
            DECODING_ERROR = 1;
            INVALID_MESSAGE = 2;
            UNSUPPORTED_SKILL = 3;
            INVALID_DIALOGUE = 4;
          }
        ErrorCodeEnum error_code = 1;
    }


    // Performatives and contents
    message Bytes_Performative{
        bytes content = 1;
    }

    message Error_Performative{
        ErrorCode error_code = 1;
        string error_msg = 2;
        map<string, bytes> error_data = 3;
    }

    message End_Performative{}


    oneof performative{
        Bytes_Performative bytes = 5;
        End_Performative end = 6;
        Error_Performative error = 7;
    }
}
```