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

package connections

import (
	"errors"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	protocols "aealite/protocols"
	"github.com/joho/godotenv"
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

type P2PClientConfig struct {
	host string
	port uint16
}

type P2PClientApi struct {
	client_config *P2PClientConfig
	agent_record  *protocols.AgentRecord

	socket    Socket
	out_queue chan *protocols.Envelope

	closing     bool
	connected   bool
	initialised bool
}

func (client *P2PClientApi) InitFromEnv() error {
	zerolog.TimeFieldFormat = time.RFC3339Nano

	if client.connected {
		return nil
	}
	client.connected = false
	client.initialised = false

	env_file := os.Args[1]
	logger.Debug().Msgf("env_file: %s", env_file)
	err := godotenv.Overload(env_file)
	if err != nil {
		log.Fatal("Error loading env file")
	}
	address := os.Getenv("AEA_ADDRESS")
	public_key := os.Getenv("AEA_PUBLIC_KEY")
	agent_record := &protocols.AgentRecord{Address: address, PublicKey: public_key}
	agent_record.ServiceId = os.Getenv("AEA_P2P_POR_SERVICE_ID")
	agent_record.LedgerId = os.Getenv("AEA_P2P_POR_LEDGER_ID")
	agent_record.PeerPublicKey = os.Getenv("AEA_P2P_POR_PEER_PUBKEY")
	agent_record.Signature = os.Getenv("AEA_P2P_POR_SIGNATURE")
	client.agent_record = agent_record
	host := os.Getenv("AEA_P2P_DELEGATE_HOST")
	port := os.Getenv("AEA_P2P_DELEGATE_PORT")
	port_conv, err := strconv.ParseUint(port, 10, 16)
	if err != nil {
		panic(err)
	}
	client.client_config = &P2PClientConfig{host: host, port: uint16(port_conv)}

	client.socket = NewSocket(client.client_config.host, client.client_config.port)
	client.initialised = true
	return nil
}

func (client *P2PClientApi) Put(envelope *protocols.Envelope) error {
	return write_envelope(client.socket, envelope)
}

func (client *P2PClientApi) Get() *protocols.Envelope {
	return <-client.out_queue
}

func (client *P2PClientApi) Queue() <-chan *protocols.Envelope {
	return client.out_queue
}

func (client *P2PClientApi) Connected() bool {
	return client.connected
}

func (client *P2PClientApi) Initialised() bool {
	return client.initialised
}

func (client *P2PClientApi) Disconnect() error {
	client.closing = true
	err := client.stop()
	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("error while disconnecting P2PClientApi")
		return err
	}
	close(client.out_queue)
	client.connected = false
	return nil
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
		err_ := client.stop()
		if err_ != nil {
			logger.Error().Str("err", err_.Error()).
				Msg("while handling other error")
		}
		return err
	}
	logger.Info().Msg("successfully registered on node")

	client.closing = false
	client.out_queue = make(chan *protocols.Envelope, 10)
	go client.listen_for_envelopes()
	logger.Info().Msg("connected to p2p node")

	client.connected = true

	return nil
}

func (client *P2PClientApi) register() error {
	registration := &protocols.Register{Record: client.agent_record}
	msg := &protocols.AcnMessage{
		Version: protocols.ACNProtocolVersion,
		Payload: &protocols.AcnMessage_Register{Register: registration},
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
	response := &protocols.AcnMessage{}
	err = proto.Unmarshal(data, response)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while deserializing response msg")
		return err
	}

	// Get Status message
	var status *protocols.Status
	switch pl := response.Payload.(type) {
	case *protocols.AcnMessage_Status:
		status = pl.Status
	default:
		logger.Error().Str("err", err.Error()).Msgf("response not a status msg")
		return err
	}

	if status.Code != protocols.Status_SUCCESS {
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
				err_ := client.stop()
				if err_ != nil {
					logger.Error().Str("err", err_.Error()).Msg("while handling other error")
				}
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

func (client *P2PClientApi) stop() error {
	return client.socket.Disconnect()
}

func write_envelope(socket Socket, envelope *protocols.Envelope) error {
	data, err := proto.Marshal(envelope)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while serializing envelope: %s", envelope)
		return err
	}
	return socket.Write(data)
}

func read_envelope(socket Socket) (*protocols.Envelope, error) {
	envelope := &protocols.Envelope{}
	data, err := socket.Read()
	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving data")
		return envelope, err
	}
	err = proto.Unmarshal(data, envelope)
	return envelope, err
}
