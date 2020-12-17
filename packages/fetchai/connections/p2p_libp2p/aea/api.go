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
)

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

	registrationDelay float64

	pipe      Pipe
	out_queue chan *Envelope

	closing    bool
	connected  bool
	sandbox    bool
	standalone bool
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

func (aea AeaApi) RegistrationDelayInSeconds() float64 {
	return aea.registrationDelay
}

func (aea AeaApi) Put(envelope *Envelope) error {
	if aea.standalone {
		errorMsg := "node running in standalone mode"
		logger.Warn().Msgf(errorMsg)
		return errors.New(errorMsg)
	}
	return write_envelope(aea.pipe, envelope)
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
	aea.closing = true
	aea.stop()
	close(aea.out_queue)
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
	registrationDelay := os.Getenv("AEA_P2P_CFG_REGISTRATION_DELAY")

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

	// parse entry peers multiaddrs
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
	go aea.listen_for_envelopes()
	logger.Info().Msg("connected to agent")

	aea.connected = true

	return nil
}

func UnmarshalEnvelope(buf []byte) (*Envelope, error) {
	envelope := &Envelope{}
	err := proto.Unmarshal(buf, envelope)
	return envelope, err
}

func (aea *AeaApi) listen_for_envelopes() {
	//TOFIX(LR) add an exit strategy
	for {
		envel, err := read_envelope(aea.pipe)
		if err != nil {
			logger.Error().Str("err", err.Error()).Msg("while receiving envelope")
			logger.Info().Msg("disconnecting")
			// TOFIX(LR) see above
			if !aea.closing {
				aea.stop()
			}
			return
		}
		logger.Debug().Msgf("received envelope from agent")
		aea.out_queue <- envel
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

func write_envelope(pipe Pipe, envelope *Envelope) error {
	data, err := proto.Marshal(envelope)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while serializing envelope: %s", envelope)
		return err
	}
	return pipe.Write(data)
}

func read_envelope(pipe Pipe) (*Envelope, error) {
	envelope := &Envelope{}
	data, err := pipe.Read()
	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving data")
		return envelope, err
	}
	err = proto.Unmarshal(data, envelope)
	return envelope, err
}
