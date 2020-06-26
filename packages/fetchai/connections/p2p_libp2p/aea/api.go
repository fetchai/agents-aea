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
	"encoding/binary"
	"errors"
	"log"
	"net"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
	"github.com/rs/zerolog"
	proto "google.golang.org/protobuf/proto"
)

var logger zerolog.Logger = zerolog.New(zerolog.ConsoleWriter{Out: os.Stdout, NoColor: false}).
	With().Timestamp().
	Str("package", "AeaApi").
	Logger()

/*

  AeaApi type

*/

type AeaApi struct {
	msgin_path    string
	msgout_path   string
	agent_addr    string
	id            string
	entry_peers   []string
	host          string
	port          uint16
	host_public   string
	port_public   uint16
	host_delegate string
	port_delegate uint16
	msgin         *os.File
	msgout        *os.File
	out_queue     chan *Envelope
	closing       bool
	connected     bool
	sandbox       bool
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

func (aea AeaApi) EntryPeers() []string {
	return aea.entry_peers
}

func (aea AeaApi) Put(envelope *Envelope) error {
	return write_envelope(aea.msgout, envelope)
}

func (aea *AeaApi) Get() *Envelope {
	return <-aea.out_queue
}

func (aea *AeaApi) Queue() <-chan *Envelope {
	return aea.out_queue
}

func (aea *AeaApi) Connected() bool {
	return aea.connected
}

func (aea *AeaApi) Stop() {
	aea.closing = true
	aea.stop()
	close(aea.out_queue)
}

func (aea *AeaApi) Init() error {
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
	err := godotenv.Load(env_file)
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
	logger.Debug().Msgf("msgin_path: %s", aea.msgin_path)
	logger.Debug().Msgf("msgout_path: %s", aea.msgout_path)
	logger.Debug().Msgf("id: %s", aea.id)
	logger.Debug().Msgf("addr: %s", aea.agent_addr)
	logger.Debug().Msgf("entry_peers: %s", entry_peers)
	logger.Debug().Msgf("uri: %s", uri)
	logger.Debug().Msgf("uri public: %s", uri_public)
	logger.Debug().Msgf("uri delegate service: %s", uri_delegate)

	if aea.msgin_path == "" || aea.msgout_path == "" || aea.id == "" || uri == "" {
		err := errors.New("couldn't get AEA configuration")
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

	// parse entry peers multiaddrs
	if len(entry_peers) > 0 {
		aea.entry_peers = strings.SplitN(entry_peers, ",", -1)
	}

	return nil
}

func (aea *AeaApi) Connect() error {
	// open pipes
	var erro, erri error
	aea.msgout, erro = os.OpenFile(aea.msgout_path, os.O_WRONLY, os.ModeNamedPipe)
	aea.msgin, erri = os.OpenFile(aea.msgin_path, os.O_RDONLY, os.ModeNamedPipe)

	if erri != nil || erro != nil {
		logger.Error().Str("err", erri.Error()).Str("err", erro.Error()).
			Msgf("while opening pipes %s %s", aea.msgin_path, aea.msgout_path)
		if erri != nil {
			return erri
		}
		return erro
	}

	aea.closing = false
	//TOFIX(LR) trade-offs between bufferd vs unbuffered channel
	aea.out_queue = make(chan *Envelope, 10)
	go aea.listen_for_envelopes()
	logger.Info().Msg("connected to agent")

	aea.connected = true

	return nil
}

/*
func (aea *AeaApi) WithSandbox() *AeaApi {
	var err error
	fmt.Println("[aea-api  ][warning] running in sandbox mode")
	aea.msgin_path, aea.msgout_path, aea.id, aea.host, aea.port, err = setup_aea_sandbox()
	if err != nil {
		return nil
	}
	aea.sandbox = true
	return aea
}
*/

func UnmarshalEnvelope(buf []byte) (*Envelope, error) {
	envelope := &Envelope{}
	err := proto.Unmarshal(buf, envelope)
	return envelope, err
}

func (aea *AeaApi) listen_for_envelopes() {
	//TOFIX(LR) add an exit strategy
	for {
		envel, err := read_envelope(aea.msgin)
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
	aea.msgin.Close()
	aea.msgout.Close()
}

/*

  Pipes helpers

*/

func write(pipe *os.File, data []byte) error {
	size := uint32(len(data))
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, size)
	_, err := pipe.Write(buf)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while writing size to pipe: %d %x", size, buf)
		return err
	}
	logger.Debug().Msgf("writing size to pipe %d %x", size, buf)
	_, err = pipe.Write(data)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while writing data to pipe %x", data)
	}
	logger.Debug().Msgf("writing data to pipe len %d", size)
	return err
}

