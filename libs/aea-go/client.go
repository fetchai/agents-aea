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

package aea

import (
	"errors"
	"os"
	"strings"
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
	Str("package", "P2PClientApi").
	Logger()

type Socket interface {
	Connect() error
	Read() ([]byte, error)
	Write(data []byte) error
	Close() error
}

type P2PClientApi struct {
	client_config *P2PClientConfig
	agent_record  *AgentRecord

	socket    Socket
	out_queue chan *Envelope

	closing   bool
	connected bool
}

func (client *P2PClientApi) Init() error {
	zerolog.TimeFieldFormat = time.RFC3339Nano

	if client.connected {
		return nil
	}
	client.connected = false

	client.socket = NewSocket(client.client_config.host, client.client_config.port)
	return nil
}

func (client *P2PClientApi) Put(envelope *Envelope) error {
	return write_envelope(client.socket, envelope)
}

func (client *P2PClientApi) Get() *Envelope {
	return <-client.out_queue
}

func (client *P2PClientApi) Queue() <-chan *Envelope {
	return client.out_queue
}

func (client *P2PClientApi) Connected() bool {
	return client.connected
}

func (client *P2PClientApi) Stop() {
	client.closing = true
	client.stop()
	close(client.out_queue)
	client.connected = false
}

func (client *P2PClientApi) Connect() error {
	err := client.socket.Connect()
	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("while connecting to socket")
		return err
	}

	err = client.register()
	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("while registering to p2p node")
		client.stop()
		return err
	}
	logger.Info().Msg("successfully registered on node")

	client.closing = false
	client.out_queue = make(chan *Envelope, 10)
	go client.listen_for_envelopes()
	logger.Info().Msg("connected to p2p node")

	client.connected = true

	return nil
}

func (client *P2PClientApi) register() error {
	registration := &Register{Record: client.agent_record}
	msg := &AcnMessage{
		Version: CurrentVersion,
		Payload: &AcnMessage_Register{Register: registration},
	}

	buf, err := proto.Marshal(msg)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while serializing registration msg: %s", msg)
		return err
	}
	err = client.socket.Write(buf)
	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("while writing register envelope")
		return err
	}
	data, err := client.socket.Read()
	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving data")
		return err
	}
	response := &AcnMessage{}
	err = proto.Unmarshal(data, response)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while deserializing response msg")
		return err
	}

	// Get Status message
	var status *Status
	switch pl := response.Payload.(type) {
	case *AcnMessage_Status:
		status = pl.Status
	default:
		logger.Error().Str("err", err.Error()).Msgf("response not a status msg")
		return err
	}

	if status.Code != Status_SUCCESS {
		return errors.New("as registration failed: " + strings.Join(status.Msgs, ":"))
	}
	return nil
}

func (client *P2PClientApi) listen_for_envelopes() {
	for {
		envel, err := read_envelope(client.socket)
		if err != nil {
			logger.Error().Str("err", err.Error()).Msg("while receiving envelope")
			logger.Info().Msg("disconnecting")
			if !client.closing {
				client.stop()
			}
			return
		}
		if envel.To != client.agent_record.Address {
			logger.Error().
				Str("err", "To ("+envel.To+") must match registered address").
				Msg("while processing envelope")
			continue
		}
		logger.Debug().Msgf("received envelope for agent")
		client.out_queue <- envel
		if client.closing {
			return
		}
	}
}

func (client *P2PClientApi) stop() {
	client.socket.Close()
}

func write_envelope(socket Socket, envelope *Envelope) error {
	data, err := proto.Marshal(envelope)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while serializing envelope: %s", envelope)
		return err
	}
	return socket.Write(data)
}

func read_envelope(socket Socket) (*Envelope, error) {
	envelope := &Envelope{}
	data, err := socket.Read()
	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving data")
		return envelope, err
	}
	err = proto.Unmarshal(data, envelope)
	return envelope, err
}
