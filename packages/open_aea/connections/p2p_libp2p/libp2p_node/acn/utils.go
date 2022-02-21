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
	"strings"
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

const ERROR_DECODE = acn_protocol.AcnMessage_StatusBody_ERROR_DECODE
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

func ignore(err error) {
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("IGNORED: %s", err.Error())
	}
}

type ACNError struct {
	ErrorCode Status_ErrCode
	Err       error
}

func (err *ACNError) Error() string {
	return err.Err.Error()
}

func DecodeAcnMessage(buf []byte) (string, *AeaEnvelopePerformative, *StatusBody, *ACNError) {
	response := &AcnMessage{}
	err := proto.Unmarshal(buf, response)
	msg_type := ""

	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while decoding acn message")
		return msg_type, nil, nil, &ACNError{ErrorCode: ERROR_DECODE, Err: err}
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
		return msg_type, nil, nil, &ACNError{ErrorCode: ERROR_UNEXPECTED_PAYLOAD, Err: err}
	}
	return msg_type, aeaEnvelope, status, nil
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

func EncodeAcnEnvelope(envelope_bytes []byte, record *AgentRecord) ([]byte, error) {
	var performative *AeaEnvelopePerformative
	if record != nil {
		performative = &AeaEnvelopePerformative{Envelope: envelope_bytes, Record: record}
	} else {
		performative = &AeaEnvelopePerformative{Envelope: envelope_bytes}
	}

	msg := &AcnMessage{
		Performative: &AeaEnvelope{AeaEnvelope: performative},
	}

	buf, err := proto.Marshal(msg)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("while serializing envelope bytes: %s", envelope_bytes)
	}
	return buf, err
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

func ReadAgentRegistrationMessage(pipe Pipe) (*RegisterPerformative, error) {
	var register *RegisterPerformative
	buf, err := pipe.Read()
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while receiving agent's registration request")
		return nil, err
	}

	msg := &AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("couldn't deserialize acn registration message")
		// TOFIX(LR) setting Msgs to err.Error is potentially a security vulnerability
		acn_send_error := SendAcnError(pipe, err.Error(), ERROR_DECODE)
		ignore(acn_send_error)
		return nil, err
	}

	switch pl := msg.Performative.(type) {
	case *Register:
		register = pl.Register
	default:
		err = errors.New("Unexpected payload")
		acn_send_error := SendAcnError(pipe, err.Error(), ERROR_UNEXPECTED_PAYLOAD)
		ignore(acn_send_error)
		return nil, err
	}
	return register, nil
}

func SendEnvelopeMessageAndWaitForStatus(
	pipe Pipe,
	envelope_bytes []byte,
	acn_status_chan chan *StatusBody,
	acnStatusTimeout time.Duration,
) error {
	err := SendEnvelopeMessage(pipe, envelope_bytes, nil)
	if err != nil {
		return err
	}

	status, err := WaitForStatus(acn_status_chan, acnStatusTimeout)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("on envelope sent status wait")
		return err
	}
	if status.Code != SUCCESS {
		logger.Error().
			Str("op", "send_envelope").
			Msgf("acn confirmation status is not Status Success: %d.", status.Code)
		return fmt.Errorf(
			"send envelope: acn confirmation status is not Status Success: %d",
			status.Code,
		)
	}
	return err

}

func ReadLookupRequest(pipe Pipe) (string, error) {
	buf, err := pipe.Read()

	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while reading message from stream")
		return "", err
	}

	msg := &AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("couldn't deserialize acn lookup request message")
		// TOFIX(LR) setting Msgs to err.Error is potentially a security vulnerability
		acn_send_error := SendAcnError(pipe, err.Error(), ERROR_DECODE)
		ignore(acn_send_error)
		return "", err
	}

	// Get LookupRequest message
	var lookupRequest *LookupRequestPerformative
	switch pl := msg.Performative.(type) {
	case *LookupRequest:
		lookupRequest = pl.LookupRequest
	default:
		err = errors.New("Unexpected payload")
		acn_send_error := SendAcnError(pipe, err.Error(), ERROR_UNEXPECTED_PAYLOAD)
		ignore(acn_send_error)
		return "", err
	}

	reqAddress := lookupRequest.AgentAddress
	return reqAddress, nil
}