func read(pipe *os.File) ([]byte, error) {
	buf := make([]byte, 4)
	_, err := pipe.Read(buf)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving size")
		return buf, err
	}
	size := binary.BigEndian.Uint32(buf)

	buf = make([]byte, size)
	_, err = pipe.Read(buf)
	return buf, err
}

func write_envelope(pipe *os.File, envelope *Envelope) error {
	data, err := proto.Marshal(envelope)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while serializing envelope: %s", envelope)
		return err
	}
	return write(pipe, data)
}

func read_envelope(pipe *os.File) (*Envelope, error) {
	envelope := &Envelope{}
	data, err := read(pipe)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msg("while receiving data")
		return envelope, err
	}
	err = proto.Unmarshal(data, envelope)
	return envelope, err
}

/*

  Sandbox
  - DISABLED

*/

/*
func setup_aea_sandbox() (string, string, string, string, uint16, error) {
	// setup id
	id := ""
	// setup uri
	host := "127.0.0.1"
	port := uint16(5000 + rand.Intn(10000))
	// setup pipes
	ROOT_PATH := "/tmp/aea_sandbox_" + strconv.FormatInt(time.Now().Unix(), 10)
	msgin_path := ROOT_PATH + ".in"
	msgout_path := ROOT_PATH + ".out"
	// create pipes
	if _, err := os.Stat(msgin_path); !os.IsNotExist(err) {
		os.Remove(msgin_path)
	}
	if _, err := os.Stat(msgout_path); !os.IsNotExist(err) {
		os.Remove(msgout_path)
	}
	erri := syscall.Mkfifo(msgin_path, 0666)
	erro := syscall.Mkfifo(msgout_path, 0666)
	if erri != nil || erro != nil {
		fmt.Println("[aea-api  ][error][sandbox] setting up pipes:", erri, erro)
		if erri != nil {
			return "", "", "", "", 0, erri
		}
		return "", "", "", "", 0, erro
	}
	// TOFIX(LR) should use channels
	go func() {
		err := run_aea_sandbox(msgin_path, msgout_path)
		if err != nil {
		}
	}()
	return msgin_path, msgout_path, id, host, port, nil
}

func run_aea_sandbox(msgin_path string, msgout_path string) error {
	// open pipe
	msgout, erro := os.OpenFile(msgout_path, os.O_RDONLY, os.ModeNamedPipe)
	msgin, erri := os.OpenFile(msgin_path, os.O_WRONLY, os.ModeNamedPipe)
	if erri != nil || erro != nil {
		fmt.Println("[aea-api  ][error][sandbox] error while opening pipes:", erri, erro)
		if erri != nil {
			return erri
		} else {
			return erro
		}
	}

	// consume envelopes
	go func() {
		for {
			envel, err := read_envelope(msgout)
			if err != nil {
				fmt.Println("[aea-api  ][error][sandbox] stopped receiving envelopes:", err)
				return
			}
			fmt.Println("[aea-api  ][error][sandbox] consumed envelope", envel)
		}
	}()

	// produce envelopes
	go func() {
		i := 1
		for {
			time.Sleep(time.Duration((rand.Intn(5000) + 3000)) * time.Millisecond)
			envel := &Envelope{"aea-sandbox", "golang", "fetchai/default:0.3.0", []byte("\x08\x01*\x07\n\x05Message from sandbox " + strconv.Itoa(i)), ""}
			err := write_envelope(msgin, envel)
			if err != nil {
				fmt.Println("[aea-api  ][error][sandbox] stopped producing envelopes:", err)
				return
			}
			i += 1
		}
	}()

	return nil
}
*/
