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
package dhtpeer

import (
	"bufio"
	"bytes"
	"context"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/binary"
	"encoding/pem"
	"fmt"
	"io"
	"log"
	"math/big"
	"net"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/btcsuite/btcd/btcec"
	"github.com/pkg/errors"

	"github.com/rs/zerolog"
	"google.golang.org/protobuf/proto"

	"github.com/libp2p/go-libp2p"
	cryptop2p "github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/libp2p/go-libp2p-core/peerstore"
	"github.com/multiformats/go-multiaddr"

	circuit "github.com/libp2p/go-libp2p-circuit"
	kaddht "github.com/libp2p/go-libp2p-kad-dht"
	routedhost "github.com/libp2p/go-libp2p/p2p/host/routed"

	acn "libp2p_node/acn"
	aea "libp2p_node/aea"
	common "libp2p_node/dht/common"
	"libp2p_node/dht/dhtnode"
	monitoring "libp2p_node/dht/monitoring"
	utils "libp2p_node/utils"
)

const AcnStatusTimeout = 5.0 * time.Second
const AcnStatusesQueueSize = 1000

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
	newStreamTimeout                     = 10 * time.Second
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

	mailboxHostPort string
	mailboxServer   *MailboxServer

	registrationDelay time.Duration

	key             cryptop2p.PrivKey
	publicKey       cryptop2p.PubKey
	localMultiaddr  multiaddr.Multiaddr
	publicMultiaddr multiaddr.Multiaddr
	bootstrapPeers  []peer.AddrInfo

	dht          *kaddht.IpfsDHT
	routedHost   *routedhost.RoutedHost
	tcpListener  net.Listener
	cert         *tls.Certificate
	sslSignature []byte

	addressAnnouncedMap     map[string]bool
	addressAnnouncedMapLock sync.RWMutex

	// flag to announce addresses over network if peer connected to other peers
	enableAddressAnnouncement     bool
	enableAddressAnnouncementWg   *sync.WaitGroup
	enableAddressAnnouncementLock sync.RWMutex

	myAgentAddress   string
	myAgentRecord    *acn.AgentRecord
	myAgentReady     func() bool
	dhtAddresses     map[string]string
	acnStatuses      map[string]chan *acn.StatusBody
	tcpAddresses     map[string]net.Conn
	agentRecords     map[string]*acn.AgentRecord
	acnStatusesLock  sync.RWMutex
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

	// syncMessages map[string]*sync.WaitGroup
	syncMessagesLock sync.RWMutex
	syncMessages     map[string](chan *aea.Envelope)
}

