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

package dhtclient

import (
	"context"
	"errors"
	"log"
	"math/rand"
	"time"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/multiformats/go-multiaddr"

	kaddht "github.com/libp2p/go-libp2p-kad-dht"
	routedhost "github.com/libp2p/go-libp2p/p2p/host/routed"

	aea "libp2p_node/aea"
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
		log.Println("TRACE", err)
	}
}

// DHTClient A restricted libp2p node for the Agents Communication Network
// It use a `DHTPeer` to communicate with other peers.
type DHTClient struct {
	bootstrapPeers []peer.AddrInfo
	relayPeer      peer.ID
	key            crypto.PrivKey
	publicKey      crypto.PubKey

	dht        *kaddht.IpfsDHT
	routedHost *routedhost.RoutedHost

	myAgentAddress  string
	myAgentReady    func() bool
	processEnvelope func(aea.Envelope) error
}

// New creates a new DHTClient
func New(opts ...Option) (*DHTClient, error) {
	var err error
	dhtClient := &DHTClient{}

	for _, opt := range opts {
		if err := opt(dhtClient); err != nil {
			return nil, err
		}
	}

	/* check correct configuration */

	// private key
	if dhtClient.key == nil {
		return nil, errors.New("private key must be provided")
	}

	// agent address is mandatory
	if dhtClient.myAgentAddress == "" {
		return nil, errors.New("missing agent address")
	}

	// bootsrap peers
	if len(dhtClient.bootstrapPeers) < 1 {
		return nil, errors.New("at least one boostrap peer should be provided")
	}

	// select a relay node randomly from entry peers
	rand.Seed(time.Now().Unix())
	index := rand.Intn(len(dhtClient.bootstrapPeers))
	dhtClient.relayPeer = dhtClient.bootstrapPeers[index].ID
	log.Println("INFO Using as relay:", dhtClient.relayPeer.Pretty())

	/* setup libp2p node */
	ctx := context.Background()

	// libp2p options
	libp2pOpts := []libp2p.Option{
		libp2p.ListenAddrs(),
		libp2p.Identity(dhtClient.key),
		libp2p.DefaultTransports,
		libp2p.DefaultMuxers,
		libp2p.DefaultSecurity,
		libp2p.NATPortMap(),
		libp2p.EnableNATService(),
		libp2p.EnableRelay(),
	}

	// create a basic host
	basicHost, err := libp2p.New(ctx, libp2pOpts...)
	if err != nil {
		return nil, err
	}

	// create the dht
	dhtClient.dht, err = kaddht.New(ctx, basicHost, kaddht.Mode(kaddht.ModeClient))
	if err != nil {
		return nil, err
	}

	// make the routed host
	dhtClient.routedHost = routedhost.Wrap(basicHost, dhtClient.dht)

	// connect to the booststrap nodes
	err = utils.BootstrapConnect(ctx, dhtClient.routedHost, dhtClient.bootstrapPeers)
	if err != nil {
		return nil, err
	}

	// bootstrap the host
	err = dhtClient.dht.Bootstrap(ctx)
	if err != nil {
		return nil, err
	}

	// register my address to relay peer
	err = dhtClient.registerAgentAddress()
	if err != nil {
		return nil, err
	}

	/* setup DHTClient message handlers */

	// aea address lookup
	log.Println("DEBUG Setting /aea-address/0.1.0 stream...")
	dhtClient.routedHost.SetStreamHandler("/aea-address/0.1.0",
		dhtClient.handleAeaAddressStream)

	// incoming envelopes stream
	log.Println("DEBUG Setting /aea/0.1.0 stream...")
	dhtClient.routedHost.SetStreamHandler("/aea/0.1.0",
		dhtClient.handleAeaEnvelopeStream)

	return dhtClient, nil
}

