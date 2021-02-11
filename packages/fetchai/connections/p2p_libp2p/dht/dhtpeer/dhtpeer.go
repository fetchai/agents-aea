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

// Package dhtpeer provides implementation of an Agent Communication Network node
// using libp2p. It participates in data storage and routing for the network.
// It offers RelayService for dhtclient and DelegateService for tcp clients.
package dhtpeer

import (
	"bufio"
	"context"
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/pkg/errors"

	"github.com/rs/zerolog"
	"google.golang.org/protobuf/proto"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/libp2p/go-libp2p-core/peerstore"
	"github.com/multiformats/go-multiaddr"

	circuit "github.com/libp2p/go-libp2p-circuit"
	kaddht "github.com/libp2p/go-libp2p-kad-dht"
	routedhost "github.com/libp2p/go-libp2p/p2p/host/routed"

	aea "libp2p_node/aea"
	"libp2p_node/dht/dhtnode"
	monitoring "libp2p_node/dht/monitoring"
	utils "libp2p_node/utils"
)

// panics if err is not nil
func check(err error) {
	if err != nil {
		panic(err)
	}
}

func ignore(err error) {
	if err != nil {
		log.Println("IGNORED", err)
	}
}

const (
	addressLookupTimeout                 = 20 * time.Second
	routingTableConnectionUpdateTimeout  = 5 * time.Second
	newStreamTimeout                     = 5 * time.Second
	addressRegisterTimeout               = 3 * time.Second
	addressRegistrationDelay             = 0 * time.Second
	monitoringNamespace                  = "acn"
	metricDHTOpLatencyStore              = "dht_op_latency_store"
	metricDHTOpLatencyLookup             = "dht_op_latency_lookup"
	metricOpLatencyRegister              = "op_latency_register"
	metricOpLatencyRoute                 = "op_latency_route"
	metricOpRouteCount                   = "op_route_count"
	metricOpRouteCountAll                = "op_route_count_all"
	metricOpRouteCountSuccess            = "op_route_count_success"
	metricServiceDelegateClientsCount    = "service_delegate_clients_count"
	metricServiceDelegateClientsCountAll = "service_delegate_clients_count_all"
	metricServiceRelayClientsCount       = "service_relay_clients_count"
	metricServiceRelayClientsCountAll    = "service_relay_clients_count_all"
	defaultPersistentStoragePath         = "./agent_records_store"
)

var (
	//latencyBucketsMilliSeconds = []float64{1., 10., 20., 50., 100., 200., 500., 1000.}
	latencyBucketsMicroSeconds = []float64{100., 500., 1e3, 1e4, 1e5, 5e5, 1e6}
)

// DHTPeer A full libp2p node for the Agents Communication Network.
// It is required to have a local address and a public one
// and can acts as a relay for `DHTClient`.
// Optionally, it provides delegate service for tcp clients.
type DHTPeer struct {
	host           string
	port           uint16
	publicHost     string
	publicPort     uint16
	delegatePort   uint16
	monitoringPort uint16
	enableRelay    bool

	registrationDelay time.Duration

	key             crypto.PrivKey
	publicKey       crypto.PubKey
	localMultiaddr  multiaddr.Multiaddr
	publicMultiaddr multiaddr.Multiaddr
	bootstrapPeers  []peer.AddrInfo

	dht         *kaddht.IpfsDHT
	routedHost  *routedhost.RoutedHost
	tcpListener net.Listener

	addressAnnounced bool
	myAgentAddress   string
	myAgentRecord    *dhtnode.AgentRecord
	myAgentReady     func() bool
	dhtAddresses     map[string]string
	tcpAddresses     map[string]net.Conn
	agentRecords     map[string]*dhtnode.AgentRecord
	dhtAddressesLock sync.RWMutex
	tcpAddressesLock sync.RWMutex
	agentRecordsLock sync.RWMutex
	// TOFIX(LR): maps and locks need refactoring for better abstraction
	processEnvelope func(*aea.Envelope) error

	persistentStoragePath string
	storage               *os.File

	monitor    monitoring.MonitoringService
	closing    chan struct{}
	goroutines *sync.WaitGroup
	logger     zerolog.Logger
}