// New creates a new DHTPeer
func New(opts ...Option) (*DHTPeer, error) {
	var err error
	dhtPeer := &DHTPeer{registrationDelay: addressRegistrationDelay}

	dhtPeer.dhtAddresses = map[string]string{}
	dhtPeer.tcpAddresses = map[string]net.Conn{}
	dhtPeer.agentRecords = map[string]*acn.AgentRecord{}
	dhtPeer.acnStatuses = map[string]chan *acn.StatusBody{}
	dhtPeer.dhtAddressesLock = sync.RWMutex{}
	dhtPeer.tcpAddressesLock = sync.RWMutex{}
	dhtPeer.agentRecordsLock = sync.RWMutex{}
	dhtPeer.persistentStoragePath = defaultPersistentStoragePath
	dhtPeer.syncMessages = make(map[string](chan *aea.Envelope))
	dhtPeer.addressAnnouncedMap = map[string]bool{}
	dhtPeer.addressAnnouncedMapLock = sync.RWMutex{}
	dhtPeer.enableAddressAnnouncementWg = &sync.WaitGroup{}
	dhtPeer.enableAddressAnnouncementLock = sync.RWMutex{}
	dhtPeer.mailboxHostPort = ""

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
		if err != nil || errPoR != nil || status.Code != acn.SUCCESS {
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

	err = dhtPeer.makeSSLCertifiateAndSignature()
	if err != nil {
		return nil, err
	}
	// make the routed host
	dhtPeer.routedHost = routedhost.Wrap(basicHost, dhtPeer.dht)
	dhtPeer.setupLogger()

	lerror, _, linfo, ldebug := dhtPeer.GetLoggers()

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
			err := dhtPeer.RegisterAgentAddress(addr)
			if err != nil {
				lerror(err).Str("addr", addr).
					Msg("while announcing stored client address")
			}
		}
	}
	linfo().Msgf("successfully loaded %d agents", nbr)

	// if peer is joining an existing network, announce my agent address if set
	if len(dhtPeer.bootstrapPeers) > 0 {
		// there are some bootstrap peers so we can announce addresses to them
		dhtPeer.enableAddressAnnouncement = true

		if dhtPeer.myAgentAddress != "" && !dhtPeer.IsAddressAnnounced(dhtPeer.myAgentAddress) {
			ldebug().Msg("Address was announced on bootstrap peers")
			opLatencyRegister, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRegister)
			timer := dhtPeer.monitor.Timer()
			start := timer.NewTimer()
			err := dhtPeer.RegisterAgentAddress(dhtPeer.myAgentAddress)
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

	// check mailbox uri is set
	if len(dhtPeer.mailboxHostPort) != 0 {
		dhtPeer.launchMailboxService()
	}

	// start monitoring
	ready := &sync.WaitGroup{}
	ready.Add(1)
	go dhtPeer.startMonitoring(ready)
	ready.Wait()

	return dhtPeer, nil
}

// saveAgentRecordToPersistentStorage saves the agent record to persistent storage
func (dhtPeer *DHTPeer) saveAgentRecordToPersistentStorage(record *acn.AgentRecord) error {
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

func parsePersistentStorageLine(line []byte) (*acn.AgentRecord, error) {
	record := &acn.AgentRecord{}
	err := proto.Unmarshal(line, record)
	return record, err
}

func formatPersistentStorageLine(record *acn.AgentRecord) []byte {
	msg, err := proto.Marshal(record)
	ignore(err)
	return msg
}

// initAgentRecordPersistentStorage loads agent records from persistent storage
func (dhtPeer *DHTPeer) initAgentRecordPersistentStorage() (int, error) {
	var err error
	_, _, linfo, _ := dhtPeer.GetLoggers()
	linfo().Msg("Load records from store " + dhtPeer.persistentStoragePath)
	dhtPeer.storage, err = os.OpenFile(
		dhtPeer.persistentStoragePath,
		os.O_APPEND|os.O_RDWR|os.O_CREATE,
		0600,
	)
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
	_, _, linfo, _ := dhtPeer.GetLoggers()
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

func (dhtPeer *DHTPeer) GetLoggers() (func(error) *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event) {
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

	_, _, linfo, _ := dhtPeer.GetLoggers()

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
		dhtPeer.tcpAddressesLock.Lock()
		for _, conn := range dhtPeer.tcpAddresses {
			err = conn.Close()
			errappend(err)
		}
		dhtPeer.tcpAddressesLock.Unlock()
	}

	if dhtPeer.mailboxServer != nil {
		dhtPeer.mailboxServer.stop()
	}

	err = dhtPeer.dht.Close()
	errappend(err)
	err = dhtPeer.routedHost.Close()
	errappend(err)

	err = dhtPeer.closeAgentRecordPersistentStorage()
	errappend(err)

	//linfo().Msg("Stopping DHTPeer: waiting for goroutines to cancel...")
	// dhtPeer.goroutines.Wait()
	dhtPeer.syncMessagesLock.Lock()
	for _, channel := range dhtPeer.syncMessages {
		close(channel)
	}
	dhtPeer.syncMessagesLock.Unlock()

	return status
}

// Generate selfsigned c509 certificate with temprorary key to be used with TLS server
// We can not use peer private key cause it does not supported by golang TLS implementation
// So we generate a new one and send session public key signature made with peer private key
// snd client can validate it with peer public key/address
func generate_x509_cert() (*tls.Certificate, error) {
	privBtcKey, err := btcec.NewPrivateKey(elliptic.P256())
	if err != nil {
		return nil, errors.Wrap(err, "while creating new private key")
	}
	privKey := privBtcKey.ToECDSA()
	pubKey := &privKey.PublicKey

	ca := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			Organization: []string{"Acn Node"},
		},
		NotBefore: time.Now(),
		NotAfter:  time.Now().AddDate(1, 0, 0),

		KeyUsage: x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{
			x509.ExtKeyUsageClientAuth,
			x509.ExtKeyUsageServerAuth,
		},
		BasicConstraintsValid: true,
	}
	ca.IsCA = true
	ca.KeyUsage |= x509.KeyUsageCertSign

	certBytes, err := x509.CreateCertificate(rand.Reader, ca, ca, pubKey, privKey)
	if err != nil {
		return nil, errors.Wrap(err, "while creating ca")
	}
	certPEM := new(bytes.Buffer)
	err = pem.Encode(certPEM, &pem.Block{
		Type:  "CERTIFICATE",
		Bytes: certBytes,
	})
	if err != nil {
		return nil, errors.Wrap(err, "while encoding cert pem")
	}

	privPEM := new(bytes.Buffer)
	b, err := x509.MarshalECPrivateKey(privKey)
	if err != nil {
		return nil, errors.Wrap(err, "while marshaling ec private key")
	}
	err = pem.Encode(privPEM, &pem.Block{
		Type:  "EC PRIVATE KEY",
		Bytes: b,
	})
	if err != nil {
		return nil, errors.Wrap(err, "while encoding prive pem")
	}

	cert, err := tls.X509KeyPair(certPEM.Bytes(), privPEM.Bytes())
	return &cert, err
}

