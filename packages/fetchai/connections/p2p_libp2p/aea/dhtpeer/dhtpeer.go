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

package dhtpeer

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"strconv"
	"time"

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
	utils "libp2p_node/aea/utils"
)

// panics if err is not nil
func check(err error) {
	if err != nil {
		panic(err)
	}
}

func ignore(err error) {
	if err != nil {
		log.Println("TRACE", err)
	}
}

// DHTPeer A full libp2p node for the Agents Communication Network.
// It is required to have a local address and a public one
// and can acts as a relay for `DHTClient`.
// Optionally, it provides delegate service for tcp clients.
type DHTPeer struct {
	host         string
	port         uint16
	publicHost   string
	publicPort   uint16
	delegatePort uint16
	enableRelay  bool

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
	processEnvelope  func(aea.Envelope) error
}

// New creates a new DHTPeer
func New(opts ...Option) (*DHTPeer, error) {
	var err error
	dhtPeer := &DHTPeer{}

	dhtPeer.dhtAddresses = map[string]string{}
	dhtPeer.tcpAddresses = map[string]net.Conn{}

	for _, opt := range opts {
		if err := opt(dhtPeer); err != nil {
			return nil, err
		}
	}

	/* check correct configuration */

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

	// connect to the booststrap nodes
	if len(dhtPeer.bootstrapPeers) > 0 {
		err = utils.BootstrapConnect(ctx, dhtPeer.routedHost, dhtPeer.bootstrapPeers)
		if err != nil {
			return nil, err
		}
	}

	// Bootstrap the dht
	err = dhtPeer.dht.Bootstrap(ctx)
	if err != nil {
		return nil, err
	}

	// print the multiaddress for aea python connection
	hostAddr, _ := multiaddr.NewMultiaddr(
		fmt.Sprintf("/p2p/%s", dhtPeer.routedHost.ID().Pretty()))
	addrs := dhtPeer.routedHost.Addrs()
	log.Printf("INFO My ID is %s\n", dhtPeer.routedHost.ID().Pretty())
	log.Println("INFO I can be reached at:")
	log.Println("MULTIADDRS_LIST_START") // NOTE: keyword
	for _, addr := range addrs {
		fmt.Println(addr.Encapsulate(hostAddr))
	}
	fmt.Println("MULTIADDRS_LIST_END") // NOTE: keyword

	log.Println("INFO successfully created libp2p node!")

	/* setup DHTPeer message handlers and services */

	// relay service
	if dhtPeer.enableRelay {
		// Allow clients to register their agents addresses
		log.Println("DEBUG Setting /aea-register/0.1.0 stream...")
		dhtPeer.routedHost.SetStreamHandler("/aea-register/0.1.0",
			dhtPeer.handleAeaRegisterStream)
	}

	// new peers connection notification, so that this peer can register its addresses
	dhtPeer.routedHost.SetStreamHandler("/aea-notif/0.1.0",
		dhtPeer.handleAeaNotifStream)

	// Notify bootstrap peers if any
	for _, bPeer := range dhtPeer.bootstrapPeers {
		ctx := context.Background()
		s, err := dhtPeer.routedHost.NewStream(ctx, bPeer.ID, "/aea-notif/0.1.0")
		if err != nil {
			log.Println("ERROR failed to notify bootstrap peer", bPeer.ID, ":", err.Error())
			return nil, err
		}
		_, err = s.Write([]byte("/aea-notif/0.1.0"))
		if err != nil {
			log.Println("ERROR failed to notify bootstrap peer", bPeer.ID, ":", err.Error())
			return nil, err
		}
		s.Close()
	}

	// if peer is joining an existing network, announce my agent address if set
	if len(dhtPeer.bootstrapPeers) > 0 && dhtPeer.myAgentAddress != "" {
		err := dhtPeer.registerAgentAddress(dhtPeer.myAgentAddress)
		if err != nil {
			return nil, err
		}
		dhtPeer.addressAnnounced = true
	}

	// aea addresses lookup
	log.Println("DEBUG Setting /aea-address/0.1.0 stream...")
	dhtPeer.routedHost.SetStreamHandler("/aea-address/0.1.0", dhtPeer.handleAeaAddressStream)

	// Set a stream handler for envelopes
	log.Println("DEBUG Setting /aea/0.1.0 stream...")
	dhtPeer.routedHost.SetStreamHandler("/aea/0.1.0", dhtPeer.handleAeaEnvelopeStream)

	// setup delegate service
	if dhtPeer.delegatePort != 0 {
		go dhtPeer.launchDelegateService()
	}

	return dhtPeer, nil
}