// New creates a new DHTPeer
func New(opts ...Option) (*DHTPeer, error) {
	var err error
	dhtPeer := &DHTPeer{registrationDelay: addressRegistrationDelay}

	dhtPeer.dhtAddresses = map[string]string{}
	dhtPeer.tcpAddresses = map[string]net.Conn{}
	dhtPeer.agentRecords = map[string]*dhtnode.AgentRecord{}
	dhtPeer.dhtAddressesLock = sync.RWMutex{}
	dhtPeer.tcpAddressesLock = sync.RWMutex{}
	dhtPeer.agentRecordsLock = sync.RWMutex{}
	dhtPeer.persistentStoragePath = defaultPersistentStoragePath

	for _, opt := range opts {
		if err := opt(dhtPeer); err != nil {
			return nil, err
		}
	}
	dhtPeer.closing = make(chan struct{})
	dhtPeer.goroutines = &sync.WaitGroup{}

	/* check correct configuration */

	// private key
	if dhtPeer.key == nil {
		return nil, errors.New("private key must be provided")
	}

	// local uri
	if dhtPeer.localMultiaddr == nil {
		return nil, errors.New("local host and port must be set")
	}

	// public uri
	if dhtPeer.publicMultiaddr == nil {
		return nil, errors.New("public host and port must be set")
	}

	// check if the PoR is delivered for my public  key
	if dhtPeer.myAgentRecord != nil {
		myPublicKey, err := utils.FetchAIPublicKeyFromPubKey(dhtPeer.publicKey)
		status, errPoR := dhtnode.IsValidProofOfRepresentation(
			dhtPeer.myAgentRecord, dhtPeer.myAgentRecord.Address, myPublicKey,
		)
		if err != nil || errPoR != nil || status.Code != dhtnode.Status_SUCCESS {
			errMsg := "Invalid AgentRecord"
			if err == nil {
				err = errors.New(errMsg)
			} else {
				err = errors.Wrap(err, errMsg)
			}
			if errPoR != nil {
				err = errors.Wrap(err, errPoR.Error())
			}
			return nil, err
		}
	}

	/* setup libp2p node */
	ctx := context.Background()

	// setup public uri as external address
	addressFactory := func(addrs []multiaddr.Multiaddr) []multiaddr.Multiaddr {
		return []multiaddr.Multiaddr{dhtPeer.publicMultiaddr}
	}

	// libp2p options
	libp2pOpts := []libp2p.Option{
		libp2p.ListenAddrs(dhtPeer.localMultiaddr),
		libp2p.AddrsFactory(addressFactory),
		libp2p.Identity(dhtPeer.key),
		libp2p.DefaultTransports,
		libp2p.DefaultMuxers,
		libp2p.DefaultSecurity,
		libp2p.NATPortMap(),
		libp2p.EnableNATService(),
		libp2p.EnableRelay(circuit.OptHop),
	}

	// create a basic host
	basicHost, err := libp2p.New(ctx, libp2pOpts...)
	if err != nil {
		return nil, err
	}

	// create the dht
	dhtPeer.dht, err = kaddht.New(ctx, basicHost, kaddht.Mode(kaddht.ModeServer))
	if err != nil {
		return nil, err
	}

	// make the routed host
	dhtPeer.routedHost = routedhost.Wrap(basicHost, dhtPeer.dht)
	dhtPeer.setupLogger()

	lerror, _, linfo, ldebug := dhtPeer.getLoggers()

	// connect to the booststrap nodes
	if len(dhtPeer.bootstrapPeers) > 0 {
		linfo().Msgf("Bootstrapping from %s", dhtPeer.bootstrapPeers)
		err = utils.BootstrapConnect(ctx, dhtPeer.routedHost, dhtPeer.dht, dhtPeer.bootstrapPeers)
		if err != nil {
			dhtPeer.Close()
			return nil, err
		}
	}

	// bootstrap the dht
	err = dhtPeer.dht.Bootstrap(ctx)
	if err != nil {
		dhtPeer.Close()
		return nil, err
	}

	linfo().Msg("INFO My ID is ")

	linfo().Msg("successfully created libp2p node!")

	/* setup DHTPeer message handlers and services */

	// setup monitoring
	dhtPeer.setupMonitoring()

	// relay service
	if dhtPeer.enableRelay {
		// Allow clients to register their agents addresses
		ldebug().Msg("Setting /aea-register/0.1.0 stream...")
		dhtPeer.routedHost.SetStreamHandler(dhtnode.AeaRegisterRelayStream,
			dhtPeer.handleAeaRegisterStream)
	}

	// new peers connection notification, so that this peer can register its addresses
	dhtPeer.routedHost.SetStreamHandler(dhtnode.AeaNotifStream,
		dhtPeer.handleAeaNotifStream)

	// Notify bootstrap peers if any
	for _, bPeer := range dhtPeer.bootstrapPeers {
		ctx := context.Background()
		s, err := dhtPeer.routedHost.NewStream(ctx, bPeer.ID, dhtnode.AeaNotifStream)
		if err != nil {
			lerror(err).Msgf("failed to open stream to notify bootstrap peer %s", bPeer.ID)
			dhtPeer.Close()
			return nil, err
		}
		_, err = s.Write([]byte(dhtnode.AeaNotifStream))
		if err != nil {
			lerror(err).Msgf("failed to notify bootstrap peer %s", bPeer.ID)
			dhtPeer.Close()
			return nil, err
		}
		s.Close()
	}

	// initialize agents records persistent storage
	if dhtPeer.persistentStoragePath == defaultPersistentStoragePath {
		myPeerID, err := peer.IDFromPublicKey(dhtPeer.publicKey)
		ignore(err)
		dhtPeer.persistentStoragePath += "_" + myPeerID.Pretty()
	}
	nbr, err := dhtPeer.initAgentRecordPersistentStorage()
	if err != nil {
		return nil, errors.Wrap(err, "while initializing agent record storage")
	}
	if len(dhtPeer.bootstrapPeers) > 0 {
		for addr := range dhtPeer.dhtAddresses {
			err := dhtPeer.registerAgentAddress(addr)
			if err != nil {
				lerror(err).Str("addr", addr).
					Msg("while announcing stored client address")
			}
		}
	}
	linfo().Msgf("successfully loaded %d agents", nbr)

	// if peer is joining an existing network, announce my agent address if set
	if len(dhtPeer.bootstrapPeers) > 0 {
		dhtPeer.addressAnnounced = true
		if dhtPeer.myAgentAddress != "" {
			opLatencyRegister, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRegister)
			timer := dhtPeer.monitor.Timer()
			start := timer.NewTimer()
			err := dhtPeer.registerAgentAddress(dhtPeer.myAgentAddress)
			if err != nil {
				dhtPeer.Close()
				return nil, err
			}
			duration := timer.GetTimer(start)
			opLatencyRegister.Observe(float64(duration.Microseconds()))
		}
	}

	// aea addresses lookup
	ldebug().Msg("Setting /aea-address/0.1.0 stream...")
	dhtPeer.routedHost.SetStreamHandler(dhtnode.AeaAddressStream, dhtPeer.handleAeaAddressStream)

	// incoming envelopes stream
	ldebug().Msg("Setting /aea/0.1.0 stream...")
	dhtPeer.routedHost.SetStreamHandler(dhtnode.AeaEnvelopeStream, dhtPeer.handleAeaEnvelopeStream)

	// setup delegate service
	if dhtPeer.delegatePort != 0 {
		dhtPeer.launchDelegateService()

		ready := &sync.WaitGroup{}
		dhtPeer.goroutines.Add(1)
		ready.Add(1)
		go dhtPeer.handleDelegateService(ready)
		ready.Wait()
	}

	// start monitoring
	ready := &sync.WaitGroup{}
	ready.Add(1)
	go dhtPeer.startMonitoring(ready)
	ready.Wait()

	return dhtPeer, nil
}

func (dhtPeer *DHTPeer) saveAgentRecordToPersistentStorage(record *dhtnode.AgentRecord) error {
	msg := formatPersistentStorageLine(record)
	if len(msg) == 0 {
		return errors.New("while formating record " + record.String())
	}

	size := uint32(len(msg))
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, size)

	buf = append(buf, msg...)
	_, err := dhtPeer.storage.Write(buf)
	if err != nil {
		return errors.Wrap(err, "while writing record to persistent storage")
	}
	return nil
}

func parsePersistentStorageLine(line []byte) (*dhtnode.AgentRecord, error) {
	record := &dhtnode.AgentRecord{}
	err := proto.Unmarshal(line, record)
	return record, err
}

func formatPersistentStorageLine(record *dhtnode.AgentRecord) []byte {
	msg, err := proto.Marshal(record)
	ignore(err)
	return msg
}

func (dhtPeer *DHTPeer) initAgentRecordPersistentStorage() (int, error) {
	var err error
	dhtPeer.storage, err = os.OpenFile(dhtPeer.persistentStoragePath, os.O_APPEND|os.O_RDWR|os.O_CREATE, 0600)
	if err != nil {
		return 0, err
	}

	reader := bufio.NewReader(dhtPeer.storage)
	var counter int = 0
	for {
		buf := make([]byte, 4)
		_, err = io.ReadFull(reader, buf)
		if err == io.EOF {
			break
		}
		if err != nil {
			return 0, errors.Wrap(err, "while loading agent records")
		}

		size := binary.BigEndian.Uint32(buf)
		line := make([]byte, size)
		_, err = io.ReadFull(reader, line)
		if err != nil {
			return 0, errors.Wrap(err, "while loading agent records")
		}

		record, err := parsePersistentStorageLine(line)
		if err != nil {
			return 0, errors.Wrap(err, "while loading agent records")
		}
		dhtPeer.agentRecords[record.Address] = record
		relayPeerID, err := utils.IDFromFetchAIPublicKey(record.PeerPublicKey)
		if err != nil {
			return 0, errors.Wrap(err, "While loading agent records")
		}
		dhtPeer.dhtAddresses[record.Address] = relayPeerID.Pretty()
		counter++
	}

	return counter, nil
}

