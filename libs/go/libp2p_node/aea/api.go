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
	"log"
	"net"
	"os"
	"strconv"
	"strings"
	"time"

	acn "libp2p_node/acn"

	"github.com/joho/godotenv"
	"github.com/rs/zerolog"
	proto "google.golang.org/protobuf/proto"
)

const ACN_STATUS_TIMEOUT = 5.0 * time.Second

// code redandency to avoid import cycle
var logger zerolog.Logger = zerolog.New(zerolog.ConsoleWriter{
	Out:        os.Stdout,
	NoColor:    false,
	TimeFormat: "15:04:05.000",
}).
	With().Timestamp().
	Str("package", "AeaApi").
	Logger()

type Pipe interface {
	Connect() error
	Read() ([]byte, error)
	Write(data []byte) error
	Close() error
}

/*

  AeaApi type

*/

type AeaApi struct {
	msgin_path      string
	msgout_path     string
	agent_addr      string
	agent_record    *acn.AgentRecord
	id              string
	entry_peers     []string
	host            string
	port            uint16
	host_public     string
	port_public     uint16
	host_delegate   string
	port_delegate   uint16
	host_monitoring string
	port_monitoring uint16

	registrationDelay  float64
	recordsStoragePath string

	pipe       Pipe
	out_queue  chan *Envelope
	send_queue chan *Envelope

	closing         bool
	connected       bool
	sandbox         bool
	standalone      bool
	acn_status_chan chan *acn.Status
}

func (aea AeaApi) AeaAddress() string {
	return aea.agent_addr
}

func (aea AeaApi) PrivateKey() string {
	return aea.id
}

func (aea AeaApi) Address() (string, uint16) {
	return aea.host, aea.port
}

func (aea AeaApi) PublicAddress() (string, uint16) {
	return aea.host_public, aea.port_public
}

func (aea AeaApi) DelegateAddress() (string, uint16) {
	return aea.host_delegate, aea.port_delegate
}

func (aea AeaApi) MonitoringAddress() (string, uint16) {
	return aea.host_monitoring, aea.port_monitoring
}

func (aea AeaApi) EntryPeers() []string {
	return aea.entry_peers
}

func (aea AeaApi) AgentRecord() *acn.AgentRecord {
	return aea.agent_record
}

func (aea AeaApi) RegistrationDelayInSeconds() float64 {
	return aea.registrationDelay
}

func (aea AeaApi) RecordStoragePath() string {
	return aea.recordsStoragePath
}

func (aea AeaApi) Put(envelope *Envelope) error {
	if aea.standalone {
		errorMsg := "node running in standalone mode"
		logger.Warn().Msgf(errorMsg)
		return errors.New(errorMsg)
	}
	aea.send_queue <- envelope
	return nil
}

func (aea *AeaApi) Get() *Envelope {
	if aea.standalone {
		errorMsg := "node running in standalone mode"
		logger.Warn().Msgf(errorMsg)
		return nil
	}
	return <-aea.out_queue
}

func (aea *AeaApi) Queue() <-chan *Envelope {
	return aea.out_queue
}

func (aea *AeaApi) Connected() bool {
	return aea.connected || aea.standalone
}

func (aea *AeaApi) Stop() {
	aea.send_queue <- nil
	aea.closing = true
	aea.stop()
	close(aea.out_queue)
	close(aea.send_queue)
}

