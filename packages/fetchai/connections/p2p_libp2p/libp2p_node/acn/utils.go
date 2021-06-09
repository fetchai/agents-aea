/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2021 Fetch.AI Limited
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*       http://www.apache.org/licenses/LICENSE-2.0
*
*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*
* ------------------------------------------------------------------------------
 */
package acn

import (
	"errors"
	"fmt"
	"os"
	"time"

	acn_protocol "libp2p_node/protocols/acn/v1_0_0"

	"github.com/rs/zerolog"
	proto "google.golang.org/protobuf/proto"
)

type StatusBody = acn_protocol.AcnMessage_StatusBody
type AgentRecord = acn_protocol.AcnMessage_AgentRecord
type AcnMessage = acn_protocol.AcnMessage
type LookupRequest = acn_protocol.AcnMessage_LookupRequest
type LookupResponse = acn_protocol.AcnMessage_LookupResponse
type Status = acn_protocol.AcnMessage_Status
type LookupRequestPerformative = acn_protocol.AcnMessage_Lookup_Request_Performative
type LookupResponsePerformative = acn_protocol.AcnMessage_Lookup_Response_Performative
type StatusPerformative = acn_protocol.AcnMessage_Status_Performative
type RegisterPerformative = acn_protocol.AcnMessage_Register_Performative
type Register = acn_protocol.AcnMessage_Register
type AeaEnvelope = acn_protocol.AcnMessage_AeaEnvelope
type AeaEnvelopePerformative = acn_protocol.AcnMessage_Aea_Envelope_Performative

const ERROR_SERIALIZATION = acn_protocol.AcnMessage_StatusBody_ERROR_SERIALIZATION
const SUCCESS = acn_protocol.AcnMessage_StatusBody_SUCCESS
const ERROR_UNEXPECTED_PAYLOAD = acn_protocol.AcnMessage_StatusBody_ERROR_UNEXPECTED_PAYLOAD
const ERROR_AGENT_NOT_READY = acn_protocol.AcnMessage_StatusBody_ERROR_AGENT_NOT_READY
const ERROR_UNKNOWN_AGENT_ADDRESS = acn_protocol.AcnMessage_StatusBody_ERROR_UNKNOWN_AGENT_ADDRESS
const ERROR_GENERIC = acn_protocol.AcnMessage_StatusBody_ERROR_GENERIC
const ERROR_WRONG_AGENT_ADDRESS = acn_protocol.AcnMessage_StatusBody_ERROR_WRONG_AGENT_ADDRESS
const ERROR_UNSUPPORTED_LEDGER = acn_protocol.AcnMessage_StatusBody_ERROR_UNSUPPORTED_LEDGER
const ERROR_WRONG_PUBLIC_KEY = acn_protocol.AcnMessage_StatusBody_ERROR_WRONG_PUBLIC_KEY
const ERROR_INVALID_PROOF = acn_protocol.AcnMessage_StatusBody_ERROR_INVALID_PROOF

type Status_ErrCode = acn_protocol.AcnMessage_StatusBody_StatusCodeEnum

var logger zerolog.Logger = zerolog.New(zerolog.ConsoleWriter{
	Out:        os.Stdout,
	NoColor:    false,
	TimeFormat: "15:04:05.000",
}).
	With().Timestamp().
	Str("package", "AeaApiACN").
	Logger()

const CurrentVersion = "0.1.0"

func DecodeAcnMessage(buf []byte) (string, *AeaEnvelopePerformative, *StatusBody, error) {
	response := &AcnMessage{}
	err := proto.Unmarshal(buf, response)
	msg_type := ""
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while decoding acn message")
		return msg_type, nil, nil, err
	}
	// response is either a LookupResponse or Status
	var aeaEnvelope *AeaEnvelopePerformative = nil
	var status *StatusBody = nil

	switch pl := response.Performative.(type) {
	case *AeaEnvelope:
		aeaEnvelope = pl.AeaEnvelope
		msg_type = "aea_envelope"
	case *Status:
		status = pl.Status.Body
		msg_type = "status"
	default:
		err = fmt.Errorf("unexpected ACN Message: %s", response)
		logger.Error().Msg(err.Error())
		return msg_type, nil, nil, err
	}
	return msg_type, aeaEnvelope, status, err
}

func WaitForStatus(ch chan *StatusBody, timeout time.Duration) (*StatusBody, error) {
	select {
	case m := <-ch:
		return m, nil
	case <-time.After(timeout):
		err := errors.New("ACN send acknowledge timeout")
		logger.Error().Msg(err.Error())
		return nil, err
	}
}

func SendAcnSuccess(pipe Pipe) error {
	status := &StatusBody{Code: SUCCESS}
	performative := &StatusPerformative{Body: status}
	msg := &AcnMessage{
		Performative: &Status{Status: performative},
	}
	buf, err := proto.Marshal(msg)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("error on encoding acn status message")
		return err
	}
	err = pipe.Write(buf)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("error on sending acn status message")

	}
	return err
}

func SendAcnError(pipe Pipe, error_msg string, err_codes ...Status_ErrCode) error {
	var err_code Status_ErrCode

	if len(err_codes) == 0 {
		err_code = ERROR_GENERIC
	} else {
		err_code = err_codes[0]
	}

	status := &StatusBody{Code: err_code, Msgs: []string{error_msg}}
	msg := &AcnMessage{
		Performative: &Status{Status: &StatusPerformative{Body: status}},
	}
	buf, err := proto.Marshal(msg)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("error on encoding acn status message")
		return err
	}
	err = pipe.Write(buf)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("error on sending acn status message")

	}
	return err
}

func EncodeAcnEnvelope(envelope_bytes []byte) (error, []byte) {
	performative := &AeaEnvelopePerformative{Envelope: envelope_bytes}
	msg := &AcnMessage{
		Performative: &AeaEnvelope{AeaEnvelope: performative},
	}
	buf, err := proto.Marshal(msg)
	return err, buf
}

type Pipe interface {
	Connect() error
	Read() ([]byte, error)
	Write(data []byte) error
	Close() error
}

type StatusQueue interface {
	AddAcnStatusMessage(status *StatusBody, counterpartyID string)
}