func (dhtPeer *DHTPeer) closeAgentRecordPersistentStorage() error {
	dhtPeer.agentRecordsLock.Lock()
	err := dhtPeer.storage.Close()
	dhtPeer.agentRecordsLock.Unlock()
	return err
}

func (dhtPeer *DHTPeer) setupMonitoring() {
	if dhtPeer.monitoringPort != 0 {
		dhtPeer.monitor = monitoring.NewPrometheusMonitoring(
			monitoringNamespace,
			dhtPeer.monitoringPort,
		)
	} else {
		dhtPeer.monitor = monitoring.NewFileMonitoring(monitoringNamespace, false)
	}

	dhtPeer.addMonitoringMetrics()
}

func (dhtPeer *DHTPeer) startMonitoring(ready *sync.WaitGroup) {
	_, _, linfo, _ := dhtPeer.getLoggers()
	linfo().Msg("Starting monitoring service: " + dhtPeer.monitor.Info())
	go dhtPeer.monitor.Start()
	ready.Done()
}

func (dhtPeer *DHTPeer) addMonitoringMetrics() {
	buckets := latencyBucketsMicroSeconds
	var err error
	// acn primitives
	_, err = dhtPeer.monitor.NewHistogram(metricDHTOpLatencyStore,
		"Histogram for time to store a key in the DHT", buckets)
	ignore(err)
	_, err = dhtPeer.monitor.NewHistogram(metricDHTOpLatencyLookup,
		"Histogram for time to find a key in the DHT", buckets)
	ignore(err)
	// acn main service
	_, err = dhtPeer.monitor.NewHistogram(metricOpLatencyRegister,
		"Histogram for end-to-end time to register an agent in the acn", buckets)
	ignore(err)
	_, err = dhtPeer.monitor.NewHistogram(
		metricOpLatencyRoute,
		"Histogram for end-to-end time to route an envelope to its destination, excluding time to send envelope itself",
		buckets,
	)
	ignore(err)
	_, err = dhtPeer.monitor.NewGauge(metricOpRouteCount,
		"Number of ongoing envelope routing requests")
	ignore(err)
	_, err = dhtPeer.monitor.NewCounter(metricOpRouteCountAll,
		"Total number envelope routing requests, successful or not")
	ignore(err)
	_, err = dhtPeer.monitor.NewCounter(metricOpRouteCountSuccess,
		"Total number envelope routed successfully")
	ignore(err)
	// acn delegate service
	_, err = dhtPeer.monitor.NewGauge(metricServiceDelegateClientsCount,
		"Number of active delagate connections")
	ignore(err)
	_, err = dhtPeer.monitor.NewCounter(metricServiceDelegateClientsCountAll,
		"Number of all delagate clients, connected or disconnected")
	ignore(err)
	// acn relay service
	_, err = dhtPeer.monitor.NewGauge(metricServiceRelayClientsCount,
		"Number of active relay clients")
	ignore(err)
	_, err = dhtPeer.monitor.NewCounter(metricServiceRelayClientsCountAll,
		"Total number of all relayed clients, connected or disconnected")
	ignore(err)
}

func (dhtPeer *DHTPeer) setupLogger() {
	fields := map[string]string{
		"package": "DHTPeer",
	}
	if dhtPeer.routedHost != nil {
		fields["peerid"] = dhtPeer.routedHost.ID().Pretty()
	}
	dhtPeer.logger = utils.NewDefaultLoggerWithFields(fields)
}

func (dhtPeer *DHTPeer) getLoggers() (func(error) *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event) {
	ldebug := dhtPeer.logger.Debug
	linfo := dhtPeer.logger.Info
	lwarn := dhtPeer.logger.Warn
	lerror := func(err error) *zerolog.Event {
		if err == nil {
			return dhtPeer.logger.Error().Str("err", "nil")
		}
		return dhtPeer.logger.Error().Str("err", err.Error())
	}

	return lerror, lwarn, linfo, ldebug
}

// SetLogLevel set utils logger level
func (dhtPeer *DHTPeer) SetLogLevel(lvl zerolog.Level) {
	dhtPeer.logger = dhtPeer.logger.Level(lvl)
}

// Close stops the DHTPeer
func (dhtPeer *DHTPeer) Close() []error {
	var err error
	var status []error

	_, _, linfo, _ := dhtPeer.getLoggers()

	linfo().Msg("Stopping DHTPeer...")
	close(dhtPeer.closing)
	//return status

	errappend := func(err error) {
		if err != nil {
			status = append(status, err)
		}
	}

	if dhtPeer.tcpListener != nil {
		err = dhtPeer.tcpListener.Close()
		errappend(err)
		for _, conn := range dhtPeer.tcpAddresses {
			err = conn.Close()
			errappend(err)
		}
	}

	err = dhtPeer.dht.Close()
	errappend(err)
	err = dhtPeer.routedHost.Close()
	errappend(err)

	err = dhtPeer.closeAgentRecordPersistentStorage()
	errappend(err)

	//linfo().Msg("Stopping DHTPeer: waiting for goroutines to cancel...")
	//dhtPeer.goroutines.Wait()

	return status
}

func (dhtPeer *DHTPeer) launchDelegateService() {
	var err error

	lerror, _, _, _ := dhtPeer.getLoggers()

	uri := dhtPeer.host + ":" + strconv.FormatInt(int64(dhtPeer.delegatePort), 10)
	dhtPeer.tcpListener, err = net.Listen("tcp", uri)
	if err != nil {
		lerror(err).Msgf("while setting up listening tcp socket %s", uri)
		check(err)
	}
}

func (dhtPeer *DHTPeer) handleDelegateService(ready *sync.WaitGroup) {
	defer dhtPeer.goroutines.Done()
	defer dhtPeer.tcpListener.Close()

	lerror, _, linfo, _ := dhtPeer.getLoggers()

	done := false
	for {
		select {
		default:
			linfo().Msg("DelegateService listening for new connections...")
			if !done {
				done = true
				ready.Done()
			}
			conn, err := dhtPeer.tcpListener.Accept()
			if err != nil {
				if strings.Contains(err.Error(), "use of closed network connection") {
					// About using string comparison to get the type of err,
					// check https://github.com/golang/go/issues/4373
					linfo().Msg("DelegateService Stopped.")
				} else {
					lerror(err).Msgf("while accepting a new connection")
				}
			} else {
				dhtPeer.goroutines.Add(1)
				go dhtPeer.handleNewDelegationConnection(conn)
			}
		case <-dhtPeer.closing:
			break
		}
	}
}

