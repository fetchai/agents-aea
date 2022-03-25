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
	"context"
	"errors"
	"fmt"
	"log"
	"math"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"time"

	protocols "aealite/protocols"
	wallet "aealite/wallet"

	acn "aealite/connections/acn"

	"github.com/joho/godotenv"
	"github.com/rs/zerolog"
	proto "google.golang.org/protobuf/proto"
)

const retryAttempts = 5
const acnStatusTimeout = 5 * time.Second

var logger zerolog.Logger = zerolog.New(zerolog.ConsoleWriter{
	Out:        os.Stdout,
	NoColor:    false,
	TimeFormat: "15:04:05.000",
}).
	With().Timestamp().
	Str("package", "P2PClientApi").
	Logger()

var (
	DefaultAttempts      = uint(10)
	DefaultOnRetry       = func(n uint, err error) {}
	DefaultRetryIf       = IsRecoverable
	DefaultDelay         = 500 * time.Millisecond
	DefaultMaxJitter     = 100 * time.Millisecond
	DefaultDelayType     = CombineDelay(BackOffDelay, RandomDelay)
	DefaultLastErrorOnly = false
	DefaultContext       = context.Background()
	MaxDelay             = 1000 * time.Millisecond
)

type P2PClientConfig struct {
	host string
	port uint16
}

type P2PClientApi struct {
	clientConfig *P2PClientConfig
	agentRecord  *acn.AgentRecord

	socket   Socket
	outQueue chan *protocols.Envelope

	closing     bool
	connected   bool
	initialised bool

	acn_status_chan chan *acn.StatusBody
}

func (client *P2PClientApi) InitFromEnv(envFile string) error {
	zerolog.TimeFieldFormat = time.RFC3339Nano

	if client.connected {
		return nil
	}
	client.connected = false
	client.initialised = false

	logger.Debug().Msgf("env_file: %s", envFile)
	err := godotenv.Overload(envFile)
	if err != nil {
		log.Fatal("Error loading env file")
	}
	address := os.Getenv("AEA_ADDRESS")
	publicKey := os.Getenv("AEA_PUBLIC_KEY")
	agentRecord := &acn.AgentRecord{Address: address, PublicKey: publicKey}
	agentRecord.ServiceId = os.Getenv("AEA_P2P_POR_SERVICE_ID")
	agentRecord.LedgerId = os.Getenv("AEA_P2P_POR_LEDGER_ID")
	agentRecord.PeerPublicKey = os.Getenv("AEA_P2P_POR_PEER_PUBKEY")
	agentRecord.Signature = os.Getenv("AEA_P2P_POR_SIGNATURE")
	ok, err := wallet.VerifyLedgerSignature(
		agentRecord.LedgerId,
		[]byte(agentRecord.PeerPublicKey),
		agentRecord.Signature,
		agentRecord.PublicKey,
	)
	if err != nil {
		log.Fatal("Could not verify signature." + err.Error())
	}
	if !ok {
		log.Fatal("Invalid signature.")
	}
	client.agentRecord = agentRecord
	host := os.Getenv("AEA_P2P_DELEGATE_HOST")
	port := os.Getenv("AEA_P2P_DELEGATE_PORT")
	portConv, err := strconv.ParseUint(port, 10, 16)
	if err != nil {
		panic(err)
	}
	client.clientConfig = &P2PClientConfig{host: host, port: uint16(portConv)}

	client.socket = NewSocket(client.clientConfig.host, client.clientConfig.port, client.agentRecord.PeerPublicKey)
	client.initialised = true
	return nil
}

func (client *P2PClientApi) Put(envelope *protocols.Envelope) error {

	envelopeBytes, err := proto.Marshal(envelope)
	if err != nil {
		logger.Error().Str("err", err.Error()).Msgf("while serializing envelope: %s", envelope)
		return err
	}
	return acn.SendEnvelopeMessageAndWaitForStatus(client.socket, envelopeBytes, client.acn_status_chan, acnStatusTimeout)

}

