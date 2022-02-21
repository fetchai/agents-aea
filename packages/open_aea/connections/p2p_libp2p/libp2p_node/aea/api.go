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

	"github.com/joho/godotenv"
	"github.com/rs/zerolog"
	proto "google.golang.org/protobuf/proto"

	acn "libp2p_node/acn"
	common "libp2p_node/common"
)

const AcnStatusTimeout = 15.0 * time.Second
const SendQueueSize = 100
const OutQueueSize = 100

// code redandency to avoid import cycle
var logger zerolog.Logger = zerolog.New(zerolog.ConsoleWriter{
	Out:        os.Stdout,
	NoColor:    false,
	TimeFormat: "15:04:05.000",
}).
	With().Timestamp().
	Str("package", "AeaApi").
	Logger()

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

	mailbox_uri string

	registrationDelay  float64
	recordsStoragePath string

	pipe       common.Pipe
	out_queue  chan *Envelope
	send_queue chan *Envelope

	closing         bool
	connected       bool
	sandbox         bool
	standalone      bool
	acn_status_chan chan *acn.StatusBody
}

func (aea AeaApi) MailboxUri() string {
	return aea.mailbox_uri
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

	aea.mailbox_uri = os.Getenv("AEA_P2P_MAILBOX_URI")
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

	aea.acn_status_chan = make(chan *acn.StatusBody, 1000)
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
	aea.out_queue = make(chan *Envelope, OutQueueSize)
	aea.send_queue = make(chan *Envelope, SendQueueSize)
	go aea.listenForEnvelopes()
	go aea.envelopeSendLoop()
	logger.Info().Msg("connected to agent")

	aea.connected = true

	return nil
}

func (aea *AeaApi) listenForEnvelopes() {
	//TOFIX(LR) add an exit strategy
	for {
		envel, err := HandleAcnMessageFromPipe(aea.pipe, aea, aea.AeaAddress())

		var e *common.PipeError

		if errors.As(err, &e) {
			logger.Error().
				Str("err", err.Error()).
				Msg("pipe error while receiving envelope. disconnect")
			logger.Info().Msg("disconnecting")

			if !aea.closing {
				aea.Stop()
			}

			return
		}
		if err != nil {
			logger.Error().Str("err", err.Error()).Msg("while receiving envelope. skip")
			continue
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
	err := aea.pipe.Close()
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("on pipe close during aeaapi stop")
	}
}

/*

  Pipes helpers

*/
const CurrentVersion = "0.1.0"

func MakeAcnMessageFromEnvelope(envelope *Envelope) ([]byte, error) {
	envelope_bytes, err := proto.Marshal(envelope)
	if err != nil {
		return envelope_bytes, err
	}
	return acn.EncodeAcnEnvelope(envelope_bytes, nil)
}

func (aea AeaApi) SendEnvelope(envelope *Envelope) error {
	return SendEnvelope(aea.pipe, aea.acn_status_chan, envelope, AcnStatusTimeout)
}

func SendEnvelope(
	pipe acn.Pipe,
	acn_status_chan chan *acn.StatusBody,
	envelope *Envelope,
	acnStatusTimeout time.Duration,
) error {
	envelope_bytes, err := proto.Marshal(envelope)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("while serializing envelope: %s", envelope.String())
		return err
	}
	err = acn.SendEnvelopeMessageAndWaitForStatus(
		pipe,
		envelope_bytes,
		acn_status_chan,
		acnStatusTimeout,
	)

	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msgf("on send envelope: %s", envelope.String())
		return err
	}
	return nil
}

func (aea AeaApi) AddAcnStatusMessage(status *acn.StatusBody, counterpartyID string) {
	aea.acn_status_chan <- status
	logger.Info().Msgf("chan len is %d", len(aea.acn_status_chan))
}