func (dhtPeer *DHTPeer) handleNewDelegationConnection(conn net.Conn) {
	defer dhtPeer.goroutines.Done()
	defer conn.Close()

	// to limit spamming
	time.Sleep(dhtPeer.registrationDelay)

	nbrConns, _ := dhtPeer.monitor.GetGauge(metricServiceDelegateClientsCount)
	nbrClients, _ := dhtPeer.monitor.GetCounter(metricServiceDelegateClientsCountAll)
	opLatencyRegister, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRegister)
	timer := dhtPeer.monitor.Timer()
	start := timer.NewTimer()

	lerror, _, linfo, _ := dhtPeer.getLoggers()

	//linfo().Msgf("received a new connection from %s", conn.RemoteAddr().String())

	// read agent registration message
	buf, err := utils.ReadBytesConn(conn)
	if err != nil {
		lerror(err).Msg("while receiving agent's registration request")
		nbrConns.Dec()
		return
	}

	msg := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		lerror(err).Msg("couldn't deserialize acn registration message")
		// TOFIX(LR) setting Msgs to err.Error is potentially a security vulnerability
		status := &dhtnode.Status{
			Code: dhtnode.Status_ERROR_SERIALIZATION,
			Msgs: []string{err.Error()},
		}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytesConn(conn, buf)
		ignore(err)

		nbrConns.Dec()
		return
	}

	linfo().Msgf("Received registration request %s", msg)

	// Get Register message
	var register *dhtnode.Register
	switch pl := msg.Payload.(type) {
	case *dhtnode.AcnMessage_Register:
		register = pl.Register
	default:
		err = errors.New("Unexpected payload")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNEXPECTED_PAYLOAD, Msgs: []string{err.Error()}}
		response := &dhtnode.AcnMessage{Version: dhtnode.CurrentVersion, Payload: &dhtnode.AcnMessage_Status{Status: status}}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytesConn(conn, buf)
		ignore(err)

		nbrConns.Dec()
		return
	}
	record := register.Record
	addr := record.Address

	linfo().Msgf("connection from %s established for Address %s",
		conn.RemoteAddr().String(), addr)

	// check if the PoR is valid
	myPubKey, err := utils.FetchAIPublicKeyFromPubKey(dhtPeer.publicKey)
	ignore(err)
	status, err := dhtnode.IsValidProofOfRepresentation(record, addr, myPubKey)
	if err != nil || status.Code != dhtnode.Status_SUCCESS {
		lerror(err).Msg("PoR is not valid")
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytesConn(conn, buf)
		ignore(err)

		nbrConns.Dec()
		return
	}

	// TOFIX(LR) post-pone answer until address successfully registered
	msg = &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_Status{Status: status},
	}
	buf, err = proto.Marshal(msg)
	ignore(err)
	err = utils.WriteBytesConn(conn, buf)
	if err != nil {
		nbrConns.Dec()
		return
	}

	// Add connection to map
	dhtPeer.agentRecordsLock.Lock()
	dhtPeer.agentRecords[addr] = record
	dhtPeer.agentRecordsLock.Unlock()
	dhtPeer.tcpAddressesLock.Lock()
	dhtPeer.tcpAddresses[addr] = conn
	dhtPeer.tcpAddressesLock.Unlock()
	if dhtPeer.addressAnnounced {
		//linfo().Msgf("announcing tcp client address %s...", addr)
		// TOFIX(LR) disconnect client?
		err = dhtPeer.registerAgentAddress(addr)
		if err != nil {
			lerror(err).Msgf("while announcing tcp client address %s to the dht", addr)
			return
		}
	}

	duration := timer.GetTimer(start)
	opLatencyRegister.Observe(float64(duration.Microseconds()))

	nbrConns.Inc()
	nbrClients.Inc()

	for {
		// read envelopes
		envel, err := utils.ReadEnvelopeConn(conn)
		if err != nil {
			if err == io.EOF {
				linfo().Str(
					"addr",
					addr,
				).Msgf(
					"connection closed by client: %s, stopping...",
					err.Error(),
				)
			} else {
				lerror(err).Str("addr", addr).Msg("while reading envelope from client connection, aborting...")
			}
			nbrConns.Dec()
			break
		}

		// route envelope
		dhtPeer.goroutines.Add(1)
		go func() {
			defer dhtPeer.goroutines.Done()
			if envel.Sender != addr {
				err = errors.New("Sender (" + envel.Sender + ") must match registered address")
				lerror(err).Str("addr", addr).
					Msg("while routing delegate client envelope")
			} else {
				err := dhtPeer.RouteEnvelope(envel)
				if err != nil {
					lerror(err).Str("addr", addr).
						Msg("while routing delegate client envelope")
					// TODO() send error back
				}
			}
		}()
	}

	// Remove connection from map
	dhtPeer.tcpAddressesLock.Lock()
	delete(dhtPeer.tcpAddresses, addr)
	dhtPeer.tcpAddressesLock.Unlock()
	// TOFIX(LR) currently I am keeping the agent record

}

// ProcessEnvelope register callback function
func (dhtPeer *DHTPeer) ProcessEnvelope(fn func(*aea.Envelope) error) {
	dhtPeer.processEnvelope = fn
}

// MultiAddr libp2p multiaddr of the peer
func (dhtPeer *DHTPeer) MultiAddr() string {
	multiAddr, _ := multiaddr.NewMultiaddr(
		fmt.Sprintf("/p2p/%s", dhtPeer.routedHost.ID().Pretty()))
	addrs := dhtPeer.routedHost.Addrs()
	if len(addrs) == 0 {
		return ""
	}
	return addrs[0].Encapsulate(multiAddr).String()
}

