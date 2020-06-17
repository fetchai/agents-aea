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

package main

import (
	"bufio"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"log"
	"net"
	"strconv"
	"sync"
	"time"

	"github.com/ipfs/go-cid"
	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/host"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/libp2p/go-libp2p-core/peerstore"
	"github.com/multiformats/go-multiaddr"
	"github.com/multiformats/go-multihash"

	circuit "github.com/libp2p/go-libp2p-circuit"
	kaddht "github.com/libp2p/go-libp2p-kad-dht"
	routedhost "github.com/libp2p/go-libp2p/p2p/host/routed"

	proto "github.com/golang/protobuf/proto"

	aea "libp2p_node/aea"
)

// panics if err is not nil
func check(err error) {
	if err != nil {
		panic(err)
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

// NewDHTPeer creates a new DHTPeer
func NewDHTPeer(opts ...DHTPeerOption) (*DHTPeer, error) {
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
		err = bootstrapConnect(ctx, dhtPeer.routedHost, dhtPeer.bootstrapPeers)
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
		s.Write([]byte("/aea-notif/0.1.0"))
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
	buf, err := readBytesConn(conn)
	if err != nil {
		log.Println("ERROR while receiving agent's Address:", err)
		return
	}
	err = writeBytesConn(conn, []byte("DONE"))

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
		envel, err := readEnvelopeConn(conn)
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
		go dhtPeer.RouteEnvelope(*envel)
	}

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
		return writeEnvelopeConn(conn, envel)
	} else {
		var peerID peer.ID
		var err error
		if sPeerID, exists := dhtPeer.dhtAddresses[target]; exists {
			log.Println("DEBUG route - destination", target, "is a relay client")
			peerID, err = peer.IDB58Decode(sPeerID)
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
		ctx, _ := context.WithTimeout(context.Background(), 30*time.Second)
		stream, err := dhtPeer.routedHost.NewStream(ctx, peerID, "/aea/0.1.0")
		if err != nil {
			log.Println("ERROR route - timeout, couldn't open stream to target ", peerID)
			return err
		}

		log.Println("DEBUG route - sending envelope to target...")
		err = writeEnvelope(envel, stream)
		if err != nil {
			stream.Reset()
		} else {
			stream.Close()
		}

		return err
	}

	return nil
}

func (dhtPeer *DHTPeer) lookupAddressDHT(address string) (peer.ID, error) {
	addressCID, err := computeCID(address)
	if err != nil {
		return "", err
	}

	log.Println("INFO Querying for providers for cid", addressCID.String(),
		" of address", address, "...")
	ctx, _ := context.WithTimeout(context.Background(), 120*time.Second)
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

	err = writeBytes(s, []byte(address))
	if err != nil {
		return "", errors.New("ERROR while sending address to peer:" + err.Error())
	}

	msg, err := readString(s)
	if err != nil {
		return "", errors.New("ERROR while reading target peer id from peer:" + err.Error())
	}
	s.Close()

	peerid, err := peer.IDB58Decode(msg)
	if err != nil {
		return "", errors.New("CRITICAL couldn't get peer ID from message:" + err.Error())
	}

	return peerid, nil
}

func (dhtPeer *DHTPeer) handleAeaEnvelopeStream(stream network.Stream) {
	log.Println("DEBUG Got a new aea envelope stream")

	envel, err := readEnvelope(stream)
	if err != nil {
		log.Println("ERROR While reading envelope from stream:", err)
		stream.Reset()
		return
	}
	stream.Close()

	log.Println("DEBUG Received envelope from peer:", envel)

	// check if destination is a tcp client
	if conn, exists := dhtPeer.tcpAddresses[envel.To]; exists {
		err = writeEnvelopeConn(conn, *envel)
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

	reqAddress, err := readString(stream)
	if err != nil {
		log.Println("ERROR While reading Address from stream:", err)
		stream.Reset()
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
	err = writeBytes(stream, []byte(sPeerID))
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

	clientAddr, err := readBytes(stream)
	if err != nil {
		log.Println("ERROR While reading client Address from stream:", err)
		stream.Reset()
		return
	}

	err = writeBytes(stream, []byte("doneAddress"))

	clientPeerID, err := readBytes(stream)
	if err != nil {
		log.Println("ERROR While reading client peerID from stream:", err)
		stream.Reset()
		return
	}

	err = writeBytes(stream, []byte("donePeerID"))

	log.Println("DEBUG Received address registration request (addr, peerid):", clientAddr, clientPeerID)
	dhtPeer.dhtAddresses[string(clientAddr)] = string(clientPeerID)
	if dhtPeer.addressAnnounced {
		log.Println("DEBUG Announcing client address", clientAddr, clientPeerID, "...")
		err = dhtPeer.registerAgentAddress(string(clientAddr))
		if err != nil {
			log.Println("ERROR While announcing client address", clientAddr, "to the dht:", err)
			stream.Reset()
			return
		}
	}
}

func (dhtPeer *DHTPeer) registerAgentAddress(addr string) error {
	addressCID, err := computeCID(addr)
	if err != nil {
		return err
	}

	// TOFIX(LR) tune timeout
	ctx, _ := context.WithTimeout(context.Background(), 3*time.Second)

	log.Println("DEBUG Announcing address", addr, "to the dht with cid key", addressCID.String())
	err = dhtPeer.dht.Provide(ctx, addressCID, true)
	if err != context.DeadlineExceeded {
		return err
	}
	return nil
}

/*
	Helpers
*/

// This code is borrowed from the go-ipfs bootstrap process
func bootstrapConnect(ctx context.Context, ph host.Host, peers []peer.AddrInfo) error {
	if len(peers) < 1 {
		return errors.New("not enough bootstrap peers")
	}

	errs := make(chan error, len(peers))
	var wg sync.WaitGroup
	for _, p := range peers {

		// performed asynchronously because when performed synchronously, if
		// one `Connect` call hangs, subsequent calls are more likely to
		// fail/abort due to an expiring context.
		// Also, performed asynchronously for dial speed.

		wg.Add(1)
		go func(p peer.AddrInfo) {
			defer wg.Done()
			defer log.Println(ctx, "bootstrapDial", ph.ID(), p.ID)
			log.Printf("%s bootstrapping to %s", ph.ID(), p.ID)

			ph.Peerstore().AddAddrs(p.ID, p.Addrs, peerstore.PermanentAddrTTL)
			if err := ph.Connect(ctx, p); err != nil {
				log.Println(ctx, "bootstrapDialFailed", p.ID)
				log.Printf("failed to bootstrap with %v: %s", p.ID, err)
				errs <- err
				return
			}

			log.Println(ctx, "bootstrapDialSuccess", p.ID)
			log.Printf("bootstrapped with %v", p.ID)
		}(p)
	}
	wg.Wait()

	// our failure condition is when no connection attempt succeeded.
	// So drain the errs channel, counting the results.
	close(errs)
	count := 0
	var err error
	for err = range errs {
		if err != nil {
			count++
		}
	}
	if count == len(peers) {
		return fmt.Errorf("failed to bootstrap. %s", err)
	}
	return nil
}

/*
   Utils
*/

func writeBytesConn(conn net.Conn, data []byte) error {
	size := uint32(len(data))
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, size)
	_, err := conn.Write(buf)
	if err != nil {
		return err
	}
	_, err = conn.Write(data)
	return err
}

func readBytesConn(conn net.Conn) ([]byte, error) {
	buf := make([]byte, 4)
	_, err := conn.Read(buf)
	if err != nil {
		return buf, err
	}
	size := binary.BigEndian.Uint32(buf)

	buf = make([]byte, size)
	_, err = conn.Read(buf)
	return buf, err
}

func writeEnvelopeConn(conn net.Conn, envelope aea.Envelope) error {
	data, err := proto.Marshal(&envelope)
	if err != nil {
		return err
	}
	return writeBytesConn(conn, data)
}

func readEnvelopeConn(conn net.Conn) (*aea.Envelope, error) {
	envelope := &aea.Envelope{}
	data, err := readBytesConn(conn)
	if err != nil {
		return envelope, err
	}
	err = proto.Unmarshal(data, envelope)
	return envelope, err
}

func aeaAddressCID(addr string) (cid.Cid, error) {
	pref := cid.Prefix{
		Version:  0,
		Codec:    cid.Raw,
		MhType:   multihash.SHA2_256,
		MhLength: -1, // default length
	}

	// And then feed it some data
	c, err := pref.Sum([]byte(addr))
	if err != nil {
		return cid.Cid{}, err
	}

	return c, nil
}

func computeCID(addr string) (cid.Cid, error) {
	pref := cid.Prefix{
		Version:  0,
		Codec:    cid.Raw,
		MhType:   multihash.SHA2_256,
		MhLength: -1, // default length
	}

	// And then feed it some data
	c, err := pref.Sum([]byte(addr))
	if err != nil {
		return cid.Cid{}, err
	}

	return c, nil
}

func readBytes(s network.Stream) ([]byte, error) {
	rstream := bufio.NewReader(s)

	buf := make([]byte, 4)
	_, err := io.ReadFull(rstream, buf)
	if err != nil {
		log.Println("ERROR while receiving size:", err)
		return buf, err
	}

	size := binary.BigEndian.Uint32(buf)
	log.Println("DEBUG expecting", size)

	buf = make([]byte, size)
	_, err = io.ReadFull(rstream, buf)

	return buf, err
}

func writeBytes(s network.Stream, data []byte) error {
	wstream := bufio.NewWriter(s)

	size := uint32(len(data))
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, size)

	_, err := wstream.Write(buf)
	if err != nil {
		log.Println("ERROR while sending size:", err)
		return err
	}

	log.Println("DEBUG writing", len(data))
	_, err = wstream.Write(data)
	wstream.Flush()
	return err
}

func readString(s network.Stream) (string, error) {
	data, err := readBytes(s)
	return string(data), err
}

func writeEnvelope(envel aea.Envelope, s network.Stream) error {
	wstream := bufio.NewWriter(s)
	data, err := proto.Marshal(&envel)
	if err != nil {
		return err
	}
	size := uint32(len(data))

	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, size)
	//log.Println("DEBUG writing size:", size, buf)
	_, err = wstream.Write(buf)
	if err != nil {
		return err
	}

	//log.Println("DEBUG writing data:", data)
	_, err = wstream.Write(data)
	if err != nil {
		return err
	}

	wstream.Flush()
	return nil
}

func readEnvelope(s network.Stream) (*aea.Envelope, error) {
	envel := &aea.Envelope{}
	rstream := bufio.NewReader(s)

	buf := make([]byte, 4)
	_, err := io.ReadFull(rstream, buf)

	if err != nil {
		log.Println("ERROR while reading size")
		return envel, err
	}

	size := binary.BigEndian.Uint32(buf)
	fmt.Println("DEBUG received size:", size, buf)
	buf = make([]byte, size)
	_, err = io.ReadFull(rstream, buf)
	if err != nil {
		log.Println("ERROR while reading data")
		return envel, err
	}

	err = proto.Unmarshal(buf, envel)
	return envel, err
}