func (aea *AeaApi) Init() error {
	zerolog.TimeFieldFormat = time.RFC3339Nano

	if aea.sandbox {
		return nil
	}

	if aea.connected {
		return nil
	}
	aea.connected = false

	env_file := os.Args[1]
	logger.Debug().Msgf("env_file: %s", env_file)

	// get config
	err := godotenv.Overload(env_file)
	if err != nil {
		log.Fatal("Error loading env file")
	}
	aea.msgin_path = os.Getenv("AEA_TO_NODE")
	aea.msgout_path = os.Getenv("NODE_TO_AEA")
	aea.agent_addr = os.Getenv("AEA_AGENT_ADDR")
	aea.id = os.Getenv("AEA_P2P_ID")
	entry_peers := os.Getenv("AEA_P2P_ENTRY_URIS")
	uri := os.Getenv("AEA_P2P_URI")
	uri_public := os.Getenv("AEA_P2P_URI_PUBLIC")
	uri_delegate := os.Getenv("AEA_P2P_DELEGATE_URI")
	uri_monitoring := os.Getenv("AEA_P2P_URI_MONITORING")

	por_address := os.Getenv("AEA_P2P_POR_ADDRESS")
	if por_address != "" {
		record := &acn.AgentRecord{Address: por_address}
		record.PublicKey = os.Getenv("AEA_P2P_POR_PUBKEY")
		record.PeerPublicKey = os.Getenv("AEA_P2P_POR_PEER_PUBKEY")
		record.Signature = os.Getenv("AEA_P2P_POR_SIGNATURE")
		record.ServiceId = os.Getenv("AEA_P2P_POR_SERVICE_ID")
		record.LedgerId = os.Getenv("AEA_P2P_POR_LEDGER_ID")
		aea.agent_record = record
	}

	registrationDelay := os.Getenv("AEA_P2P_CFG_REGISTRATION_DELAY")
	aea.recordsStoragePath = os.Getenv("AEA_P2P_CFG_STORAGE_PATH")

	logger.Debug().Msgf("msgin_path: %s", aea.msgin_path)
	logger.Debug().Msgf("msgout_path: %s", aea.msgout_path)
	logger.Debug().Msgf("id: %s", aea.id)
	logger.Debug().Msgf("addr: %s", aea.agent_addr)
	logger.Debug().Msgf("entry_peers: %s", entry_peers)
	logger.Debug().Msgf("uri: %s", uri)
	logger.Debug().Msgf("uri public: %s", uri_public)
	logger.Debug().Msgf("uri delegate service: %s", uri_delegate)

	if aea.id == "" || uri == "" {
		err := errors.New("couldn't get AEA configuration: key and uri are required")
		logger.Error().Str("err", err.Error()).Msg("")
		return err
	}
	if aea.msgin_path == "" && aea.msgout_path == "" && aea.agent_addr == "" {
		aea.standalone = true
	} else if aea.msgin_path == "" || aea.msgout_path == "" || aea.agent_addr == "" {
		err := errors.New("couldn't get AEA configuration: pipes paths are required when agent address is provided")
		logger.Error().Str("err", err.Error()).Msg("")
		return err
	}

	// parse uri
	parts := strings.SplitN(uri, ":", -1)
	if len(parts) < 2 {
		err := errors.New("malformed Uri " + uri)
		logger.Error().Str("err", err.Error()).Msg("")
		return err
	}
	aea.host = parts[0]
	port, _ := strconv.ParseUint(parts[1], 10, 16)
	aea.port = uint16(port)
	// hack: test if port is taken
	addr, err := net.ResolveTCPAddr("tcp", uri)
	if err != nil {
		return err
	}
	listener, err := net.ListenTCP("tcp", addr)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("Uri already taken %s", uri)
		return err
	}
	listener.Close()

	// parse public uri
	if uri_public != "" {
		parts = strings.SplitN(uri_public, ":", -1)
		if len(parts) < 2 {
			err := errors.New("malformed Uri " + uri_public)
			logger.Error().Str("err", err.Error()).Msg("")
			return err
		}
		aea.host_public = parts[0]
		port, _ = strconv.ParseUint(parts[1], 10, 16)
		aea.port_public = uint16(port)
	} else {
		aea.host_public = ""
		aea.port_public = 0
	}

	// parse delegate uri
	if uri_delegate != "" {
		parts = strings.SplitN(uri_delegate, ":", -1)
		if len(parts) < 2 {
			err := errors.New("malformed Uri " + uri_delegate)
			logger.Error().Str("err", err.Error()).Msg("")
			return err
		}
		aea.host_delegate = parts[0]
		port, _ = strconv.ParseUint(parts[1], 10, 16)
		aea.port_delegate = uint16(port)
	} else {
		aea.host_delegate = ""
		aea.port_delegate = 0
	}

	// parse monitoring uri
	if uri_monitoring != "" {
		parts = strings.SplitN(uri_monitoring, ":", -1)
		if len(parts) < 2 {
			err := errors.New("malformed Uri " + uri_monitoring)
			logger.Error().Str("err", err.Error()).Msg("")
			return err
		}
		aea.host_monitoring = parts[0]
		port, _ = strconv.ParseUint(parts[1], 10, 16)
		aea.port_monitoring = uint16(port)
	} else {
		aea.host_monitoring = ""
		aea.port_monitoring = 0
	}

	// parse entry peers multiaddress
	if len(entry_peers) > 0 {
		aea.entry_peers = strings.SplitN(entry_peers, ",", -1)
	}

	// parse registration delay
	if registrationDelay == "" {
		aea.registrationDelay = 0.0
	} else {
		delay, err := strconv.ParseFloat(registrationDelay, 32)
		if err != nil {
			logger.Error().Str("err", err.Error()).Msgf("malformed RegistrationDelay value")
			return err
		}
		aea.registrationDelay = delay
	}

	// setup pipe
	if !aea.standalone {
		aea.pipe = NewPipe(aea.msgin_path, aea.msgout_path)
	}

	aea.acn_status_chan = make(chan *acn.Status, 1)
	return nil
}

func (aea *AeaApi) Connect() error {
	if aea.standalone {
		logger.Info().Msg("Successfully running in standalone mode")
		return nil
	}

	// open pipes
	err := aea.pipe.Connect()

	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("while connecting to pipe")
		return err
	}

	aea.closing = false
	//TOFIX(LR) trade-offs between bufferd vs unbuffered channel
	aea.out_queue = make(chan *Envelope, 10)
	aea.send_queue = make(chan *Envelope, 10)
	go aea.listenForEnvelopes()
	go aea.envelopeSendLoop()
	logger.Info().Msg("connected to agent")

	aea.connected = true

	return nil
}