// RouteEnvelope to its destination
func (dhtPeer *DHTPeer) RouteEnvelope(envel *aea.Envelope) error {
	lerror, lwarn, linfo, ldebug := dhtPeer.getLoggers()

	routeCount, _ := dhtPeer.monitor.GetGauge(metricOpRouteCount)
	routeCountAll, _ := dhtPeer.monitor.GetCounter(metricOpRouteCountAll)
	routeCountSuccess, _ := dhtPeer.monitor.GetCounter(metricOpRouteCountSuccess)
	opLatencyRoute, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRoute)
	timer := dhtPeer.monitor.Timer()

	routeCount.Inc()
	routeCountAll.Inc()
	start := timer.NewTimer()

	println("-> Routing envelope:", envel.String())

	// get sender agent envelRec
	// TODO can change function signature to force the caller to provide the envelRec
	var envelRec *dhtnode.AgentRecord
	sender := envel.Sender

	dhtPeer.agentRecordsLock.RLock()
	localRec, existsLocal := dhtPeer.agentRecords[sender]
	dhtPeer.agentRecordsLock.RUnlock()

	if sender == dhtPeer.myAgentAddress {
		envelRec = dhtPeer.myAgentRecord
	} else if existsLocal {
		// TOFIX(LR) should acquire RLock
		envelRec = localRec
	} else {
		err := errors.New("Envelope sender is not registered locally " + sender)
		lerror(err).Str("op", "route").Str("addr", envel.To).
			Msg("")
		return err
	}

	target := envel.To

	dhtPeer.tcpAddressesLock.RLock()
	connDelegate, existsDelegate := dhtPeer.tcpAddresses[target]
	dhtPeer.tcpAddressesLock.RUnlock()

	if target == dhtPeer.myAgentAddress {
		linfo().Str("op", "route").Str("addr", target).
			Msg("route envelope destinated to my local agent...")
		// TOFIX(LR) risk of infinite loop
		for dhtPeer.myAgentReady != nil && !dhtPeer.myAgentReady() {
			lwarn().Str("op", "route").Str("addr", target).
				Msg("agent not ready yet, sleeping for some time ...")
			time.Sleep(time.Duration(100) * time.Millisecond)
		}
		if dhtPeer.processEnvelope != nil {
			duration := timer.GetTimer(start)
			opLatencyRoute.Observe(float64(duration.Microseconds()))
			err := dhtPeer.processEnvelope(envel)
			routeCount.Dec()
			if err != nil {
				return err
			}
			routeCountSuccess.Inc()
		} else {
			lwarn().Str("op", "route").Str("addr", target).
				Msgf("ProcessEnvelope not set, ignoring envelope %s", envel.String())
			return errors.New("Agent not ready")
		}
	} else if existsDelegate {
		linfo().Str("op", "route").Str("addr", target).
			Msgf("destination is a delegate client %s", connDelegate.RemoteAddr().String())
		routeCount.Dec()
		routeCountSuccess.Inc()
		duration := timer.GetTimer(start)
		opLatencyRoute.Observe(float64(duration.Microseconds()))
		return utils.WriteEnvelopeConn(connDelegate, envel)
	} else {
		var peerID peer.ID
		var err error
		dhtPeer.dhtAddressesLock.RLock()
		sPeerID, exists := dhtPeer.dhtAddresses[target]
		dhtPeer.dhtAddressesLock.RUnlock()
		if exists {
			linfo().Str("op", "route").Str("addr", target).
				Msgf("destination is a relay client %s", sPeerID)
			peerID, err = peer.Decode(sPeerID)
			if err != nil {
				lerror(err).Str("op", "route").Str("addr", target).
					Msgf("CRITICAL couldn't parse peer id from relay client id")
				routeCount.Dec()
				return err
			}
		} else {
			linfo().Str("op", "route").Str("addr", target).
				Msg("did NOT find destination address locally, looking for it in the DHT...")
			peerID, _, err = dhtPeer.lookupAddressDHT(target) // guarantees peerID has a valid PoR
			if err != nil {
				lerror(err).Str("op", "route").Str("addr", target).
					Msg("while looking up address on the DHT")
				routeCount.Dec()
				return err
			}
		}

		//linfo().Str("op", "route").Str("addr", target).
		//	Msgf("got peer id '%s' for agent address", peerID.Pretty())

		//linfo().Str("op", "route").Str("addr", target).
		//	Msgf("opening stream to target %s...", peerID.Pretty())
		ctx, cancel := context.WithTimeout(context.Background(), newStreamTimeout)
		defer cancel()
		stream, err := dhtPeer.routedHost.NewStream(ctx, peerID, dhtnode.AeaEnvelopeStream)
		if err != nil {
			lerror(err).Str("op", "route").Str("addr", target).
				Msgf("timeout, couldn't open stream to target %s", peerID.Pretty())
			routeCount.Dec()
			return err
		}

		duration := timer.GetTimer(start)
		opLatencyRoute.Observe(float64(duration.Microseconds()))

		linfo().Str("op", "route").Str("addr", target).
			Msgf("sending envelope to target peer %s...", peerID.Pretty())

		envelBytes, err := proto.Marshal(envel)
		if err != nil {
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("couldn't serialize envelope")
			errReset := stream.Reset()
			ignore(errReset)
			routeCount.Dec()
			return err
		}
		aeaEnvelope := &dhtnode.AeaEnvelope{
			Envel:  envelBytes,
			Record: envelRec,
		}
		msg := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_AeaEnvelope{AeaEnvelope: aeaEnvelope},
		}
		buf, err := proto.Marshal(msg)
		if err != nil {
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("couldn't serialize envelope")
			errReset := stream.Reset()
			ignore(errReset)
			routeCount.Dec()
			return err
		}

		ldebug().
			Str("op", "route").
			Str("target", target).
			Msg("sending envelope to target...")
		err = utils.WriteBytes(stream, buf)
		if err != nil {
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("couldn't send envelope")
			errReset := stream.Reset()
			ignore(errReset)
			routeCount.Dec()
			return err
		}

		// wait for response
		linfo().Str("op", "route").Str("addr", target).
			Msgf("waiting fro envelope delivery confirmation from target peer %s...", peerID.Pretty())
		buf, err = utils.ReadBytes(stream)
		if err != nil {
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("while getting confirmation")
			errReset := stream.Reset()
			ignore(errReset)
			routeCount.Dec()
			return err
		}

		stream.Close()

		response := &dhtnode.AcnMessage{}
		err = proto.Unmarshal(buf, response)
		if err != nil {
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("while deserializing acn confirmation message")
			routeCount.Dec()
			return err
		}

		// response is expected to be a Status
		var status *dhtnode.Status
		switch pl := response.Payload.(type) {
		case *dhtnode.AcnMessage_Status:
			status = pl.Status
		default:
			err = errors.New("Unexpected Acn Message")
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("while deserializing acn confirmation message")
			routeCount.Dec()
			return err
		}

		if status.Code != dhtnode.Status_SUCCESS {
			err = errors.New(status.Code.String() + " : " + strings.Join(status.Msgs, ":"))
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("failed to deliver envelope")
			routeCount.Dec()
			return err
		}

		routeCount.Dec()
		return nil
	}

	return nil
}

