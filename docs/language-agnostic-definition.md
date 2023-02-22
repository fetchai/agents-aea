# Language Agnostic Definition

Currently, there is an implementation of the AEA framework in Python which enables the development of AEAs in Python, and allows AEAs which are built with it to run.

However, AEAs can be developed in different programming languages. This is further backed by the idea that agent-based solutions are suited for multi-stakeholder environments where the different AEAs may be developed independently of one another, resulting in heterogeneous systems.

This means that in principle, there could be different implementations of the AEA framework, in various programming languages and for different platforms. However, to ensure that AEAs under any implementation are compatible with one another and able to interact, they must satisfy specific definitions. In this page, we compile a set of definitions which any AEA independent of its implementation must satisfy in order to be able to interact with other AEAs.

An AEA, in technical terms, must satisfy the following requirements:

- It MUST be capable of receiving and sending `Envelopes` which satisfy the following <a href="https://protobuf.dev/" target="_blank">protobuf</a> schema:

    ``` proto
    syntax = "proto3";

    package aea.base.v0_1_0;

    message Envelope{
      string to = 1;
      string sender = 2;
      string protocol_id = 3;
      bytes message = 4;
      string uri = 5;
    }
    ```

    The format for the above fields are as follows:

    - `to` and `sender`: an address derived from the private key of a <a href="https://en.bitcoin.it/wiki/Secp256k1" target="_blank">secp256k1</a>-compatible elliptic curve
    - `protocol_id`: this must match a defined  <a href="https://learn.microsoft.com/en-us/dotnet/standard/base-types/regular-expression-language-quick-reference" target="_blank">regular expression</a> (see below)
    - `message`: a bytes string representing a serialized message in the specified  <a href="../protocol">protocol</a>
    - `URI`: follows <a href="https://datatracker.ietf.org/doc/html/rfc3986" target="_blank">this syntax</a>

- It MUST implement each protocol's `message` with the required meta-fields:

    ``` proto
    syntax = "proto3";

    package aea.base.v0_1_0;

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

    message Envelope{
      string to = 1;
      string sender = 2;
      string protocol_id = 3;
      bytes message = 4;
      string uri = 5;
    }
    ```

     where `content` is replaced with the protocol specific content (see <a href="../protocol-generator">here</a> for details).

- It MUST implement protocols according to their specification (see <a href="../protocol-generator/#full-mode-vs-protobuf-only-mode">here</a> for details).

- It SHOULD implement the `fetchai/default:1.1.7` protocol which satisfies the following protobuf schema:

    ``` proto
    syntax = "proto3";

    package aea.fetchai.default.v1_0_0;

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

      message End_Performative{
      }


      oneof performative{
        Bytes_Performative bytes = 5;
        End_Performative end = 6;
        Error_Performative error = 7;
      }
    }
    ```

- The protocol id MUST match the following regular expression: `^([a-zA-Z_][a-zA-Z0-9_]{0,127})/([a-zA-Z_][a-zA-Z0-9_]{0,127})(:((any|latest|((0|[1-9]\d*))\.((0|[1-9]\d*))\.((0|[1-9]\d*))(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)))?$`
- It is recommended that it processes `Envelopes` asynchronously. Note, the specification regarding the processing of messages does not impose any particular implementation, and the AEA can be designed to process envelopes either synchronously and asynchronously. However, asynchronous message handling enables the agent to be more responsive and scalable in maintaining many concurrent dialogues with its peers.
- It MUST have an identity in the form of, at a minimum, an address derived from a public key and its associated private key (where the elliptic curve must be of type <a href="https://en.bitcoin.it/wiki/Secp256k1" target="_blank">SECP256k1</a>).
- It SHOULD implement handling of errors using the `fetchai/default:1.1.7` protocol. The protobuf schema is given above.
- It MUST implement the following principles when handling messages:
    - It MUST ALWAYS handle incoming envelopes/messages and NEVER raise an exception when decoding and validating the message. This ensures another AEA cannot cause the agent to fail by sending a malicious envelope/message.
    - It MUST NEVER handle outgoing messages and ALWAYS raise an exception when validating the message. An exception implies that the handler is resolving a bug in the implementation.

!!! note
    Additional constraints will be added soon!