func UnmarshalEnvelope(buf []byte) (*Envelope, error) {
	envelope := &Envelope{}
	err := proto.Unmarshal(buf, envelope)
	return envelope, err
}

func (aea *AeaApi) listenForEnvelopes() {
	//TOFIX(LR) add an exit strategy
	for {
		envel, err := HandleAcnMessageFromPipe(aea.pipe, aea, aea.AeaAddress())

		if err != nil {
			logger.Error().Str("err", err.Error()).Msg("while receiving envelope")
			logger.Info().Msg("disconnecting")
			// TOFIX(LR) see above
			if !aea.closing {
				aea.stop()
			}
			return
		}
		if envel == nil {
			// ACN STATUS MSG
			continue
		}
		if envel.Sender != aea.agent_record.Address {
			logger.Error().
				Str("err", "Sender ("+envel.Sender+") must match registered address").
				Msg("while processing envelope")
			// TODO send error back to agent
			continue
		}
		logger.Debug().Msgf("received envelope from agent")
		aea.out_queue <- envel
		if aea.closing {
			return
		}
	}
}

func (aea *AeaApi) envelopeSendLoop() {
	logger.Debug().Msg("send loop started")
	var err error
	for {
		envelope := <-aea.send_queue
		logger.Debug().Msg("send loop: got envelope")

		if envelope == nil {
			logger.Info().Msg("envelope is nil. exit send loop")
			return
		}
		err = aea.SendEnvelope(envelope)
		if err != nil {
			logger.Error().Str("err", err.Error()).Msg("while sending envelope")
		} else {
			logger.Debug().Msg("envelope sent")
		}

		if aea.closing {
			return
		}
	}
}
func (aea *AeaApi) stop() {
	aea.pipe.Close()
}

/*

  Pipes helpers

*/
const CurrentVersion = "0.1.0"

func MakeACNMessageFromEnvelope(envelope *Envelope) (error, []byte) {
	envelope_bytes, err := proto.Marshal(envelope)
	if err != nil {
		return err, envelope_bytes
	}
	return acn.EncodeACNEnvelope(envelope_bytes)
}

func (aea AeaApi) SendEnvelope(envelope *Envelope) error {
	err, data := MakeACNMessageFromEnvelope(envelope)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while serializing envelope: %s", envelope)
		return err
	}
	err = aea.pipe.Write(data)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("on pipe write")
		return err
	}

	status, err := acn.WaitForStatus(aea.acn_status_chan, ACN_STATUS_TIMEOUT)

	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("on status wait")
		return err
	}
	if status.Code != acn.Status_SUCCESS {
		logger.Error().Str("err", err.Error()).Msgf("bad status: %d", status.Code)
		return errors.New("bad status!")
	}
	return err
}

func (aea AeaApi) AddACNStatusMessage(status *acn.Status, counterpartyID string) {
	aea.acn_status_chan <- status
	logger.Info().Msgf("chan len is %d", len(aea.acn_status_chan))
}

func (aea AeaApi) ReceiveEnvelope() (*Envelope, error) {
	envelope := &Envelope{}
	var acn_err error
	data, err := aea.pipe.Read()

	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving data")
		return envelope, err
	}
	msg_type, acn_envelope, status, err := acn.DecodeACNMessage(data)

	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while decoding acn")
		acn_err = acn.SendAcnError(aea.pipe, "error on decoding acn message")
		if acn_err != nil {
			logger.Error().Str("err", err.Error()).Msg("on acn send error")
		}
		return envelope, err
	}

	switch msg_type {
	case "aea_envelope":
		{
			err = proto.Unmarshal(acn_envelope.Envel, envelope)
			if err != nil {
				logger.Error().Str("err", err.Error()).Msg("while decoding envelope")
				acn_err = acn.SendAcnError(aea.pipe, "error on decoding envelope")
				if acn_err != nil {
					logger.Error().Str("err", err.Error()).Msg("on acn send error")
				}
				return envelope, err
			}
			err = acn.SendAcnSuccess(aea.pipe)
			return envelope, err

		}
	case "status":
		{
			logger.Info().Msgf("acn status %d", status.Code)
			aea.acn_status_chan <- status
			logger.Info().Msgf("chan len is %d", len(aea.acn_status_chan))
			return nil, nil

		}
	default:
		{
			acn_err = acn.SendAcnError(aea.pipe, "BAD ACN MESSAGE")
			if acn_err != nil {
				logger.Error().Str("err", err.Error()).Msg("on acn send error")
			}
			return nil, errors.New("bad ACN message!")
		}
	}
}