/// TOFIX(LR) should return (*dhtnode)
func (dhtPeer *DHTPeer) lookupAddressDHT(address string) (peer.ID, *dhtnode.AgentRecord, error) {
	lerror, lwarn, linfo, _ := dhtPeer.getLoggers()
	var err error

	dhtLookupLatency, _ := dhtPeer.monitor.GetHistogram(metricDHTOpLatencyLookup)
	timer := dhtPeer.monitor.Timer()

	addressCID, err := utils.ComputeCID(address)
	if err != nil {
		return "", nil, err
	}

	linfo().Str("op", "lookup").Str("addr", address).
		Msgf("Querying for providers for cid %s...", addressCID.String())
	ctx, cancel := context.WithTimeout(context.Background(), addressLookupTimeout)
	defer cancel()
	//var elapsed time.Duration
	var provider peer.AddrInfo
	var stream network.Stream

	start := timer.NewTimer()

	noProvider := false
	for {
		providers := dhtPeer.dht.FindProvidersAsync(ctx, addressCID, 0)

		for provider = range providers {
			duration := timer.GetTimer(start)
			dhtLookupLatency.Observe(float64(duration.Microseconds()))

			//linfo().Str("op", "lookup").Str("addr", address).
			//	Msgf("found provider %s after %s", provider, elapsed.String())

			// Add peer to host PeerStore - the provider should be the holder of the address
			dhtPeer.routedHost.Peerstore().AddAddrs(
				provider.ID,
				provider.Addrs,
				peerstore.PermanentAddrTTL,
			)

			//linfo().Str("op", "lookup").Str("addr", address).
			//	Msgf("opening stream to the address provider %s...", provider)
			ctxConnect := context.Background()
			stream, err = dhtPeer.routedHost.NewStream(
				ctxConnect,
				provider.ID,
				dhtnode.AeaAddressStream,
			)
			if err != nil {
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("couldn't open stream to address provider %s: %s, looking up other providers...", provider, err.Error())
				dhtPeer.routedHost.Peerstore().ClearAddrs(provider.ID)
				continue
			}

			linfo().Str("op", "lookup").Str("addr", address).
				Msgf("getting agent record from provider %s...", provider)

			// prepare LookupRequest
			lookupRequest := &dhtnode.LookupRequest{AgentAddress: address}
			msg := &dhtnode.AcnMessage{
				Version: dhtnode.CurrentVersion,
				Payload: &dhtnode.AcnMessage_LookupRequest{LookupRequest: lookupRequest},
			}
			buf, err := proto.Marshal(msg)
			ignore(err)

			err = utils.WriteBytes(stream, []byte(buf))
			if err != nil {
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("couldn't send agent lookup request to provider %s (%s), looking up other providers...", provider, err.Error())
				err = stream.Reset()
				ignore(err)
				continue
			}

			buf, err = utils.ReadBytes(stream)
			if err != nil {
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("couldn't receive agent lookup response from provider %s (%s), looking up other providers...", provider, err.Error())
				err = stream.Reset()
				ignore(err)
				continue
			}

			stream.Close()

			response := &dhtnode.AcnMessage{}
			err = proto.Unmarshal(buf, response)
			if err != nil {
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("couldn't deserialize agent lookup response from provider %s (%s), looking up other providers...", provider, err.Error())
				continue
			}

			// Response is either a LookupResponse or Status
			var lookupResponse *dhtnode.LookupResponse = nil
			var status *dhtnode.Status = nil
			switch pl := response.Payload.(type) {
			case *dhtnode.AcnMessage_LookupResponse:
				lookupResponse = pl.LookupResponse
			case *dhtnode.AcnMessage_Status:
				status = pl.Status
			default:
				err = errors.New("Unexpected Acn Message")
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("couldn't deserialize agent lookup response from provider %s (%s), looking up other providers...", provider, err.Error())
				continue
			}

			if status != nil {
				err = errors.New(status.Code.String() + " : " + strings.Join(status.Msgs, ":"))
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("Failed agent lookup response from provider %s (%s), looking up other providers...", provider, err.Error())
				continue
			}

			// lookupResponse must be set
			record := lookupResponse.AgentRecord
			valid, err := dhtnode.IsValidProofOfRepresentation(
				record,
				address,
				record.PeerPublicKey,
			)
			if err != nil || valid.Code != dhtnode.Status_SUCCESS {
				errMsg := status.Code.String() + " : " + strings.Join(status.Msgs, ":")
				if err == nil {
					err = errors.New(errMsg)
				} else {
					err = errors.Wrap(err, status.Code.String()+" : "+strings.Join(status.Msgs, ":"))
				}
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("invalid agent record from provider %s (%s), looking up other providers...", provider, err.Error())
				continue
			}

			peerid, err := utils.IDFromFetchAIPublicKey(record.PeerPublicKey)
			if err != nil {
				return "", nil, errors.New(
					"CRITICAL couldn't get peer ID from message:" + err.Error(),
				)
			}

			return peerid, record, nil
		}

		if provider.ID == "" {
			msg := "didn't find any provider for address"
			if !noProvider {
				noProvider = true
				lwarn().Str("op", "lookup").Str("addr", address).Msgf("%s, retrying...", msg)
			}
			select {
			default:
				time.Sleep(200 * time.Millisecond)
			case <-ctx.Done():
				err = errors.New(msg + " " + address + " within timeout")
				lerror(err).Str("op", "lookup").Str("addr", address).Msg("")
				return "", nil, err
			}
		} else {
			return "", nil, err
		}
	}
}