func (dhtPeer *DHTPeer) launchDelegateService() {
	var err error

	uri := dhtPeer.host + ":" + strconv.FormatInt(int64(dhtPeer.delegatePort), 10)
	dhtPeer.tcpListener, err = net.Listen("tcp", uri)
	if err != nil {
		log.Println("ERROR while setting up listening tcp socket", uri)
		check(err)
	}
	defer dhtPeer.tcpListener.Close()

	for {
		conn, err := dhtPeer.tcpListener.Accept()
		if err != nil {
			log.Println("ERROR while accepting a new connection:", err)
			continue
		}
		go dhtPeer.handleNewDelegationConnection(conn)
	}
}

func (dhtPeer *DHTPeer) handleNewDelegationConnection(conn net.Conn) {
	log.Println("INFO received a new connection from ", conn.RemoteAddr().String())

	// read agent address
	buf, err := utils.ReadBytesConn(conn)
	if err != nil {
		log.Println("ERROR while receiving agent's Address:", err)
		return
	}
	err = utils.WriteBytesConn(conn, []byte("DONE"))
	ignore(err)

	addr := string(buf)
	log.Println("DEBUG connection from ", conn.RemoteAddr().String(),
		"established for Address", addr)

	// Add connection to map
	dhtPeer.tcpAddresses[addr] = conn
	if dhtPeer.addressAnnounced {
		log.Println("DEBUG announcing tcp client address", addr, "...")
		err = dhtPeer.registerAgentAddress(addr)
		if err != nil {
			log.Println("ERROR while announcing tcp client address", addr, "to the dht:", err)
			return
		}
	}

	for {
		// read envelopes
		envel, err := utils.ReadEnvelopeConn(conn)
		if err != nil {
			if err == io.EOF {
				log.Println("INFO connection closed by client:", err)
				log.Println("      stoppig...")
			} else {
				log.Println("ERROR while reading envelope from client connection:", err)
				log.Println("      aborting..")
			}
			break
		}

		// route envelope
		go func() {
			err := dhtPeer.RouteEnvelope(*envel)
			ignore(err)
		}()
	}

}

// ProcessEnvelope register callback function
func (dhtPeer *DHTPeer) ProcessEnvelope(fn func(aea.Envelope) error) {
	dhtPeer.processEnvelope = fn
}

// RouteEnvelope to its destination
func (dhtPeer *DHTPeer) RouteEnvelope(envel aea.Envelope) error {
	target := envel.To

	if target == dhtPeer.myAgentAddress {
		log.Println("DEBUG route envelope destinated to my local agent ...")
		for dhtPeer.myAgentReady != nil && !dhtPeer.myAgentReady() {
			log.Println("DEBUG route agent not ready yet, sleeping for some time ...")
			time.Sleep(time.Duration(100) * time.Millisecond)
		}
		if dhtPeer.processEnvelope != nil {
			err := dhtPeer.processEnvelope(envel)
			if err != nil {
				return err
			}
		} else {
			log.Println("WARN route ProcessEnvelope not set, ignoring envelope", envel)
		}
	} else if conn, exists := dhtPeer.tcpAddresses[target]; exists {
		log.Println("DEBUG route - destination", target, " is a delegate client",
			conn.RemoteAddr().String())
		return utils.WriteEnvelopeConn(conn, envel)
	} else {
		var peerID peer.ID
		var err error
		if sPeerID, exists := dhtPeer.dhtAddresses[target]; exists {
			log.Println("DEBUG route - destination", target, "is a relay client")
			peerID, err = peer.Decode(sPeerID)
			if err != nil {
				log.Println("CRITICAL couldn't parse peer id from relay client id")
				return err
			}
		} else {
			log.Println("DEBUG route - did NOT found destination address locally, looking for it in the DHT...")
			peerID, err = dhtPeer.lookupAddressDHT(target)
			if err != nil {
				log.Println("ERROR route - while looking up address on the DHT:", err)
				return err
			}
		}

		log.Println("DEBUG route - got peer id for agent address", target, ":", peerID.Pretty())

		log.Println("DEBUG route - opening stream to target ", peerID)
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		defer cancel()
		stream, err := dhtPeer.routedHost.NewStream(ctx, peerID, "/aea/0.1.0")
		if err != nil {
			log.Println("ERROR route - timeout, couldn't open stream to target ", peerID)
			return err
		}

		log.Println("DEBUG route - sending envelope to target...")
		err = utils.WriteEnvelope(envel, stream)
		if err != nil {
			errReset := stream.Reset()
			ignore(errReset)
		} else {
			stream.Close()
		}

		return err
	}

	return nil
}