// launchDelegateService launches the delegate service on the configured uri
func (dhtPeer *DHTPeer) launchDelegateService() {
	var err error

	lerror, _, _, _ := dhtPeer.GetLoggers()
	config := &tls.Config{Certificates: []tls.Certificate{*dhtPeer.cert}}
	uri := dhtPeer.host + ":" + strconv.FormatInt(int64(dhtPeer.delegatePort), 10)
	listener, err := tls.Listen("tcp", uri, config)

	if err != nil {
		lerror(err).Msgf("while setting up listening tcp socket %s", uri)
		check(err)
	}

	if err != nil {
		lerror(err).Msgf("while generating tls signature")
		check(err)
	}
	dhtPeer.tcpListener = TLSListener{Listener: listener, Signature: dhtPeer.sslSignature}
}

// launchDelegateService launches the delegate service on the configured uri
func (dhtPeer *DHTPeer) makeSSLCertifiateAndSignature() error {
	var err error

	lerror, _, _, _ := dhtPeer.GetLoggers()
	dhtPeer.cert, err = generate_x509_cert()
	if err != nil {
		lerror(err).Msgf("while generating tls certificate")
		return err
	}
	dhtPeer.sslSignature, err = makeSessionKeySignature(dhtPeer.cert, dhtPeer.key)
	if err != nil {
		lerror(err).Msgf("while generating tls certificate server signature")
		return err
	}
	return nil
}

// launchMailboxService launches the mailbox http service on the configured uri
func (dhtPeer *DHTPeer) launchMailboxService() {
	_, _, linfo, _ := dhtPeer.GetLoggers()
	if len(dhtPeer.mailboxHostPort) == 0 {
		return
	}
	dhtPeer.mailboxServer = &MailboxServer{
		addr:    dhtPeer.mailboxHostPort,
		dhtPeer: dhtPeer,
	}
	linfo().Msgf("Starting mailbox service on %s", dhtPeer.mailboxHostPort)
	go dhtPeer.mailboxServer.start()
}