func (dhtPeer *DHTPeer) handleAeaEnvelopeStream(stream network.Stream) {
	lerror, lwarn, linfo, _ := dhtPeer.getLoggers()

	//linfo().Msg("Got a new aea envelope stream")

	buf, err := utils.ReadBytes(stream)
	if err != nil {
		lerror(err).Msg("while reading envelope from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	// get envelope
	msg := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		lerror(err).Msg("while deserializing acn aea envelope message")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_SERIALIZATION}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	// payload is expected to be AeaEnvelope
	var aeaEnvelope *dhtnode.AeaEnvelope
	switch pl := msg.Payload.(type) {
	case *dhtnode.AcnMessage_AeaEnvelope:
		aeaEnvelope = pl.AeaEnvelope
	default:
		err = errors.New("Unexpected payload")
		lerror(err).Msg("while deserializing acn aea envelope message")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNEXPECTED_PAYLOAD}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	envel := &aea.Envelope{}
	err = proto.Unmarshal(aeaEnvelope.Envel, envel)
	if err != nil {
		lerror(err).Msg("while deserializing acn aea envelope message")
		status := &dhtnode.Status{
			Code: dhtnode.Status_ERROR_SERIALIZATION,
			Msgs: []string{err.Error()},
		}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	remotePubkey, err := utils.FetchAIPublicKeyFromPubKey(stream.Conn().RemotePublicKey())
	ignore(err)
	status, err := dhtnode.IsValidProofOfRepresentation(
		aeaEnvelope.Record,
		aeaEnvelope.Record.Address,
		remotePubkey,
	)
	if err != nil || status.Code != dhtnode.Status_SUCCESS {
		if err == nil {
			err = errors.New(status.Code.String() + ":" + strings.Join(status.Msgs, ":"))
		}
		lerror(err).Msg("incoming envelope PoR is not valid")
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	linfo().Msgf("Received envelope from peer %s", envel.String())

	// check if destination is a tcp client

	dhtPeer.tcpAddressesLock.RLock()
	connDelegate, existsDelegate := dhtPeer.tcpAddresses[envel.To]
	dhtPeer.tcpAddressesLock.RUnlock()

	if existsDelegate {
		linfo().Msgf(
			"Sending envelope to tcp delegate client %s...",
			connDelegate.RemoteAddr().String(),
		)
		err = utils.WriteEnvelopeConn(connDelegate, envel)
		if err != nil {
			lerror(
				err,
			).Msgf(
				"while sending envelope to tcp client %s",
				connDelegate.RemoteAddr().String(),
			)
			status := &dhtnode.Status{Code: dhtnode.Status_ERROR_AGENT_NOT_READY}
			response := &dhtnode.AcnMessage{
				Version: dhtnode.CurrentVersion,
				Payload: &dhtnode.AcnMessage_Status{Status: status},
			}
			buf, err = proto.Marshal(response)
			ignore(err)
			err = utils.WriteBytes(stream, buf)
			ignore(err)
			err = stream.Close()
			ignore(err)
			return
		}
	} else if envel.To == dhtPeer.myAgentAddress {
		if dhtPeer.processEnvelope == nil {
			lerror(err).Msgf("while processing envelope by agent")
			status := &dhtnode.Status{Code: dhtnode.Status_ERROR_AGENT_NOT_READY}
			response := &dhtnode.AcnMessage{
				Version: dhtnode.CurrentVersion,
				Payload: &dhtnode.AcnMessage_Status{Status: status},
			}
			buf, err = proto.Marshal(response)
			ignore(err)
			err = utils.WriteBytes(stream, buf)
			ignore(err)
			err = stream.Close()
			ignore(err)
			return
		}
		linfo().Msg("Processing envelope by local agent...")
		err = dhtPeer.processEnvelope(envel)
		ignore(err)
	} else {
		lwarn().Msgf("ignored envelope %s", envel.String())
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNKNOWN_AGENT_ADDRESS}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	// all good
	status = &dhtnode.Status{Code: dhtnode.Status_SUCCESS}
	response := &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_Status{Status: status},
	}
	buf, err = proto.Marshal(response)
	ignore(err)
	err = utils.WriteBytes(stream, buf)
	ignore(err)
	err = stream.Close()
	ignore(err)

}

func (dhtPeer *DHTPeer) handleAeaAddressStream(stream network.Stream) {
	lerror, _, linfo, _ := dhtPeer.getLoggers()

	//linfo().Msgf("Got a new aea address stream")

	// get LookupRequest
	buf, err := utils.ReadBytes(stream)
	if err != nil {
		lerror(err).Str("op", "resolve").
			Msg("while reading message from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	msg := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		lerror(err).Str("op", "resolve").Msg("couldn't deserialize acn registration message")
		// TOFIX(LR) setting Msgs to err.Error is potentially a security vulnerability
		status := &dhtnode.Status{
			Code: dhtnode.Status_ERROR_SERIALIZATION,
			Msgs: []string{err.Error()},
		}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	// Get LookupRequest message
	var lookupRequest *dhtnode.LookupRequest
	switch pl := msg.Payload.(type) {
	case *dhtnode.AcnMessage_LookupRequest:
		lookupRequest = pl.LookupRequest
	default:
		err = errors.New("Unexpected payload")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNEXPECTED_PAYLOAD, Msgs: []string{err.Error()}}
		response := &dhtnode.AcnMessage{Version: dhtnode.CurrentVersion, Payload: &dhtnode.AcnMessage_Status{Status: status}}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	reqAddress := lookupRequest.AgentAddress

	//linfo().Str("op", "resolve").Str("addr", reqAddress).
	//	Msg("Received query for addr")
	var sPeerID string
	var sRecord *dhtnode.AgentRecord = nil

	dhtPeer.dhtAddressesLock.RLock()
	idRelay, existsRelay := dhtPeer.dhtAddresses[reqAddress]
	dhtPeer.dhtAddressesLock.RUnlock()
	dhtPeer.tcpAddressesLock.RLock()
	_, existsDelegate := dhtPeer.tcpAddresses[reqAddress]
	dhtPeer.tcpAddressesLock.RUnlock()
	dhtPeer.agentRecordsLock.RLock()
	localRec := dhtPeer.agentRecords[reqAddress]
	dhtPeer.agentRecordsLock.RUnlock()

	if reqAddress == dhtPeer.myAgentAddress {
		peerID, err := peer.IDFromPublicKey(dhtPeer.publicKey)
		if err != nil {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msgf("CRITICAL could not get peer ID from public key %s", dhtPeer.publicKey)
		} else {
			sPeerID = peerID.Pretty()
			sRecord = dhtPeer.myAgentRecord
		}
	} else if existsRelay {
		linfo().Str("op", "resolve").Str("addr", reqAddress).
			Msg("found address in my relay clients map")
		sPeerID = idRelay
		sRecord = localRec
	} else if existsDelegate {
		linfo().Str("op", "resolve").Str("addr", reqAddress).
			Msgf("found address in my delegate clients map")
		peerID, err := peer.IDFromPublicKey(dhtPeer.publicKey)
		if err != nil {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msgf("CRITICAL could not get peer ID from public key %s", dhtPeer.publicKey)
		} else {
			sPeerID = peerID.Pretty()
			sRecord = localRec
		}
	} else {
		// needed when a relay client queries for a peer ID
		//linfo().Str("op", "resolve").Str("addr", reqAddress).
		//	Msg("did NOT found the address locally, looking for it in the DHT...")
		peerID, peerRecord, err := dhtPeer.lookupAddressDHT(reqAddress)
		if err == nil {
			linfo().Str("op", "resolve").Str("addr", reqAddress).
				Msg("found address on the DHT")
			sPeerID = peerID.Pretty()
			sRecord = peerRecord
		} else {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msgf("did NOT find address locally or on the DHT.")

			status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNKNOWN_AGENT_ADDRESS}
			response := &dhtnode.AcnMessage{
				Version: dhtnode.CurrentVersion,
				Payload: &dhtnode.AcnMessage_Status{Status: status},
			}
			buf, err = proto.Marshal(response)
			ignore(err)
			err = utils.WriteBytes(stream, buf)
			ignore(err) // TODO(LR) stream.Reset() if err
			err = stream.Close()
			ignore(err)
			return
		}
	}

	if sRecord != nil {
		linfo().Str("op", "resolve").Str("addr", reqAddress).
			Msgf("sending agent record (%s) %s", sPeerID, sRecord)

		lookupResponse := &dhtnode.LookupResponse{AgentRecord: sRecord}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_LookupResponse{LookupResponse: lookupResponse},
		}
		buf, err := proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		if err != nil {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msg("While sending agent record to peer")
			err = stream.Reset()
			ignore(err)
		}
	}

	status := &dhtnode.Status{
		Code: dhtnode.Status_ERROR_GENERIC,
		Msgs: []string{"Internal error: Couldn't get AgentRecord"},
	}
	response := &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_Status{Status: status},
	}
	buf, err = proto.Marshal(response)
	ignore(err)
	err = utils.WriteBytes(stream, buf)
	ignore(err)
}

func (dhtPeer *DHTPeer) handleAeaNotifStream(stream network.Stream) {
	lerror, _, _, ldebug := dhtPeer.getLoggers()

	//linfo().Str("op", "notif").
	//	Msgf("Got a new notif stream")

	if !dhtPeer.addressAnnounced {
		opLatencyRegister, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRegister)
		timer := dhtPeer.monitor.Timer()
		start := timer.NewTimer()

		// workaround: to avoid getting `failed to find any peer in table`
		//  when calling dht.Provide (happens occasionally)
		ldebug().Msg("waiting for notifying peer to be added to dht routing table...")
		ctx, cancel := context.WithTimeout(
			context.Background(),
			routingTableConnectionUpdateTimeout,
		)
		defer cancel()
		for dhtPeer.dht.RoutingTable().Find(stream.Conn().RemotePeer()) == "" {
			select {
			case <-ctx.Done():
				lerror(nil).
					Msgf("timeout: notifying peer %s haven't been added to DHT routing table",
						stream.Conn().RemotePeer().Pretty())
				return
			case <-time.After(time.Millisecond * 5):
			}
		}

		if dhtPeer.myAgentAddress != "" {
			err := dhtPeer.registerAgentAddress(dhtPeer.myAgentAddress)
			if err != nil {
				lerror(err).Str("op", "notif").
					Str("addr", dhtPeer.myAgentAddress).
					Msgf("while announcing my agent address")
				return
			}
		}
		if dhtPeer.enableRelay {
			dhtPeer.dhtAddressesLock.RLock()
			for addr := range dhtPeer.dhtAddresses {
				err := dhtPeer.registerAgentAddress(addr)
				if err != nil {
					lerror(err).Str("op", "notif").
						Str("addr", addr).
						Msg("while announcing relay client address")
				}
			}
			dhtPeer.dhtAddressesLock.RUnlock()
		}
		if dhtPeer.delegatePort != 0 {
			dhtPeer.tcpAddressesLock.RLock()
			for addr := range dhtPeer.tcpAddresses {
				err := dhtPeer.registerAgentAddress(addr)
				if err != nil {
					lerror(err).Str("op", "notif").
						Str("addr", addr).
						Msg("while announcing delegate client address")
				}
			}
			dhtPeer.tcpAddressesLock.RUnlock()

		}
		duration := timer.GetTimer(start)
		opLatencyRegister.Observe(float64(duration.Microseconds()))
	}
	dhtPeer.addressAnnounced = true
}

