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
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/rs/zerolog"

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
	myAgentReady     func() bool
	dhtAddresses     map[string]string
	tcpAddresses     map[string]net.Conn
	dhtAddressesLock sync.RWMutex
	tcpAddressesLock sync.RWMutex
	processEnvelope  func(*aea.Envelope) error

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
	dhtPeer.dhtAddressesLock = sync.RWMutex{}
	dhtPeer.tcpAddressesLock = sync.RWMutex{}

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

func (dhtPeer *DHTPeer) setupMonitoring() {
	if dhtPeer.monitoringPort != 0 {
		dhtPeer.monitor = monitoring.NewPrometheusMonitoring(monitoringNamespace, dhtPeer.monitoringPort)
	} else {
		dhtPeer.monitor = monitoring.NewFileMonitoring(monitoringNamespace, false)
	}

	dhtPeer.addMonitoringMetrics()
}

func (dhtPeer *DHTPeer) startMonitoring(ready *sync.WaitGroup) {
	_, _, linfo, _ := dhtPeer.getLoggers()
	linfo().Msg("Starting monitoring service: " + dhtPeer.monitor.Info())
	dhtPeer.monitor.Start()
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
	_, err = dhtPeer.monitor.NewHistogram(metricOpLatencyRoute,
		"Histogram for end-to-end time to route an envelope to its destination, excluding time to send envelope itself",
		buckets)
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

	// read agent address
	buf, err := utils.ReadBytesConn(conn)
	if err != nil {
		lerror(err).Msg("while receiving agent's Address")
		nbrConns.Dec()
		return
	}

	addr := string(buf)
	linfo().Msgf("connection from %s established for Address %s",
		conn.RemoteAddr().String(), addr)

	// Add connection to map
	dhtPeer.tcpAddressesLock.Lock()
	dhtPeer.tcpAddresses[addr] = conn
	dhtPeer.tcpAddressesLock.Unlock()
	if dhtPeer.addressAnnounced {
		//linfo().Msgf("announcing tcp client address %s...", addr)
		err = dhtPeer.registerAgentAddress(addr)
		if err != nil {
			lerror(err).Msgf("while announcing tcp client address %s to the dht", addr)
			return
		}
	}

	err = utils.WriteBytesConn(conn, []byte("DONE"))
	ignore(err)

	duration := timer.GetTimer(start)
	opLatencyRegister.Observe(float64(duration.Microseconds()))

	nbrConns.Inc()
	nbrClients.Inc()

	for {
		// read envelopes
		envel, err := utils.ReadEnvelopeConn(conn)
		if err != nil {
			if err == io.EOF {
				linfo().Str("addr", addr).Msgf("connection closed by client: %s, stopping...", err.Error())
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
			err := dhtPeer.RouteEnvelope(envel)
			ignore(err)
		}()
	}

	// Remove connection from map
	dhtPeer.tcpAddressesLock.Lock()
	delete(dhtPeer.tcpAddresses, addr)
	dhtPeer.tcpAddressesLock.Unlock()

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
	lerror, lwarn, linfo, _ := dhtPeer.getLoggers()

	routeCount, _ := dhtPeer.monitor.GetGauge(metricOpRouteCount)
	routeCountAll, _ := dhtPeer.monitor.GetCounter(metricOpRouteCountAll)
	routeCountSuccess, _ := dhtPeer.monitor.GetCounter(metricOpRouteCountSuccess)
	opLatencyRoute, _ := dhtPeer.monitor.GetHistogram(metricOpLatencyRoute)
	timer := dhtPeer.monitor.Timer()

	routeCount.Inc()
	routeCountAll.Inc()
	start := timer.NewTimer()

	target := envel.To

	if target == dhtPeer.myAgentAddress {
		linfo().Str("op", "route").Str("addr", target).
			Msg("route envelope destinated to my local agent...")
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
		}
	} else if conn, exists := dhtPeer.tcpAddresses[target]; exists {
		linfo().Str("op", "route").Str("addr", target).
			Msgf("destination is a delegate client %s", conn.RemoteAddr().String())
		routeCount.Dec()
		routeCountSuccess.Inc()
		duration := timer.GetTimer(start)
		opLatencyRoute.Observe(float64(duration.Microseconds()))
		return utils.WriteEnvelopeConn(conn, envel)
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
			peerID, err = dhtPeer.lookupAddressDHT(target)
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
		err = utils.WriteEnvelope(envel, stream)
		if err != nil {
			errReset := stream.Reset()
			ignore(errReset)
		} else {
			routeCountSuccess.Inc()
			stream.Close()
		}

		routeCount.Dec()
		return err
	}

	return nil
}