func (client *P2PClientApi) Get() *protocols.Envelope {
	return <-client.outQueue
}

func (client *P2PClientApi) Queue() <-chan *protocols.Envelope {
	return client.outQueue
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
	close(client.outQueue)
	close(client.acn_status_chan)
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

	err = client.registerWithRetry()
	if err != nil {
		logger.Error().Str("err", err.Error()).
			Msg("while registering with retry to p2p node")
		err_ := client.stop()
		if err_ != nil {
			logger.Error().Str("err", err_.Error()).
				Msg("while handling other error")
		}
		return err
	}
	logger.Info().Msg("successfully registered on node")

	client.closing = false
	client.outQueue = make(chan *protocols.Envelope, 10)
	client.acn_status_chan = make(chan *acn.StatusBody, 10)
	go client.listenForEnvelopes()
	logger.Info().Msg("connected to p2p node")

	client.connected = true

	return nil
}

func (client *P2PClientApi) registerWithRetry() error {
	var n uint

	//default
	config := &Config{
		attempts:      DefaultAttempts,
		delay:         DefaultDelay,
		maxJitter:     DefaultMaxJitter,
		onRetry:       DefaultOnRetry,
		retryIf:       DefaultRetryIf,
		delayType:     DefaultDelayType,
		lastErrorOnly: DefaultLastErrorOnly,
		context:       DefaultContext,
	}

	var errorLog = make(Error, 1)
	context_ := context.Background()

	lastErrIndex := n
	for n < retryAttempts {
		err := client.register()

		if err != nil {
			errorLog[lastErrIndex] = unpackUnrecoverable(err)

			// if this is last attempt - don't wait
			if n == retryAttempts-1 {
				break
			}

			delayTime := config.delayType(n, err, config)
			if config.maxDelay > 0 && delayTime > config.maxDelay {
				delayTime = config.maxDelay
			}

			select {
			case <-time.After(delayTime):
			case <-context_.Done():
				return context_.Err()
			}

		} else {
			return nil
		}

		n++
	}
	return errorLog
}

func (client *P2PClientApi) register() error {
	return acn.SendAgentRegisterMessage(client.socket, client.agentRecord)
}