func SendLookupRequest(pipe Pipe, address string) error {
	lookupRequest := &LookupRequestPerformative{AgentAddress: address}
	msg := &AcnMessage{
		Performative: &LookupRequest{LookupRequest: lookupRequest},
	}
	buf, err := proto.Marshal(msg)
	if err != nil {
		return err
	}
	err = pipe.Write([]byte(buf))
	return err
}

func ReadLookupResponse(pipe Pipe) (*AgentRecord, error) {
	buf, err := pipe.Read()
	if err != nil {
		return nil, err
	}
	response := &AcnMessage{}
	err = proto.Unmarshal(buf, response)
	if err != nil {
		return nil, err
	}
	var lookupResponse *LookupResponsePerformative = nil
	var status *StatusPerformative = nil
	switch pl := response.Performative.(type) {
	case *LookupResponse:
		lookupResponse = pl.LookupResponse
	case *Status:
		status = pl.Status
	default:
		err = errors.New("Unexpected Acn Message")
		logger.Error().Str("err", err.Error()).Msgf("couldn't deserialize acn lookup response message")
		return nil, err
	}

	if status != nil {
		err = errors.New(
			"Failed agent lookup response " + status.Body.Code.String() + " : " + strings.Join(
				status.Body.Msgs,
				":",
			),
		)
		return nil, err
	}
	return lookupResponse.Record, nil
}

func SendLookupResponse(pipe Pipe, record *AgentRecord) error {
	lookupResponse := &LookupResponsePerformative{Record: record}
	response := &AcnMessage{
		Performative: &LookupResponse{LookupResponse: lookupResponse},
	}
	buf, err := proto.Marshal(response)
	if err != nil {
		return err
	}
	err = pipe.Write(buf)
	return err
}

func SendEnvelopeMessage(pipe Pipe, envelope_bytes []byte, record *AgentRecord) error {
	acnMsgBytes, err := EncodeAcnEnvelope(envelope_bytes, record)
	if err != nil {
		return err
	}
	err = pipe.Write(acnMsgBytes)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("on pipe write")
		return err
	}
	return nil
}

func SendAgentRegisterMessage(pipe Pipe, agentRecord *AgentRecord) error {
	registration := &RegisterPerformative{Record: agentRecord}
	msg := &AcnMessage{
		Performative: &Register{Register: registration},
	}
	buf, err := proto.Marshal(msg)
	if err != nil {
		return err
	}

	err = pipe.Write(buf)
	if err != nil {
		return err
	}

	status, err := ReadAcnStatus(pipe)
	if err != nil {
		return err
	}
	if status.Code != SUCCESS {
		return errors.New("Registration failed: " + strings.Join(status.Msgs, ":"))
	}
	return nil
}

func ReadAcnStatus(pipe Pipe) (*StatusBody, error) {
	buf, err := pipe.Read()
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("on pipe read")
		return nil, err
	}

	response := &AcnMessage{}
	err = proto.Unmarshal(buf, response)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("on acn decode")
		return nil, err
	}

	// response is expected to be a Status
	var status *StatusPerformative
	switch pl := response.Performative.(type) {
	case *Status:
		status = pl.Status
	default:
		err = errors.New("Unexpected Acn Message")
		return nil, err
	}

	return status.Body, nil
}

func ReadEnvelopeMessage(pipe Pipe) (*AeaEnvelopePerformative, error) {
	buf, err := pipe.Read()
	if err != nil {
		return nil, err
	}
	messageType, envelope, _, acnErr := DecodeAcnMessage(buf)

	if acnErr != nil {
		err = SendAcnError(
			pipe,
			acnErr.Error(),
			acnErr.ErrorCode,
		)
		ignore(err)
		return nil, acnErr.Err
	}
	if messageType != "aea_envelope" {
		return nil, errors.New("unexpected payload for acn message")
	}
	return envelope, nil
}

func PerformAddressLookup(pipe Pipe, address string) (*AgentRecord, error) {
	err := SendLookupRequest(pipe, address)
	if err != nil {
		return nil, err
	}
	return ReadLookupResponse(pipe)
}