func (dhtPeer *DHTPeer) lookupAddressDHT(address string) (peer.ID, error) {
	lerror, lwarn, linfo, _ := dhtPeer.getLoggers()
	var err error

	dhtLookupLatency, _ := dhtPeer.monitor.GetHistogram(metricDHTOpLatencyLookup)
	timer := dhtPeer.monitor.Timer()

	addressCID, err := utils.ComputeCID(address)
	if err != nil {
		return "", err
	}

	linfo().Str("op", "lookup").Str("addr", address).
		Msgf("Querying for providers for cid %s...", addressCID.String())
	ctx, cancel := context.WithTimeout(context.Background(), addressLookupTimeout)
	defer cancel()
	//var elapsed time.Duration
	var provider peer.AddrInfo
	var connected bool = false
	var stream network.Stream

	start := timer.NewTimer()

	noProvider := false
	for !connected {
		providers := dhtPeer.dht.FindProvidersAsync(ctx, addressCID, 0)

		for provider = range providers {
			duration := timer.GetTimer(start)
			dhtLookupLatency.Observe(float64(duration.Microseconds()))

			//linfo().Str("op", "lookup").Str("addr", address).
			//	Msgf("found provider %s after %s", provider, elapsed.String())

			// Add peer to host PeerStore - the provider should be the holder of the address
			dhtPeer.routedHost.Peerstore().AddAddrs(provider.ID, provider.Addrs, peerstore.PermanentAddrTTL)

			//linfo().Str("op", "lookup").Str("addr", address).
			//	Msgf("opening stream to the address provider %s...", provider)
			ctxConnect := context.Background()
			stream, err = dhtPeer.routedHost.NewStream(ctxConnect, provider.ID, dhtnode.AeaAddressStream)
			if err == nil {
				connected = true
				break
			}

			dhtPeer.routedHost.Peerstore().ClearAddrs(provider.ID)
			lwarn().Str("op", "lookup").Str("addr", address).Msgf("couldn't open stream to address provider %s: %s, looking up for other providers...", provider, err.Error())
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
				return "", err
			}
		} else if !connected {
			return "", err
		}
	}

	linfo().Str("op", "lookup").Str("addr", address).
		Msgf("reading peer ID from provider %s...", provider)

	err = utils.WriteBytes(stream, []byte(address))
	if err != nil {
		return "", errors.New("ERROR while sending address to peer:" + err.Error())
	}

	msg, err := utils.ReadString(stream)
	if err != nil {
		return "", errors.New("ERROR while reading target peer id from peer:" + err.Error())
	}
	stream.Close()

	peerid, err := peer.Decode(msg)
	if err != nil {
		return "", errors.New("CRITICAL couldn't get peer ID from message:" + err.Error())
	}

	return peerid, nil
}

func (dhtPeer *DHTPeer) handleAeaEnvelopeStream(stream network.Stream) {
	lerror, lwarn, linfo, _ := dhtPeer.getLoggers()

	//linfo().Msg("Got a new aea envelope stream")

	envel, err := utils.ReadEnvelope(stream)
	if err != nil {
		lerror(err).Msg("while reading envelope from stream")
		err = stream.Reset()
		ignore(err)
		return
	}
	stream.Close()

	linfo().Msgf("Received envelope from peer %s", envel.String())

	// check if destination is a tcp client
	if conn, exists := dhtPeer.tcpAddresses[envel.To]; exists {
		linfo().Msgf("Sending envelope to tcp delegate client %s...", conn.RemoteAddr().String())
		err = utils.WriteEnvelopeConn(conn, envel)
		if err != nil {
			lerror(err).Msgf("while sending envelope to tcp client %s", conn.RemoteAddr().String())
		}
	} else if envel.To == dhtPeer.myAgentAddress && dhtPeer.processEnvelope != nil {
		linfo().Msg("Processing envelope by local agent...")
		err = dhtPeer.processEnvelope(envel)
		if err != nil {
			lerror(err).Msgf("while processing envelope by agent")
		}
	} else {
		lwarn().Msgf("ignored envelope %s", envel.String())
	}
}