// Make signature for session public key using peer private key
func makeSessionKeySignature(cert *tls.Certificate, privateKey cryptop2p.PrivKey) ([]byte, error) {
	cert_pub_key := cert.PrivateKey.(*ecdsa.PrivateKey).Public().(*ecdsa.PublicKey)
	cert_pub_key_bytes := elliptic.Marshal(cert_pub_key.Curve, cert_pub_key.X, cert_pub_key.Y)
	signature, err := privateKey.Sign(cert_pub_key_bytes)
	return signature, err
}

// handleDelegateService listens for new connections to delegate service and handles them
func (dhtPeer *DHTPeer) handleDelegateService(ready *sync.WaitGroup) {
	defer dhtPeer.goroutines.Done()
	defer dhtPeer.tcpListener.Close()

	lerror, _, linfo, _ := dhtPeer.GetLoggers()

	done := false
L:
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
			break L
		}
	}
}

func (dhtPeer *DHTPeer) CheckPOR(record *acn.AgentRecord) (*acn.StatusBody, error) {
	addr := record.Address
	myPubKey, err := utils.FetchAIPublicKeyFromPubKey(dhtPeer.publicKey)
	ignore(err)
	status, err := dhtnode.IsValidProofOfRepresentation(record, addr, myPubKey)
	return status, err
}

// handleNewDelegationConnection handles a new delegate connection
// verifies agent record and registers agent in DHT, handles incoming envelopes
// and forwards them for processing
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

	lerror, _, linfo, _ := dhtPeer.GetLoggers()

	//linfo().Msgf("received a new connection from %s", conn.RemoteAddr().String())

	// read agent registration message
	conPipe := utils.ConnPipe{Conn: conn}

	var register *acn.RegisterPerformative
	var err error

	register, err = acn.ReadAgentRegistrationMessage(conPipe)
	if err != nil {
		lerror(err).Msg("while receiving agent's registration request")
		nbrConns.Dec()
		return
	}
	linfo().Msgf("Received registration request %s", register)

	// Get Register message
	record := register.Record
	addr := record.Address

	linfo().Msgf("connection from %s established for Address %s",
		conn.RemoteAddr().String(), addr)

	// check if the PoR is valid
	status, err := dhtPeer.CheckPOR(record)
	if err != nil || status.Code != acn.SUCCESS {
		lerror(err).Msg("PoR is not valid")
		acn_send_error := acn.SendAcnError(conPipe, err.Error(), status.Code)
		ignore(acn_send_error)
		nbrConns.Dec()
		return
	}

	// TOFIX(LR) post-pone answer until address successfully registered
	err = acn.SendAcnSuccess(conPipe)
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

	dhtPeer.acnStatusesLock.Lock()
	dhtPeer.acnStatuses[addr] = make(chan *acn.StatusBody, AcnStatusesQueueSize)
	dhtPeer.acnStatusesLock.Unlock()

	//linfo().Msgf("announcing tcp client address %s...", addr)
	// TOFIX(LR) disconnect client?
	if dhtPeer.IsAddressAnnouncementEnabled() {
		err = dhtPeer.RegisterAgentAddress(addr)
		if err != nil {
			lerror(err).Msgf("while announcing tcp client address %s to the dht", addr)
			return
		}
	}

	duration := timer.GetTimer(start)
	opLatencyRegister.Observe(float64(duration.Microseconds()))

	nbrConns.Inc()
	nbrClients.Inc()

	connPipe := utils.ConnPipe{Conn: conn}

	for {
		// read envelopes
		envel, err := aea.HandleAcnMessageFromPipe(connPipe, dhtPeer, addr)
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
		if envel == nil {
			// ACN status
			continue
		}
		linfo().Str(
			"addr",
			addr,
		).Msgf(
			"got envelope from delegate connection",
		)
		if envel.Sender != addr {
			err = errors.New("Sender (" + envel.Sender + ") must match registered address")
			lerror(err).Str("addr", addr).
				Msg("while routing delegate client envelope")
			continue
		}

		// initializing pairwise channel queues and one go routine per pair
		pair := envel.To + envel.Sender
		dhtPeer.syncMessagesLock.Lock()
		_, ok := dhtPeer.syncMessages[pair]
		dhtPeer.syncMessagesLock.Unlock()
		if !ok {
			dhtPeer.syncMessagesLock.Lock()
			dhtPeer.syncMessages[pair] = make(chan *aea.Envelope, 1000)
			dhtPeer.syncMessagesLock.Unlock()

			// route envelope
			dhtPeer.goroutines.Add(1)
			go func() {
				defer dhtPeer.goroutines.Done()
				dhtPeer.syncMessagesLock.Lock()
				pair_range := dhtPeer.syncMessages[pair]
				dhtPeer.syncMessagesLock.Unlock()

				for e := range pair_range {
					err := dhtPeer.RouteEnvelope(e)
					if err != nil {
						lerror(err).Str("addr", addr).
							Msg("while routing delegate client envelope")
						// TODO() send error back
					}
				}
			}()
		}
		// add to queue (nonblocking - buffered queue)
		dhtPeer.syncMessagesLock.Lock()

		select {
		case dhtPeer.syncMessages[pair] <- envel:
		default:
			// send back! error
			fmt.Println("CHANNEL FULL, DISCARDING <<<-------- ", string(envel.Message))
		}
		dhtPeer.syncMessagesLock.Unlock()
	}

	linfo().Str("addr", addr).
		Msg("delegate client disconnected")
	// Remove connection from map
	dhtPeer.tcpAddressesLock.Lock()
	delete(dhtPeer.tcpAddresses, addr)
	dhtPeer.tcpAddressesLock.Unlock()
	// TOFIX(LR) currently I am keeping the agent record

	dhtPeer.acnStatusesLock.Lock()
	delete(dhtPeer.acnStatuses, addr)
	dhtPeer.acnStatusesLock.Unlock()

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