func (client *P2PClientApi) listenForEnvelopes() {
	for {
		envel, err := client.HandleAcnMessageFromPipe()

		if err != nil && !client.closing {
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
		if envel == nil {
			// got acn status, not an envelope
			continue
		}
		if envel.To != client.agentRecord.Address {
			logger.Error().
				Str("err", "To ("+envel.To+") must match registered address").
				Msg("while processing envelope")
			continue
		}
		logger.Debug().Msgf("received envelope for agent")
		client.outQueue <- envel
		if client.closing {
			return
		}
	}
}

func (client *P2PClientApi) stop() error {
	return client.socket.Disconnect()
}

// Error type represents list of errors in retry
type Error []error

// Error method return string representation of Error
// Implements error interface
func (e Error) Error() string {
	logWithNumber := make([]string, lenWithoutNil(e))
	for i, l := range e {
		if l != nil {
			logWithNumber[i] = fmt.Sprintf("#%d: %s", i+1, l.Error())
		}
	}

	return fmt.Sprintf("All attempts fail:\n%s", strings.Join(logWithNumber, "\n"))
}

func lenWithoutNil(e Error) (count int) {
	for _, v := range e {
		if v != nil {
			count++
		}
	}

	return
}

// WrappedErrors returns the list of errors that this Error is wrapping.
func (e Error) WrappedErrors() []error {
	return e
}

type unrecoverableError struct {
	error
}

// Unrecoverable wraps an error in `unrecoverableError` struct
func Unrecoverable(err error) error {
	return unrecoverableError{err}
}

// IsRecoverable checks if error is an instance of `unrecoverableError`
func IsRecoverable(err error) bool {
	_, isUnrecoverable := err.(unrecoverableError)
	return !isUnrecoverable
}

func unpackUnrecoverable(err error) error {
	if unrecoverable, isUnrecoverable := err.(unrecoverableError); isUnrecoverable {
		return unrecoverable.error
	}

	return err
}

// DelayTypeFunc is called to return the next delay to wait after the retriable function fails on `err` after `n` attempts.
type DelayTypeFunc func(n uint, err error, config *Config) time.Duration

// Function signature of retry if function
type RetryIfFunc func(error) bool

// Function signature of OnRetry function
// n = count of attempts
type OnRetryFunc func(n uint, err error)

type Config struct {
	attempts      uint
	delay         time.Duration
	maxDelay      time.Duration
	maxJitter     time.Duration
	onRetry       OnRetryFunc
	retryIf       RetryIfFunc
	delayType     DelayTypeFunc
	lastErrorOnly bool
	context       context.Context

	maxBackOffN uint
}

// CombineDelay is a DelayType the combines all of the specified delays into a new DelayTypeFunc
func CombineDelay(delays ...DelayTypeFunc) DelayTypeFunc {
	const maxInt64 = uint64(math.MaxInt64)

	return func(n uint, err error, config *Config) time.Duration {
		var total uint64
		for _, delay := range delays {
			total += uint64(delay(n, err, config))
			if total > maxInt64 {
				total = maxInt64
			}
		}

		return time.Duration(total)
	}
}

// BackOffDelay is a DelayType which increases delay between consecutive retries
func BackOffDelay(n uint, _ error, config *Config) time.Duration {
	// 1 << 63 would overflow signed int64 (time.Duration), thus 62.
	const max uint = 62

	if config.maxBackOffN == 0 {
		if config.delay <= 0 {
			config.delay = 1
		}

		config.maxBackOffN = max - uint(math.Floor(math.Log2(float64(config.delay))))
	}

	if n > config.maxBackOffN {
		n = config.maxBackOffN
	}

	return config.delay << n
}

// RandomDelay is a DelayType which picks a random delay up to config.maxJitter
func RandomDelay(_ uint, _ error, config *Config) time.Duration {
	return time.Duration(rand.Int63n(int64(config.maxJitter)))
}

func (client *P2PClientApi) HandleAcnMessageFromPipe() (*protocols.Envelope, error) {
	pipe := client.socket
	envelope := &protocols.Envelope{}
	var acn_err error

	data, err := pipe.Read()

	if err != nil {

		return nil, err
	}

	msg_type, acn_envelope, status, acnErr := acn.DecodeAcnMessage(data)

	if acnErr != nil {
		logger.Error().Str("err", acnErr.Error()).Msg("while handling acn message")
		acn_err = acn.SendAcnError(
			pipe,
			acnErr.Error(),
			acnErr.ErrorCode,
		)
		if acn_err != nil {
			logger.Error().Str("err", acn_err.Error()).Msg("on acn send error")
		}
		return envelope, acnErr
	}

	switch msg_type {
	case "aea_envelope":
		{
			err = proto.Unmarshal(acn_envelope.Envelope, envelope)
			if err != nil {
				logger.Error().Str("err", err.Error()).Msg("while decoding envelope")
				acn_err = acn.SendAcnError(
					pipe,
					"error on decoding envelope",
					acn.ERROR_DECODE,
				)
				if acn_err != nil {
					logger.Error().Str("err", acn_err.Error()).Msg("on acn send error")
				}
				return envelope, err
			}
			err = acn.SendAcnSuccess(pipe)
			return envelope, err

		}
	case "status":
		{
			logger.Debug().Msgf("got acn status %d", status.Code)
			client.acn_status_chan <- status
			return nil, nil

		}
	default:
		{
			acn_err = acn.SendAcnError(pipe, "Unsupported ACN message")
			if acn_err != nil {
				logger.Error().Str("err", acn_err.Error()).Msg("on acn send error")
			}
			return nil, errors.New("unsupported ACN message")
		}
	}
}