func (dhtPeer *DHTPeer) lookupAddressDHT(address string) (peer.ID, error) {
	addressCID, err := utils.ComputeCID(address)
	if err != nil {
		return "", err
	}

	log.Println("INFO Querying for providers for cid", addressCID.String(),
		" of address", address, "...")
	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()
	providers := dhtPeer.dht.FindProvidersAsync(ctx, addressCID, 1)
	start := time.Now()
	provider := <-providers
	elapsed := time.Since(start)
	log.Println("DEBUG found provider", provider, "for address", address, "after", elapsed)

	// Add peer to host PeerStore - the provider should be the holder of the address
	dhtPeer.routedHost.Peerstore().AddAddrs(provider.ID, provider.Addrs, peerstore.PermanentAddrTTL)

	log.Println("DEBUG opening stream to the address provider", provider)
	ctx = context.Background()
	s, err := dhtPeer.routedHost.NewStream(ctx, provider.ID, "/aea-address/0.1.0")
	if err != nil {
		return "", err
	}

	log.Println("DEBUG reading peer ID from provider for addr", address)

	err = utils.WriteBytes(s, []byte(address))
	if err != nil {
		return "", errors.New("ERROR while sending address to peer:" + err.Error())
	}

	msg, err := utils.ReadString(s)
	if err != nil {
		return "", errors.New("ERROR while reading target peer id from peer:" + err.Error())
	}
	s.Close()

	peerid, err := peer.Decode(msg)
	if err != nil {
		return "", errors.New("CRITICAL couldn't get peer ID from message:" + err.Error())
	}

	return peerid, nil
}

func (dhtPeer *DHTPeer) handleAeaEnvelopeStream(stream network.Stream) {
	log.Println("DEBUG Got a new aea envelope stream")

	envel, err := utils.ReadEnvelope(stream)
	if err != nil {
		log.Println("ERROR While reading envelope from stream:", err)
		err = stream.Reset()
		ignore(err)
		return
	}
	stream.Close()

	log.Println("DEBUG Received envelope from peer:", envel)

	// check if destination is a tcp client
	if conn, exists := dhtPeer.tcpAddresses[envel.To]; exists {
		err = utils.WriteEnvelopeConn(conn, *envel)
		if err != nil {
			log.Println("ERROR While sending envelope to tcp client:", err)
		}
	} else if envel.To == dhtPeer.myAgentAddress && dhtPeer.processEnvelope != nil {
		err = dhtPeer.processEnvelope(*envel)
		if err != nil {
			log.Println("ERROR While processing envelope by agent:", err)
		}
	} else {
		log.Println("WARN ignored envelope", *envel)
	}
}