func (dhtPeer *DHTPeer) handleAeaRegisterStream(stream network.Stream) {
	lerror, _, linfo, _ := dhtPeer.getLoggers()

	// to limit spamming
	time.Sleep(dhtPeer.registrationDelay)

	nbrClients, _ := dhtPeer.monitor.GetCounter(metricServiceRelayClientsCountAll)

	opLatencyRegister, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRegister)
	timer := dhtPeer.monitor.Timer()
	start := timer.NewTimer()

	//linfo().Str("op", "register").
	//	Msg("Got a new aea register stream")

	buf, err := utils.ReadBytes(stream)
	if err != nil {
		lerror(err).Str("op", "register").
			Msg("while reading relay client registration request from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	msg := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		lerror(err).Msg("couldn't deserialize acn registration message")
		// TOFIX(LR) setting Msgs to err.Error is potentially a security vulnerability
		status := &dhtnode.Status{
			Code: dhtnode.Status_ERROR_SERIALIZATION,
			Msgs: []string{err.Error()},
		}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	linfo().Msgf("Received relay registration request %s", msg)

	// Get Register message
	var register *dhtnode.Register
	switch pl := msg.Payload.(type) {
	case *dhtnode.AcnMessage_Register:
		register = pl.Register
	default:
		err = errors.New("Unexpected payload")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNEXPECTED_PAYLOAD, Msgs: []string{err.Error()}}
		response := &dhtnode.AcnMessage{Version: dhtnode.CurrentVersion, Payload: &dhtnode.AcnMessage_Status{Status: status}}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}
	record := register.Record
	clientAddr := record.Address

	//linfo().Msgf("connection from %s established for Address %s",
	//	stream.Conn().RemotePeer().Pretty(), clientAddr)

	// check if the PoR is valid
	clientPubKey, err := utils.FetchAIPublicKeyFromPubKey(stream.Conn().RemotePublicKey())
	ignore(err)
	status, err := dhtnode.IsValidProofOfRepresentation(record, record.Address, clientPubKey)
	if err != nil || status.Code != dhtnode.Status_SUCCESS {
		if err == nil {
			err = errors.New(status.Code.String() + ":" + strings.Join(status.Msgs, ":"))
		}
		lerror(err).Msg("PoR is not valid")
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	// TOFIX(LR) post-pone answer until address successfully registered
	msg = &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_Status{Status: status},
	}
	buf, err = proto.Marshal(msg)
	ignore(err)
	err = utils.WriteBytes(stream, buf)
	if err != nil {
		err = stream.Reset()
		ignore(err)
		return
	}

	stream.Close()
	nbrClients.Inc()

	//linfo().Str("op", "register").
	//	Str("addr", string(clientAddr)).
	//	Msgf("Received address registration request for peer id %s", string(clientPeerID))
	clientPeerID := stream.Conn().RemotePeer().Pretty()
	dhtPeer.agentRecordsLock.Lock()
	dhtPeer.agentRecords[clientAddr] = record
	dhtPeer.agentRecordsLock.Unlock()
	dhtPeer.dhtAddressesLock.Lock()
	dhtPeer.dhtAddresses[clientAddr] = clientPeerID
	err = dhtPeer.saveAgentRecordToPersistentStorage(record)
	if err != nil {
		lerror(err).Str("op", "register").
			Str("addr", clientAddr).
			Msg("while saving agent record to persistent storage")
	}
	dhtPeer.dhtAddressesLock.Unlock()
	if dhtPeer.addressAnnounced {
		linfo().Str("op", "register").
			Str("addr", clientAddr).
			Msgf("Announcing client address on behalf of %s...", clientPeerID)
		err = dhtPeer.registerAgentAddress(string(clientAddr))
		if err != nil {
			//TOFIX(LR) remove agent from map, or don't add it unless announcement done
			lerror(err).Str("op", "register").
				Str("addr", clientAddr).
				Msg("while announcing client address to the dht")
			return
		}
	}

	duration := timer.GetTimer(start)
	opLatencyRegister.Observe(float64(duration.Microseconds()))
}

func (dhtPeer *DHTPeer) registerAgentAddress(addr string) error {
	_, _, linfo, _ := dhtPeer.getLoggers()

	dhtStoreLatency, _ := dhtPeer.monitor.GetHistogram(metricDHTOpLatencyStore)
	timer := dhtPeer.monitor.Timer()

	addressCID, err := utils.ComputeCID(addr)
	if err != nil {
		return err
	}

	// TOFIX(LR) tune timeout
	ctx, cancel := context.WithTimeout(context.Background(), addressRegisterTimeout)
	defer cancel()

	linfo().Str("op", "register").
		Str("addr", addr).
		Msgf("Announcing address to the dht with cid key %s", addressCID.String())
	start := timer.NewTimer()
	err = dhtPeer.dht.Provide(ctx, addressCID, true)
	if err != context.DeadlineExceeded {
		duration := timer.GetTimer(start)
		dhtStoreLatency.Observe(float64(duration.Microseconds()))
		return err
	}
	return nil
}