func (dhtPeer *DHTPeer) GetCertAndSignature() (*tls.Certificate, []byte) {
	return dhtPeer.cert, dhtPeer.sslSignature
}

// RouteEnvelope to its destination
func (dhtPeer *DHTPeer) RouteEnvelope(envel *aea.Envelope) error {
	lerror, lwarn, linfo, ldebug := dhtPeer.GetLoggers()

	routeCount, _ := dhtPeer.monitor.GetGauge(metricOpRouteCount)
	routeCountAll, _ := dhtPeer.monitor.GetCounter(metricOpRouteCountAll)
	routeCountSuccess, _ := dhtPeer.monitor.GetCounter(metricOpRouteCountSuccess)
	opLatencyRoute, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRoute)
	timer := dhtPeer.monitor.Timer()

	routeCount.Inc()
	routeCountAll.Inc()
	start := timer.NewTimer()
	ldebug().Str("addr", envel.To).Msgf("-> Routing envelope: %s", envel.String())

	// get sender agent envelRec
	// TODO can change function signature to force the caller to provide the envelRec
	var envelRec *acn.AgentRecord
	sender := envel.Sender

	dhtPeer.agentRecordsLock.RLock()
	localRec, existsLocal := dhtPeer.agentRecords[sender]
	dhtPeer.agentRecordsLock.RUnlock()

	if sender == dhtPeer.myAgentAddress {
		envelRec = dhtPeer.myAgentRecord
	} else if dhtPeer.mailboxServer != nil && dhtPeer.mailboxServer.IsAddrRegistered(sender) {
		envelRec = dhtPeer.mailboxServer.GetAgentRecord(sender)
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

	if dhtPeer.mailboxServer != nil {
		if dhtPeer.mailboxServer.RouteEnvelope(envel) {
			linfo().Str("op", "route").Str("addr", target).
				Msg("route envelope destinated to mailbox registered agent...")
			return nil
		}
	}

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

		data, err := aea.MakeAcnMessageFromEnvelope(envel)
		if err != nil {
			lerror(err).Msgf("while serializing envelope: %s", envel)
			return err
		}
		err = utils.WriteBytesConn(connDelegate, data)
		if err != nil {
			lerror(err).Msgf("while writing envelope: %s", envel)
			return err
		}
		linfo().Str("addr", target).Msg("wait for acn ack")
		err = dhtPeer.AwaitAcnStatus(target)
		linfo().Str("addr", target).Msg("got acn ack")
		if err != nil {
			lerror(err).Msgf("while waiting acn ack for envelope: %s", envel)
			return err
		}

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
			linfo().Str("op", "route").Str("addr", target).
				Msgf("relay client peer is %s", peerID)
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

		streamPipe := utils.StreamPipe{Stream: stream}
		err = acn.SendEnvelopeMessage(streamPipe, envelBytes, envelRec)
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

		statusBody, err := acn.ReadAcnStatus(streamPipe)

		if err != nil {
			lerror(err).
				Str("op", "route").
				Str("addr", target).
				Msg("failed to decode acn status")
			routeCount.Dec()
			return err
		}
		if statusBody.Code != acn.SUCCESS {
			err = errors.New(statusBody.Code.String() + " : " + strings.Join(statusBody.Msgs, ":"))
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
func (dhtPeer *DHTPeer) lookupAddressDHT(address string) (peer.ID, *acn.AgentRecord, error) {
	lerror, lwarn, linfo, _ := dhtPeer.GetLoggers()
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
			streamPipe := utils.StreamPipe{Stream: stream}

			linfo().Str("op", "lookup").Str("addr", address).
				Msgf("getting agent record from provider %s...", provider)

			// perfrormaddress lookup
			record, err := acn.PerformAddressLookup(streamPipe, address)

			// Response is either a LookupResponse or Status
			ignore(stream.Reset())
			stream.Close()
			if err != nil {
				lwarn().Str("op", "lookup").Str("addr", address).
					Msgf("Failed agent lookup from provider %s (%s), looking up other providers...", provider, err.Error())
				continue
			}

			// lookupResponse must be set
			valid, err := dhtnode.IsValidProofOfRepresentation(
				record,
				address,
				record.PeerPublicKey,
			)
			if err != nil || valid.Code != acn.SUCCESS {
				errMsg := valid.Code.String() + " : " + strings.Join(valid.Msgs, ":")
				if err == nil {
					err = errors.New(errMsg)
				} else {
					err = errors.Wrap(err, valid.Code.String()+" : "+strings.Join(valid.Msgs, ":"))
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

// handleAeaEnvelopeStream deals with incoming envelopes on the AeaEnvelopeStream
// envelopes arrive from other peers (full or client) and are processed
// by HandleAeaEnvelope
func (dhtPeer *DHTPeer) handleAeaEnvelopeStream(stream network.Stream) {
	common.HandleAeaEnvelopeStream(dhtPeer, stream)
}

// Callback to handle and route  aea envelope comes from the aea envelope stream
// return ACNError if message routing failed, otherwise nil.
func (dhtPeer *DHTPeer) HandleAeaEnvelope(envel *aea.Envelope) *acn.ACNError {
	var err error
	lerror, lwarn, linfo, _ := dhtPeer.GetLoggers()
	dhtPeer.tcpAddressesLock.RLock()
	connDelegate, existsDelegate := dhtPeer.tcpAddresses[envel.To]
	dhtPeer.tcpAddressesLock.RUnlock()

	if dhtPeer.mailboxServer != nil {
		if dhtPeer.mailboxServer.RouteEnvelope(envel) {
			linfo().Str("op", "route").Str("addr", envel.To).
				Msg("route envelope destinated to mailbox registered agent...")
			return nil
		}
	}

	if existsDelegate {
		linfo().Msgf(
			"Sending envelope to tcp delegate client %s...",
			connDelegate.RemoteAddr().String(),
		)
		data, err := aea.MakeAcnMessageFromEnvelope(envel)
		if err != nil {
			lerror(err).Msgf("while serializing envelope: %s", envel)
			return &acn.ACNError{
				Err:       errors.New("serializing envelope error"),
				ErrorCode: acn.ERROR_DECODE,
			}
		}
		err = utils.WriteBytesConn(connDelegate, data)

		if err != nil {
			lerror(
				err,
			).Msgf(
				"while sending envelope to tcp client %s",
				connDelegate.RemoteAddr().String(),
			)
			return &acn.ACNError{
				Err:       errors.New("agent is not ready"),
				ErrorCode: acn.ERROR_AGENT_NOT_READY,
			}
		}
		err = dhtPeer.AwaitAcnStatus(envel.To)
		if err != nil {
			lerror(
				err,
			).Msgf(
				"while awating acn ack on sending  envelope to tcp client %s",
				connDelegate.RemoteAddr().String(),
			)
			return &acn.ACNError{
				Err:       errors.New("while awating acn ack on sending  envelope to tcp clien"),
				ErrorCode: acn.ERROR_AGENT_NOT_READY,
			}
		}
	} else if envel.To == dhtPeer.myAgentAddress {
		if dhtPeer.processEnvelope == nil {
			lerror(err).Msgf("while processing envelope by agent")
			return &acn.ACNError{Err: errors.New("agent is not ready"), ErrorCode: acn.ERROR_AGENT_NOT_READY}
		}
		linfo().Msg("Processing envelope by local agent...")
		err = dhtPeer.processEnvelope(envel)
		ignore(err)
	} else {
		lwarn().Msgf("ignored envelope %s", envel.String())
		return &acn.ACNError{Err: errors.New("unknown agent address"), ErrorCode: acn.ERROR_UNKNOWN_AGENT_ADDRESS}
	}

	// all good
	return nil
}

func (dhtPeer *DHTPeer) handleAeaAddressStream(stream network.Stream) {
	common.HandleAeaAddressStream(dhtPeer, stream)

}

func (dhtPeer *DHTPeer) HandleAeaAddressRequest(
	reqAddress string,
) (*acn.AgentRecord, *acn.ACNError) {
	lerror, _, linfo, _ := dhtPeer.GetLoggers()

	//	Msg("Received query for addr")
	var sPeerID string
	var sRecord *acn.AgentRecord = nil

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
	} else if dhtPeer.mailboxServer != nil && dhtPeer.mailboxServer.IsAddrRegistered(reqAddress) {
		sPeerID = idRelay
		sRecord = dhtPeer.mailboxServer.GetAgentRecord(reqAddress)
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

			return nil, &acn.ACNError{
				Err:       errors.New("unknown agent address"),
				ErrorCode: acn.ERROR_UNKNOWN_AGENT_ADDRESS,
			}
		}
	}

	if sRecord == nil {
		return nil, &acn.ACNError{
			Err:       errors.New("unknown agent address"),
			ErrorCode: acn.ERROR_UNKNOWN_AGENT_ADDRESS,
		}
	}

	// record found, send
	linfo().Str("op", "resolve").Str("addr", reqAddress).
		Msgf("sending agent record (%s) %s", sPeerID, sRecord)

	return sRecord, nil
}

func (dhtPeer *DHTPeer) handleAeaNotifStream(stream network.Stream) {
	lerror, _, _, ldebug := dhtPeer.GetLoggers()

	//linfo().Str("op", "notif").
	//	Msgf("Got a new notif stream")
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

	defer dhtPeer.enableAddressAnnouncementWg.Done()
	dhtPeer.enableAddressAnnouncementWg.Add(1)

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

	if dhtPeer.myAgentAddress != "" && !dhtPeer.IsAddressAnnounced(dhtPeer.myAgentAddress) {
		err := dhtPeer.RegisterAgentAddress(dhtPeer.myAgentAddress)
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
			err := dhtPeer.RegisterAgentAddress(addr)
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
			err := dhtPeer.RegisterAgentAddress(addr)
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
	ldebug().Msg("Address was announced")
	// got a connection to a peer, so now we can allow address announcements
	dhtPeer.enableAddressAnnouncementLock.Lock()
	dhtPeer.enableAddressAnnouncement = true
	dhtPeer.enableAddressAnnouncementLock.Unlock()
}

func (dhtPeer *DHTPeer) IsAddressAnnouncementEnabled() bool {
	// wait if new peers connection establish in process
	dhtPeer.enableAddressAnnouncementWg.Wait()
	dhtPeer.enableAddressAnnouncementLock.Lock()
	isEnabled := dhtPeer.enableAddressAnnouncement
	dhtPeer.enableAddressAnnouncementLock.Unlock()
	return isEnabled
}

func (dhtPeer *DHTPeer) handleAeaRegisterStream(stream network.Stream) {
	lerror, _, linfo, _ := dhtPeer.GetLoggers()

	// to limit spamming
	time.Sleep(dhtPeer.registrationDelay)

	nbrClients, _ := dhtPeer.monitor.GetCounter(metricServiceRelayClientsCountAll)

	opLatencyRegister, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRegister)
	timer := dhtPeer.monitor.Timer()
	start := timer.NewTimer()

	//linfo().Str("op", "register").
	//	Msg("Got a new aea register stream")
	streamPipe := utils.StreamPipe{Stream: stream}

	// Get Register message
	register, err := acn.ReadAgentRegistrationMessage(streamPipe)
	if err != nil {
		lerror(err).Str("op", "register").
			Msg("while reading relay client registration request from stream")
		err = stream.Reset()
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

	if err != nil || status.Code != acn.SUCCESS {
		lerror(err).Msg("PoR is not valid")
		acn_send_error := acn.SendAcnError(streamPipe, err.Error(), status.Code)
		ignore(acn_send_error)
		return
	}

	// TOFIX(LR) post-pone answer until address successfully registered
	err = acn.SendAcnSuccess(streamPipe)
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

	linfo().Str("op", "register").
		Str("addr", clientAddr).
		Msgf("peer added: %s", clientPeerID)

	if dhtPeer.IsAddressAnnouncementEnabled() && !dhtPeer.IsAddressAnnounced(string(clientAddr)) {
		linfo().Str("op", "register").
			Str("addr", clientAddr).
			Msgf("Announcing client address on behalf of %s...", clientPeerID)
		err = dhtPeer.RegisterAgentAddress(string(clientAddr))
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

func (dhtPeer *DHTPeer) RegisterAgentAddress(addr string) error {
	_, _, linfo, _ := dhtPeer.GetLoggers()

	if dhtPeer.IsAddressAnnounced(addr) {
		// already announced
		return nil
	}

	dhtPeer.setAddressAnnounced(addr)

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

func (dhtPeer *DHTPeer) IsAddressAnnounced(address string) bool {
	dhtPeer.addressAnnouncedMapLock.Lock()
	_, present := dhtPeer.addressAnnouncedMap[address]
	dhtPeer.addressAnnouncedMapLock.Unlock()
	return present
}

func (dhtPeer *DHTPeer) setAddressAnnounced(address string) {
	dhtPeer.addressAnnouncedMapLock.Lock()
	dhtPeer.addressAnnouncedMap[address] = true
	dhtPeer.addressAnnouncedMapLock.Unlock()
}

func (dhtPeer *DHTPeer) AddAcnStatusMessage(status *acn.StatusBody, counterpartyID string) {
	dhtPeer.acnStatusesLock.Lock()
	queue := dhtPeer.acnStatuses[counterpartyID]
	dhtPeer.acnStatusesLock.Unlock()

	queue <- status
}

func (dhtPeer *DHTPeer) AwaitAcnStatus(counterpartyID string) error {
	lerror, _, _, _ := dhtPeer.GetLoggers()

	dhtPeer.acnStatusesLock.Lock()
	counterParty := dhtPeer.acnStatuses[counterpartyID]
	dhtPeer.acnStatusesLock.Unlock()

	status, err := acn.WaitForStatus(counterParty, AcnStatusTimeout)

	if err != nil {
		lerror(err).Msg("timeout on status wait")
		return err
	}
	if status.Code != acn.SUCCESS {
		lerror(err).Msgf("bad status: %d", status.Code)
		return errors.New("bad status!")
	}
	return err

}