// RouteEnvelope to its destination
func (dhtClient *DHTClient) RouteEnvelope(envel aea.Envelope) error {
	target := envel.To

	if target == dhtClient.myAgentAddress {
		log.Println("DEBUG route - envelope destinated to my local agent...")
		for !dhtClient.myAgentReady() {
			log.Println("DEBUG route agent not ready yet, sleeping for some time ...")
			time.Sleep(time.Duration(100) * time.Millisecond)
		}
		if dhtClient.processEnvelope != nil {
			err := dhtClient.processEnvelope(envel)
			if err != nil {
				return err
			}
		} else {
			log.Println("WARN route ProcessEnvelope not set, ignoring envelope", envel)
			return nil
		}
	}

	log.Println("DEBUG route - looking up peer ID for agent Address", target)
	// client can get addresses only through bootstrap peer
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	stream, err := dhtClient.routedHost.NewStream(ctx, dhtClient.relayPeer, "/aea-address/0.1.0")
	if err != nil {
		log.Println("ERROR route - couldn't open stream to relay", dhtClient.relayPeer.Pretty())
		return err
	}

	log.Println("DEBUG route - requesting peer ID from relay...")

	err = utils.WriteBytes(stream, []byte(target))
	if err != nil {
		log.Println("ERROR route - While sending address to relay:", err)
		return errors.New("ERROR route - While sending address to relay:" + err.Error())
	}

	msg, err := utils.ReadString(stream)
	if err != nil {
		log.Println("ERROR route - While reading target peer id from relay:", err)
		return errors.New("ERROR route - While reading target peer id from relay:" + err.Error())
	}
	stream.Close()

	peerID, err := peer.Decode(msg)
	if err != nil {
		log.Println("CRITICAL route - couldn't get peer ID from message", msg, ":", err)
		return errors.New("CRITICAL route - couldn't get peer ID from message:" + err.Error())
	}

	log.Println("DEBUG route - got peer ID for agent Address", target, ":", peerID.Pretty())

	multiAddr := "/p2p/" + dhtClient.relayPeer.Pretty() + "/p2p-circuit/p2p/" + peerID.Pretty()
	relayMultiaddr, err := multiaddr.NewMultiaddr(multiAddr)
	if err != nil {
		log.Println("ERROR route - while creating relay multiaddress ", multiAddr, err)
		return err
	}
	peerRelayInfo := peer.AddrInfo{
		ID:    peerID,
		Addrs: []multiaddr.Multiaddr{relayMultiaddr},
	}

	log.Println("DEBUG route - connecting to target through relay ", relayMultiaddr)

	if err = dhtClient.routedHost.Connect(context.Background(), peerRelayInfo); err != nil {
		log.Println("ERROR route - couldn't connect to target", peerID)
		return err
	}

	log.Println("DEBUG route - opening stream to target ", peerID)
	ctx, cancel = context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	stream, err = dhtClient.routedHost.NewStream(ctx, peerID, "/aea/0.1.0")
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

func (dhtClient *DHTClient) handleAeaEnvelopeStream(stream network.Stream) {
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

	if envel.To == dhtClient.myAgentAddress && dhtClient.processEnvelope != nil {
		err = dhtClient.processEnvelope(*envel)
		if err != nil {
			log.Println("ERROR While processing envelope by agent:", err)
		}
	} else {
		log.Println("WARN ignored envelope", *envel)
	}
}

func (dhtClient *DHTClient) handleAeaAddressStream(stream network.Stream) {
	log.Println("DEBUG Got a new aea address stream")

	reqAddress, err := utils.ReadString(stream)
	if err != nil {
		log.Println("ERROR While reading Address from stream:", err)
		err = stream.Reset()
		ignore(err)
		return
	}

	log.Println("DEBUG Received query for addr:", reqAddress)
	if reqAddress != dhtClient.myAgentAddress {
		log.Println("ERROR requested address different from advertised one",
			reqAddress, dhtClient.myAgentAddress)
		stream.Close()
	} else {
		err = utils.WriteBytes(stream, []byte(dhtClient.routedHost.ID().Pretty()))
		if err != nil {
			log.Println("ERROR While sending peerID to peer:", err)
		}
	}

}

func (dhtClient *DHTClient) registerAgentAddress() error {
	log.Println("DEBUG opening stream aea-register to bootsrap peer ", dhtClient.relayPeer)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	stream, err := dhtClient.routedHost.NewStream(ctx, dhtClient.relayPeer, "/aea-register/0.1.0")
	if err != nil {
		log.Println("ERROR timeout, couldn't open stream to target",
			dhtClient.relayPeer, ":", err)
		return err
	}

	log.Println("DEBUG sending addr and peerID to bootstrap peer",
		dhtClient.myAgentAddress, dhtClient.routedHost.ID().Pretty())
	err = utils.WriteBytes(stream, []byte(dhtClient.myAgentAddress))
	if err != nil {
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}
	_, _ = utils.ReadBytes(stream)
	err = utils.WriteBytes(stream, []byte(dhtClient.routedHost.ID().Pretty()))
	if err != nil {
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}

	_, _ = utils.ReadBytes(stream)
	stream.Close()
	return nil

}

//ProcessEnvelope register a callback function
func (dhtClient *DHTClient) ProcessEnvelope(fn func(aea.Envelope) error) {
	dhtClient.processEnvelope = fn
}