func (dhtPeer *DHTPeer) handleAeaAddressStream(stream network.Stream) {
	log.Println("DEBUG Got a new aea address stream")

	reqAddress, err := utils.ReadString(stream)
	if err != nil {
		log.Println("ERROR While reading Address from stream:", err)
		err = stream.Reset()
		ignore(err)
		return
	}

	log.Println("DEBUG Received query for addr:", reqAddress)
	var sPeerID string

	if reqAddress == dhtPeer.myAgentAddress {
		peerID, err := peer.IDFromPublicKey(dhtPeer.publicKey)
		if err != nil {
			log.Println("CRITICAL could not get peer ID from public key",
				dhtPeer.publicKey, ":", err.Error())
			return
		}
		sPeerID = peerID.Pretty()
	} else if id, exists := dhtPeer.dhtAddresses[reqAddress]; exists {
		log.Println("DEBUG found address", reqAddress, "in my relay clients map")
		sPeerID = id
	} else if _, exists := dhtPeer.tcpAddresses[reqAddress]; exists {
		log.Println("DEBUG found address", reqAddress, "in my delegate clients map")
		peerID, err := peer.IDFromPublicKey(dhtPeer.publicKey)
		if err != nil {
			log.Println("CRITICAL could not get peer ID from public key",
				dhtPeer.publicKey, ":", err.Error())
			return
		}
		sPeerID = peerID.Pretty()
	} else {
		// needed when a relay client queries for a peer ID
		log.Println("DEBUG did NOT found the address locally, looking for it in the DHT...")
		peerID, err := dhtPeer.lookupAddressDHT(reqAddress)
		if err == nil {
			log.Println("DEBUG found address", reqAddress, "on the DHT")
			sPeerID = peerID.Pretty()
		} else {
			log.Println("ERROR did NOT find address", reqAddress, " locally or on the DHT.")
			return
		}
	}

	log.Println("DEBUG sending peer id", sPeerID, "for address", reqAddress)
	err = utils.WriteBytes(stream, []byte(sPeerID))
	if err != nil {
		log.Println("ERROR While sending peerID to peer:", err)
	}
}

func (dhtPeer *DHTPeer) handleAeaNotifStream(stream network.Stream) {
	log.Println("DEBUG Got a new notif stream")

	if !dhtPeer.addressAnnounced {
		if dhtPeer.myAgentAddress != "" {
			err := dhtPeer.registerAgentAddress(dhtPeer.myAgentAddress)
			if err != nil {
				log.Println("ERROR while announcing my agent address to dht:" + err.Error())
				return
			}
		}
		if dhtPeer.enableRelay {
			for addr := range dhtPeer.dhtAddresses {
				err := dhtPeer.registerAgentAddress(addr)
				if err != nil {
					log.Println("ERROR while announcing relay client address", addr, ":", err)
				}
			}

		}
		if dhtPeer.delegatePort != 0 {
			for addr := range dhtPeer.tcpAddresses {
				err := dhtPeer.registerAgentAddress(addr)
				if err != nil {
					log.Println("ERROR while announcing delegate client address", addr, ":", err)
				}
			}

		}
	}
	dhtPeer.addressAnnounced = true
}

func (dhtPeer *DHTPeer) handleAeaRegisterStream(stream network.Stream) {
	log.Println("DEBUG Got a new aea register stream")

	clientAddr, err := utils.ReadBytes(stream)
	if err != nil {
		log.Println("ERROR While reading client Address from stream:", err)
		err = stream.Reset()
		ignore(err)
		return
	}

	err = utils.WriteBytes(stream, []byte("doneAddress"))
	ignore(err)

	clientPeerID, err := utils.ReadBytes(stream)
	if err != nil {
		log.Println("ERROR While reading client peerID from stream:", err)
		err = stream.Reset()
		ignore(err)
		return
	}

	err = utils.WriteBytes(stream, []byte("donePeerID"))
	ignore(err)

	log.Println("DEBUG Received address registration request (addr, peerid):", clientAddr, clientPeerID)
	dhtPeer.dhtAddresses[string(clientAddr)] = string(clientPeerID)
	if dhtPeer.addressAnnounced {
		log.Println("DEBUG Announcing client address", clientAddr, clientPeerID, "...")
		err = dhtPeer.registerAgentAddress(string(clientAddr))
		if err != nil {
			log.Println("ERROR While announcing client address", clientAddr, "to the dht:", err)
			err = stream.Reset()
			ignore(err)
			return
		}
	}
}

func (dhtPeer *DHTPeer) registerAgentAddress(addr string) error {
	addressCID, err := utils.ComputeCID(addr)
	if err != nil {
		return err
	}

	// TOFIX(LR) tune timeout
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	log.Println("DEBUG Announcing address", addr, "to the dht with cid key", addressCID.String())
	err = dhtPeer.dht.Provide(ctx, addressCID, true)
	if err != context.DeadlineExceeded {
		return err
	}
	return nil
}
