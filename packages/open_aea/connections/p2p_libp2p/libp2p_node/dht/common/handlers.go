/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2019 Fetch.AI Limited
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

// Package dhtpeer provides an implementation of an Agent Communication Network node
// using libp2p. It participates in data storage and routing for the network.
// It offers RelayService for dhtclient and DelegateService for tcp clients.
package common

import (
	"strings"

	"log"

	"github.com/libp2p/go-libp2p-core/network"
	"github.com/pkg/errors"
	"github.com/rs/zerolog"
	"google.golang.org/protobuf/proto"

	acn "libp2p_node/acn"
	aea "libp2p_node/aea"
	"libp2p_node/dht/dhtnode"
	utils "libp2p_node/utils"
)

func ignore(err error) {
	if err != nil {
		log.Println("IGNORED", err)
	}
}

//Abstract DHTHandler that provides logging function and handle for incoming envelopes and ACN address requests
type DHTHandler interface {
	GetLoggers() (func(error) *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event)
	HandleAeaEnvelope(envel *aea.Envelope) *acn.ACNError
	HandleAeaAddressRequest(reqAddress string) (*acn.AgentRecord, *acn.ACNError)
}

//read ACN message, decode envelope, check PoR
func receiveEnvelopeFromPeer(dhtHandler DHTHandler, stream network.Stream) (*aea.Envelope, error) {
	lerror, _, _, _ := dhtHandler.GetLoggers()
	streamPipe := utils.StreamPipe{Stream: stream}

	aeaEnvelope, err := acn.ReadEnvelopeMessage(streamPipe)
	if err != nil {
		lerror(err).Msg("while handling acn envelope message")
		return nil, err
	}

	envel := &aea.Envelope{}
	err = proto.Unmarshal(aeaEnvelope.Envelope, envel)
	if err != nil {
		lerror(err).Msg("while deserializing acn aea envelope message")
		ignore(acn.SendAcnError(
			streamPipe,
			"while deserializing acn aea envelope message",
			acn.ERROR_DECODE,
		))
		return nil, err
	}

	remotePubkey, err := utils.FetchAIPublicKeyFromPubKey(stream.Conn().RemotePublicKey())
	ignore(err)
	status, err := dhtnode.IsValidProofOfRepresentation(
		aeaEnvelope.Record,
		aeaEnvelope.Record.Address,
		remotePubkey,
	)
	if err != nil || status.Code != acn.SUCCESS {
		if err == nil {
			err = errors.New(status.Code.String() + ":" + strings.Join(status.Msgs, ":"))
		}
		lerror(err).Msg("incoming envelope PoR is not valid")
		ignore(acn.SendAcnError(streamPipe, "incoming envelope PoR is not valid", status.Code))
		return nil, err
	}
	return envel, nil
}

// handle envelope stream, handle acn protocol and call dhtHandler.HandleAeaEnvelope for incoming envelopes
func HandleAeaEnvelopeStream(dhtHandler DHTHandler, stream network.Stream) {
	lerror, _, _, ldebug := dhtHandler.GetLoggers()

	//ldebug().Msgf("Got a new aea envelope stream")

	envel, err := receiveEnvelopeFromPeer(dhtHandler, stream)

	if err != nil {
		lerror(err).Msgf("while reading envelope from peer")
		stream.Close()
		return
	}

	ldebug().Msgf("Received envelope from peer %s", envel.String())
	streamPipe := utils.StreamPipe{Stream: stream}
	acnError := dhtHandler.HandleAeaEnvelope(envel)

	if acnError != nil {
		err = acn.SendAcnError(streamPipe, acnError.Err.Error(), acnError.ErrorCode)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	err = acn.SendAcnSuccess(streamPipe)
	ignore(err)
	err = stream.Close()
	ignore(err)
}

// handle address request stream, handle acn protocol and call dhtHandler.HandleAeaAddressRequest for incoming requests
func HandleAeaAddressStream(dhtHandler DHTHandler, stream network.Stream) {
	lerror, _, _, ldebug := dhtHandler.GetLoggers()

	//ldebug().Msg("Got a new aea address stream")

	// get LookupRequest
	streamPipe := utils.StreamPipe{Stream: stream}
	reqAddress, err := acn.ReadLookupRequest(streamPipe)
	if err != nil {
		lerror(err).Str("op", "resolve").
			Msg("while reading message from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	ldebug().
		Str("op", "resolve").
		Str("target", reqAddress).
		Msg("Received query for addr")

	record, acnError := dhtHandler.HandleAeaAddressRequest(reqAddress)
	if acnError != nil {
		lerror(acnError.Err).
			Str("op", "resolve").
			Str("target", reqAddress).
			Msgf("request address error")
		err = acn.SendAcnError(streamPipe, acnError.Err.Error(), acnError.ErrorCode)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}
	if record == nil {
		lerror(acnError.Err).
			Str("op", "resolve").
			Str("target", reqAddress).
			Msgf("unexpected error. agent record is nil!")
		return
	}
	err = acn.SendLookupResponse(streamPipe, record)
	if err != nil {
		lerror(err).Str("op", "resolve").Str("addr", reqAddress).
			Msg("while sending agent record to peer")
		err = stream.Reset()
		ignore(err)
	}
}
