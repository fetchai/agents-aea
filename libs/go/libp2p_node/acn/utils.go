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
	"os"
	"time"

	"github.com/rs/zerolog"
	proto "google.golang.org/protobuf/proto"
)

var logger zerolog.Logger = zerolog.New(zerolog.ConsoleWriter{
	Out:        os.Stdout,
	NoColor:    false,
	TimeFormat: "15:04:05.000",
}).
	With().Timestamp().
	Str("package", "AeaApiACN").
	Logger()

const CurrentVersion = "0.1.0"

func DecodeACNMessage(buf []byte) (string, *AeaEnvelope, *Status, error) {
	response := &AcnMessage{}
	err := proto.Unmarshal(buf, response)
	msg_type := ""
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while decoding acn message")
		return msg_type, nil, nil, err
	}
	// response is either a LookupResponse or Status
	var aeaEnvelope *AeaEnvelope = nil
	var status *Status = nil

	switch pl := response.Payload.(type) {
	case *AcnMessage_AeaEnvelope:
		aeaEnvelope = pl.AeaEnvelope
		msg_type = "aea_envelope"
	case *AcnMessage_Status:
		status = pl.Status
		msg_type = "status"
	default:
		logger.Error().Str("err", err.Error()).Msgf("unexpected ACN Message")
		err = errors.New("unexpected ACN Message")
		return msg_type, nil, nil, err
	}
	return msg_type, aeaEnvelope, status, err
}

func WaitForStatus(ch chan *Status, timeout time.Duration) (*Status, error) {
	select {
	case m := <-ch:
		return m, nil
	case <-time.After(timeout):
		logger.Error().Msgf("ACN send acknowledge timeout")
		return nil, errors.New("ACN send acknowledge timeout")
	}
}

func SendAcnSuccess(pipe Pipe) error {
	status := &Status{Code: Status_SUCCESS}
	msg := &AcnMessage{
		Version: CurrentVersion,
		Payload: &AcnMessage_Status{Status: status},
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

func SendAcnError(pipe Pipe, error_msg string) error {
	status := &Status{Code: Status_ERROR_GENERIC, Msgs: []string{error_msg}}
	msg := &AcnMessage{
		Version: CurrentVersion,
		Payload: &AcnMessage_Status{Status: status},
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

func EncodeACNEnvelope(envelope_bytes []byte) (error, []byte) {
	aeaEnvelope := &AeaEnvelope{Envel: envelope_bytes}
	msg := &AcnMessage{
		Version: CurrentVersion,
		Payload: &AcnMessage_AeaEnvelope{AeaEnvelope: aeaEnvelope},
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
	AddACNStatusMessage(status *Status, counterpartyID string)
}