func (dhtPeer *DHTPeer) handleAeaAddressStream(stream network.Stream) {
	lerror, _, linfo, _ := dhtPeer.getLoggers()

	//linfo().Msgf("Got a new aea address stream")

	reqAddress, err := utils.ReadString(stream)
	if err != nil {
		lerror(err).Str("op", "resolve").Str("addr", reqAddress).
			Msg("while reading Address from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	//linfo().Str("op", "resolve").Str("addr", reqAddress).
	//	Msg("Received query for addr")
	var sPeerID string
	dhtPeer.dhtAddressesLock.RLock()
	idRelay, existsRelay := dhtPeer.dhtAddresses[reqAddress]
	dhtPeer.dhtAddressesLock.RUnlock()
	dhtPeer.tcpAddressesLock.RLock()
	_, existsDelegate := dhtPeer.tcpAddresses[reqAddress]
	dhtPeer.tcpAddressesLock.RUnlock()

	if reqAddress == dhtPeer.myAgentAddress {
		peerID, err := peer.IDFromPublicKey(dhtPeer.publicKey)
		if err != nil {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msgf("CRITICAL could not get peer ID from public key %s", dhtPeer.publicKey)
			return
		}
		sPeerID = peerID.Pretty()
	} else if existsRelay {
		linfo().Str("op", "resolve").Str("addr", reqAddress).
			Msg("found address in my relay clients map")
		sPeerID = idRelay
	} else if existsDelegate {
		linfo().Str("op", "resolve").Str("addr", reqAddress).
			Msgf("found address in my delegate clients map")
		peerID, err := peer.IDFromPublicKey(dhtPeer.publicKey)
		if err != nil {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msgf("CRITICAL could not get peer ID from public key %s", dhtPeer.publicKey)
			return
		}
		sPeerID = peerID.Pretty()
	} else {
		// needed when a relay client queries for a peer ID
		//linfo().Str("op", "resolve").Str("addr", reqAddress).
		//	Msg("did NOT found the address locally, looking for it in the DHT...")
		peerID, err := dhtPeer.lookupAddressDHT(reqAddress)
		if err == nil {
			linfo().Str("op", "resolve").Str("addr", reqAddress).
				Msg("found address on the DHT")
			sPeerID = peerID.Pretty()
		} else {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msgf("did NOT find address locally or on the DHT.")
			return
		}
	}

	linfo().Str("op", "resolve").Str("addr", reqAddress).
		Msgf("sending peer id %s", sPeerID)
	err = utils.WriteBytes(stream, []byte(sPeerID))
	if err != nil {
		lerror(err).Str("op", "resolve").Str("addr", reqAddress).
			Msg("While sending peerID to peer")
	}
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
		ctx, cancel := context.WithTimeout(context.Background(), routingTableConnectionUpdateTimeout)
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

	clientAddr, err := utils.ReadBytes(stream)
	if err != nil {
		lerror(err).Str("op", "register").
			Msg("while reading client Address from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	err = utils.WriteBytes(stream, []byte("doneAddress"))
	ignore(err)

	clientPeerID, err := utils.ReadBytes(stream)
	if err != nil {
		lerror(err).Str("op", "register").
			Msgf("while reading client peerID from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	err = utils.WriteBytes(stream, []byte("donePeerID"))
	ignore(err)

	nbrClients.Inc()

	//linfo().Str("op", "register").
	//	Str("addr", string(clientAddr)).
	//	Msgf("Received address registration request for peer id %s", string(clientPeerID))
	dhtPeer.dhtAddressesLock.Lock()
	dhtPeer.dhtAddresses[string(clientAddr)] = string(clientPeerID)
	dhtPeer.dhtAddressesLock.Unlock()
	if dhtPeer.addressAnnounced {
		linfo().Str("op", "register").
			Str("addr", string(clientAddr)).
			Msgf("Announcing client address on behalf of %s...", string(clientPeerID))
		err = dhtPeer.registerAgentAddress(string(clientAddr))
		if err != nil {
			lerror(err).Str("op", "register").
				Str("addr", string(clientAddr)).
				Msg("while announcing client address to the dht")
			err = stream.Reset()
			ignore(err)
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
