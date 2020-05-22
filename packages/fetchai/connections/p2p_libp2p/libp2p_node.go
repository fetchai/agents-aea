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
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"log"
	"os"
	"os/signal"
	"sync"
	"time"

	"github.com/libp2p/go-libp2p"
	circuit "github.com/libp2p/go-libp2p-circuit"
	"github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/host"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/libp2p/go-libp2p-core/peerstore"
	basichost "github.com/libp2p/go-libp2p/p2p/host/basic"

	//ds "github.com/ipfs/go-datastore"
	//dsync "github.com/ipfs/go-datastore/sync"
	dht "github.com/libp2p/go-libp2p-kad-dht"
	rhost "github.com/libp2p/go-libp2p/p2p/host/routed"
	"github.com/multiformats/go-multiaddr"

	cid "github.com/ipfs/go-cid"
	mh "github.com/multiformats/go-multihash"

	aea "libp2p_node/aea"

	btcec "github.com/btcsuite/btcd/btcec"

	proto "github.com/golang/protobuf/proto"
)

// panics if err is not nil
func check(err error) {
	if err != nil {
		panic(err)
	}
}

// TOFIX(LR) temp, just the time to refactor
var (
	cfg_client        = false
	cfg_relays        = []peer.ID{}
	cfg_addresses_map = map[string]string{}
)

func main() {

	var err error

	// Initialize connection to aea
	agent := aea.AeaApi{}
	check(agent.Init())
	log.Println("successfully initialised API to AEA!")

	// Get node configuration

	// aea agent address
	aeaAddr := agent.AeaAddress()

	// node address (ip and port)
	nodeHost, nodePort := agent.Address()

	// node public address, if set
	nodeHostPublic, nodePortPublic := agent.PublicAddress()

	// node private key
	key := agent.PrivateKey()
	prvKey, pubKey, err := KeyPairFromFetchAIKey(key)
	check(err)

	// entry peers
	entryPeers := agent.EntryPeers()
	bootstrapPeers, err := GetPeersAddrInfo(entryPeers)
	check(err)
	log.Println(bootstrapPeers)

	// Configure node's multiaddr
	nodeMultiaddr, _ := multiaddr.NewMultiaddr(fmt.Sprintf("/ip4/%s/tcp/%d", nodeHost, nodePort))

	// Run as a peer or just as a client
	// TOFIX(LR) global vars, will be refatoring very soon
	if nodePortPublic == 0 {
		// if no external address is provided, run as a client
		cfg_client = true

		if len(bootstrapPeers) <= 0 {
			check(errors.New("client should be provided with bootstrap peers"))
		}
		for _, addr := range bootstrapPeers {
			cfg_relays = append(cfg_relays, addr.ID)
		}
	} else {
		cfg_client = false
	}

	// Make a host that listens on the given multiaddress
	routedHost, hdht, err := setupRoutedHost(nodeMultiaddr, prvKey, bootstrapPeers, aeaAddr, nodeHostPublic, nodePortPublic)
	log.Println("successfully created libp2p node!")

	if !cfg_client {
		// Allow clients to register their agents addresses
		log.Println("DEBUG Setting /aea-register/0.1.0 stream...")
		annouced := false // TOFIX(LR) hack, need to define own NetworkManager otherwise
		routedHost.SetStreamHandler("/aea-register/0.1.0", func(s network.Stream) {
			handleAeaRegisterStream(hdht, s, &annouced)
		})

		// For new peers in case I am the genesis peer, please notify me so that I can register my address and my clients' ones as well
		// TOFIX(LR) hack, as it seems that a peer cannot Provide when it is alone in the DHT
		routedHost.SetStreamHandler("/aea-notif/0.1.0", func(s network.Stream) {
			handleAeaNotifStream(s, hdht, aeaAddr, &annouced)
		})

		// Notify bootstrap peer if any
		for _, bpeer := range bootstrapPeers {
			ctx := context.Background()
			s, err := routedHost.NewStream(ctx, bpeer.ID, "/aea-notif/0.1.0")
			if err != nil {
				log.Println("ERROR failed to notify bootstrap peer:" + err.Error())
				check(err)
			}
			s.Write([]byte("/aea-notif/0.1.0"))
			s.Close()
		}

		// if I am joining an existing network, annouce my address
		if len(bootstrapPeers) > 0 {
			// TOFIX(LR) assumes that agent key and node key are the same
			err = registerAgentAddress(hdht, aeaAddr)
			check(err)
			annouced = true
		}

	}

	if cfg_client {
		// ask the bootstrap peer to annouce my address for myself
		// register my address to bootstrap peer
		// TOFIX(LR) only to one bootsrap peer
		err = registerAgentAddressClient(routedHost, aeaAddr, bootstrapPeers[0].ID)
		check(err)
	}

	////	// Publish (agent address, node public key) pair to the dht
	////
	////
	////	if len(bootstrapPeers) > 0 && false {
	////		// TOFIX(LR) assumes that agent key and node key are the same
	////		err = registerAgentAddress(hdht, aeaAddr)
	////		check(err)
	////		annouced = true
	////	}

	// Set a stream handler for aea addresses lookup
	log.Println("DEBUG Setting /aea-address/0.1.0 stream...")
	pubKeyBytes, err := crypto.MarshalPublicKey(pubKey)
	check(err)
	routedHost.SetStreamHandler("/aea-address/0.1.0", func(s network.Stream) {
		handleAeaAddressStream(routedHost, hdht, s, aeaAddr, pubKeyBytes)
	})

	// Set a stream handler for envelopes
	log.Println("DEBUG Setting /aea/0.1.0 stream...")
	routedHost.SetStreamHandler("/aea/0.1.0", func(s network.Stream) {
		handleAeaStream(s, agent)
	})

	// Connect to the agent
	check(agent.Connect())
	log.Println("successfully connected to AEA!")

	////// Receive envelopes from agent and forward to peer
	////	var bootstrapID peer.ID
	////	if nodePortPublic == 0 {
	////		bootstrapID = bootstrapPeers[0].ID
	////	}
	go func() {
		for envel := range agent.Queue() {
			log.Println("INFO Received envelope from agent:", envel)
			go route(*envel, routedHost, hdht)
		}
	}()

	// Wait until Ctrl+C or a termination call is done.
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c

	log.Println("node stopped")
}

func aeaAddressCID(addr string) (cid.Cid, error) {
	pref := cid.Prefix{
		Version:  0,
		Codec:    cid.Raw,
		MhType:   mh.SHA2_256,
		MhLength: -1, // default length
	}

	// And then feed it some data
	c, err := pref.Sum([]byte(addr))
	if err != nil {
		return cid.Cid{}, err
	}

	return c, nil
}

/*

  Aea stream queries and requests

*/

func route(envel aea.Envelope, routedHost host.Host, hdht *dht.IpfsDHT) error {
	target := envel.To

	//// TOFIX
	//envel.Sender = routedHost.ID().Pretty()

	// Get peerID corresponding to aea Address
	var err error
	var peerid peer.ID

	log.Println("DEBUG route - looking up peer ID for agent Address", target)
	if cfg_client {
		// client can get addresses only through bootstrap peer
		ctx, _ := context.WithTimeout(context.Background(), 10*time.Second)
		s, err := routedHost.NewStream(ctx, cfg_relays[0], "/aea-address/0.1.0")
		if err != nil {
			log.Println("ERROR route - couldn't open stream to relay", cfg_relays[0].Pretty())
			return err
		}

		log.Println("DEBUG route - requesting peer ID registred with addr from relay...")

		err = writeBytes(s, []byte(target))
		if err != nil {
			log.Println("ERROR route - While sending address to relay:", err)
			return errors.New("ERROR route - While sending address to relay:" + err.Error())
		}

		msg, err := readString(s)
		if err != nil {
			log.Println("ERROR route - While reading target peer id from relay:", err)
			return errors.New("ERROR route - While reading target peer id from relay:" + err.Error())
		}
		s.Close()

		peerid, err = peer.IDB58Decode(msg)
		if err != nil {
			log.Println("CRITICAL route - couldn't get peer ID from message:", err)
			return errors.New("CRITICAL route - couldn't get peer ID from message:" + err.Error())
		}

	}

	if !cfg_client {
		// peers first check if the address is available locally, otherwise they query the DHT
		// first check if I have the reqAddress locally
		cpeerid, exists := cfg_addresses_map[target]
		if exists {
			log.Println("DEBUG route - found address on my local lookup table")
			peerid, err = peer.IDB58Decode(cpeerid)
			if err != nil {
				log.Println("CRITICAL route - couldn't get peer ID from local addresses map:", err)
				return err
			}
		} else {
			log.Println("DEBUG route - did NOT found address on my local lookup table, looking for it on the DHT...")
			peerid, err = lookupAddress(routedHost, hdht, target)
			if err != nil {
				log.Println("ERROR route - while looking up address on the DHT:", err)
				return err
			}
		}

	}

	//peerid, err := peer.IDB58Decode(target)
	log.Println("DEBUG route - got peer ID for agent Address", target, ":", peerid.Pretty())

	if cfg_client {
		// TOFIX(LR) using only the first bootstrap peer
		relayID := cfg_relays[0]
		relayaddr, err := multiaddr.NewMultiaddr("/p2p/" + relayID.Pretty() + "/p2p-circuit/p2p/" + peerid.Pretty())
		if err != nil {
			log.Println("ERROR route - while creating relay multiaddress", peerid)
			return err
		}

		peerRelayInfo := peer.AddrInfo{
			ID:    peerid,
			Addrs: []multiaddr.Multiaddr{relayaddr},
		}

		log.Println("DEBUG route - connecting to taregt through relay:", relayaddr)
		if err = routedHost.Connect(context.Background(), peerRelayInfo); err != nil {
			log.Println("ERROR route - couldn't connect to target", peerid)
			return err
		}

	}
	//
	log.Println("DEBUG route - opening stream to target ", peerid)
	//ctx := context.Background()
	ctx, _ := context.WithTimeout(context.Background(), 30*time.Second)
	s, err := routedHost.NewStream(ctx, peerid, "/aea/0.1.0")
	if err != nil {
		log.Println("ERROR route - timeout, couldn't open stream to target ", peerid)
		return err
	}

	//
	log.Println("DEBUG route - sending envelope to target...")
	err = writeEnvelope(envel, s)
	if err != nil {
		s.Reset()
	} else {
		s.Close()
	}

	return err
}

func lookupAddress(routedHost host.Host, hdht *dht.IpfsDHT, address string) (peer.ID, error) {
	// Get peerID corresponding to target
	addressCID, err := computeCID(address)
	if err != nil {
		return "", err
	}

	// TOFIX(LR) use select with timeout
	log.Println("Querying for providers for cid", addressCID.String(), " of address", address, "...")
	ctx, _ := context.WithTimeout(context.Background(), 120*time.Second)
	// TOFIX(LR) how does FindProviderAsync manages timeouts with channels?
	providers := hdht.FindProvidersAsync(ctx, addressCID, 1)
	start := time.Now()
	provider := <-providers
	elapsed := time.Since(start)
	log.Println("DEBUG found provider after", elapsed)

	// Add peer to host PeerStore - the provider should be the holder of the address
	routedHost.Peerstore().AddAddrs(provider.ID, provider.Addrs, peerstore.PermanentAddrTTL)

	log.Println("DEBUG opening stream to the address provider", provider)
	ctx = context.Background()
	s, err := routedHost.NewStream(ctx, provider.ID, "/aea-address/0.1.0")
	if err != nil {
		return "", err
	}

	// TOFIX(LR) getting peerID instead of public key
	/*
			log.Println("DEBUG reading peer public key from provider for addr", address)

			err = writeBytes(s, []byte(address))
			if err != nil {
				return "", errors.New("ERROR While sending address to peer:" + err.Error())
			}

			pubKeyBytes, err := readBytes(s)
			if err != nil {
				return "", errors.New("ERROR While reading target Public key from peer:" + err.Error())
			}
			s.Close()

		pubKey, err := crypto.UnmarshalPublicKey(pubKeyBytes)
		if err != nil {
			return "", errors.New("ERROR While unmarshaling target Public key:" + err.Error())
		}

		peerid, err := peer.IDFromPublicKey(pubKey)
		if err != nil {
			return "", errors.New("CRITICAL couldn't get peer ID from publick key:" + err.Error())
		}
	*/

	log.Println("DEBUG reading peer ID from provider for addr", address)

	err = writeBytes(s, []byte(address))
	if err != nil {
		return "", errors.New("ERROR While sending address to peer:" + err.Error())
	}

	msg, err := readString(s)
	if err != nil {
		return "", errors.New("ERROR While reading target peer id from peer:" + err.Error())
	}
	s.Close()

	peerid, err := peer.IDB58Decode(msg)
	if err != nil {
		return "", errors.New("CRITICAL couldn't get peer ID from message:" + err.Error())
	}

	return peerid, nil
}

func registerAgentAddress(hdht *dht.IpfsDHT, address string) error {
	addressCID, err := computeCID(address)
	if err != nil {
		return err
	}

	// TOFIX(LR) tune timeout
	ctx, _ := context.WithTimeout(context.Background(), 3*time.Second)

	log.Println("DEBUG Annoucing address", address, "to the dht with cid key", addressCID.String())
	err = hdht.Provide(ctx, addressCID, true)
	if err != context.DeadlineExceeded {
		return err
	} else {
		return nil
	}

}

func registerAgentAddressClient(routedHost host.Host, aeaAddr string, bootstrapPeer peer.ID) error {
	log.Println("DEBUG opening stream aea-register to bootsrap peer ", bootstrapPeer)
	//ctx := context.Background()
	ctx, _ := context.WithTimeout(context.Background(), 30*time.Second)
	s, err := routedHost.NewStream(ctx, bootstrapPeer, "/aea-register/0.1.0")
	if err != nil {
		log.Println("ERROR timeout, couldn't open stream to target ", bootstrapPeer)
		return err
	}

	//
	log.Println("DEBUG sending addr and peerID to bootstrap peer...")
	err = writeBytes(s, []byte(aeaAddr))
	if err != nil {
		s.Reset()
		return err
	}
	_, _ = readBytes(s)
	err = writeBytes(s, []byte(routedHost.ID().Pretty()))
	if err != nil {
		s.Reset()
		return err
	}

	_, _ = readBytes(s)
	s.Close()
	return nil
}

func computeCID(addr string) (cid.Cid, error) {
	pref := cid.Prefix{
		Version:  0,
		Codec:    cid.Raw,
		MhType:   mh.SHA2_256,
		MhLength: -1, // default length
	}

	// And then feed it some data
	c, err := pref.Sum([]byte(addr))
	if err != nil {
		return cid.Cid{}, err
	}

	return c, nil
}

func handleAeaAddressStream(routedHost host.Host, hdht *dht.IpfsDHT, s network.Stream, address string, pubKey []byte) {
	log.Println("DEBUG Got a new aea address stream")
	// TOFIX(LR) not needed, assuming this node is the only one advertising its own addr
	reqAddress, err := readString(s)
	if err != nil {
		log.Println("ERROR While reading Address from stream:", err)
		s.Reset()
		return
	}

	log.Println("DEBUG Received query for addr:", reqAddress)
	if reqAddress != address {
		if cfg_client {
			log.Println("ERROR requested address different from advertised one", reqAddress, address)
			s.Close()
			return
		} else {
			// first check if I have the reqAddress locally
			cpeerid, exists := cfg_addresses_map[reqAddress]
			if exists {
				log.Println("DEBUG found address on my local lookup table")
				err = writeBytes(s, []byte(cpeerid))
				if err != nil {
					log.Println("ERROR While sending peerID to peer:", err)
				}
				return
			} else {
				log.Println("DEBUG did NOT found address on my local lookup table, looking for it on the DHT...")
				rpeerid, err := lookupAddress(routedHost, hdht, reqAddress)
				if err != nil {
					log.Println("ERROR while looking up address on the DHT:", err)
					return
				}

				log.Println("DEBUG found peerID of address from DHT:", rpeerid)
				err = writeBytes(s, []byte(rpeerid.Pretty()))
				if err != nil {
					log.Println("ERROR While sending peerID to peer:", err)

				}
				return
			}

			// request it from DHT
		}
	} else {
		// TOFIX(LR) sending peerID instead of public key
		/*
			err = writeBytes(s, pubKey)
			if err != nil {
				log.Println("ERROR While sending public key to peer:", err)
			}
		*/

		key, err := crypto.UnmarshalPublicKey(pubKey)
		if err != nil {
			log.Println("ERROR While preparing peerID to be sent to peer (TOFIX):", err)
		}

		peerid, err := peer.IDFromPublicKey(key)

		err = writeBytes(s, []byte(peerid.Pretty()))
		if err != nil {
			log.Println("ERROR While sending peerID to peer:", err)
		}
	}

}

func handleAeaRegisterStream(hdht *dht.IpfsDHT, s network.Stream, annouced *bool) {
	log.Println("DEBUG Got a new aea register stream")
	client_addr, err := readBytes(s)
	if err != nil {
		log.Println("ERROR While reading client Address from stream:", err)
		s.Reset()
		return
	}

	err = writeBytes(s, []byte("doneAddress"))

	client_peerid, err := readBytes(s)
	if err != nil {
		log.Println("ERROR While reading client peerID from stream:", err)
		s.Reset()
		return
	}

	err = writeBytes(s, []byte("donePeerID"))

	log.Println("DEBUG Received address regitration request (addr, peerid):", client_addr, client_peerid)
	cfg_addresses_map[string(client_addr)] = string(client_peerid)
	if *annouced {
		log.Println("DEBUG Annoucing client address", client_addr, client_peerid, "...")
		err = registerAgentAddress(hdht, string(client_addr))
		if err != nil {
			log.Println("ERROR While annoucing client address to the dht:", err)
			s.Reset()
			return
		}
	}

}

func handleAeaNotifStream(s network.Stream, hdht *dht.IpfsDHT, aeaAddr string, annouced *bool) {
	log.Println("DEBUG Got a new notif stream")
	if !*annouced {
		err := registerAgentAddress(hdht, aeaAddr)
		if err != nil {
			log.Println("ERROR while annoucing my address to dht:" + err.Error())
			return
		}
		// annouce clients addresses
		for a, _ := range cfg_addresses_map {
			err = registerAgentAddress(hdht, a)
		}
		*annouced = true
	}
	s.Close()
}

func handleAeaStream(s network.Stream, agent aea.AeaApi) {
	log.Println("DEBUG Got a new stream")
	env, err := readEnvelope(s)
	if err != nil {
		log.Println("ERROR While reading envelope from stream:", err)
		s.Reset()
		return
	} else {
		s.Close()
	}

	log.Println("DEBUG Received envelope from peer:", env)
	err = agent.Put(env)
	if err != nil {
		log.Println("ERROR While sending envelope to agent:", err)
	}
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

/*

  Routed Host setup - Host with DHT

*/

func setupRoutedHost(
	ma multiaddr.Multiaddr, key crypto.PrivKey, bootstrapPeers []peer.AddrInfo, aeaAddr string,
	nodeHostPublic string, nodePortPublic uint16) (host.Host, *dht.IpfsDHT, error) {

	// Construct a datastore (needed by the DHT). This is just a simple, in-memory thread-safe datastore.
	// TOFIX(LR) doesn't seem to be necessary
	//dstore := dsync.MutexWrap(ds.NewMapDatastore())

	// set external ip address
	var addressFactory basichost.AddrsFactory
	//if nodePortPublic != 0 {
	if !cfg_client {

		publicMultiaddr, _ := multiaddr.NewMultiaddr(fmt.Sprintf("/dns4/%s/tcp/%d", nodeHostPublic, nodePortPublic))
		addressFactory = func(addrs []multiaddr.Multiaddr) []multiaddr.Multiaddr {
			return []multiaddr.Multiaddr{publicMultiaddr}
		}
	} else {
		addressFactory = func(addrs []multiaddr.Multiaddr) []multiaddr.Multiaddr {
			return addrs
		}
	}

	ctx := context.Background()

	opts := []libp2p.Option{
		//libp2p.ListenAddrs(ma),
		libp2p.AddrsFactory(addressFactory),
		libp2p.Identity(key),
		libp2p.DefaultTransports,
		libp2p.DefaultMuxers,
		libp2p.DefaultSecurity,
		libp2p.NATPortMap(), // TOFIX(LR) doesn't seem to have an impact
		libp2p.EnableNATService(),
		//libp2p.EnableAutoNAT()(), // TOFIX deprecated? https://github.com/libp2p/go-libp2p-autonat/blob/master/test/autonat_test.go
	}

	if !cfg_client {
		//opts = append(opts, libp2p.EnableRelay(circuit.OptActive)) // TOFIX(LR) does it allow for multihops relays? or OptHop is already enough?
		opts = append(opts, libp2p.EnableRelay(circuit.OptHop))
		opts = append(opts, libp2p.ListenAddrs(ma))
	} else {
		opts = append(opts, libp2p.EnableRelay())
		opts = append(opts, libp2p.ListenAddrs())
		log.Println("DEBUG I shouldn't have any addres")
	}

	basicHost, err := libp2p.New(ctx, opts...)
	if err != nil {
		return nil, nil, err
	}

	// Make the DHT
	// TOFIX(LR) not sure if explicitly passing a dstore is needed
	//ndht := dht.NewDHT(ctx, basicHost, dstore)
	var ndht *dht.IpfsDHT
	if !cfg_client {
		ndht, err = dht.New(ctx, basicHost, dht.Mode(dht.ModeServer))
		if err != nil {
			return nil, nil, err
		}
	} else {
		ndht, err = dht.New(ctx, basicHost, dht.Mode(dht.ModeClient))
		if err != nil {
			return nil, nil, err
		}

	}

	// Make the routed host
	routedHost := rhost.Wrap(basicHost, ndht)

	// connect to the booststrap nodes
	// For both peers and clients
	if len(bootstrapPeers) > 0 {
		err = bootstrapConnect(ctx, routedHost, bootstrapPeers)
		if err != nil {
			return nil, nil, err
		}
	}

	// Bootstrap the host
	// TOFIX(LR) doesn't seems to be mandatory for enabling routing
	err = ndht.Bootstrap(ctx)
	if err != nil {
		return nil, nil, err
	}

	// Build host multiaddress
	hostAddr, _ := multiaddr.NewMultiaddr(fmt.Sprintf("/p2p/%s", routedHost.ID().Pretty()))

	// Now we can build a full multiaddress to reach this host
	// by encapsulating both addresses:
	// addr := routedHost.Addrs()[0]
	addrs := routedHost.Addrs()
	log.Printf("INFO My ID is %s\n", routedHost.ID().Pretty())
	log.Println("INFO I can be reached at:")
	log.Println("MULTIADDRS_LIST_START")
	for _, addr := range addrs {
		fmt.Println(addr.Encapsulate(hostAddr))
	}
	fmt.Println("MULTIADDRS_LIST_END")

	return routedHost, ndht, nil
}

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

  Libp2p types helpers

*/

// KeyPairFromFetchAIKey  key pair from hex encoded secp256k1 private key
func KeyPairFromFetchAIKey(key string) (crypto.PrivKey, crypto.PubKey, error) {
	pk_bytes, err := hex.DecodeString(key)
	if err != nil {
		return nil, nil, err
	}

	btc_private_key, _ := btcec.PrivKeyFromBytes(btcec.S256(), pk_bytes)
	prvKey, pubKey, err := crypto.KeyPairFromStdKey(btc_private_key)
	if err != nil {
		return nil, nil, err
	}

	return prvKey, pubKey, nil
}

// GetPeersAddrInfo Parse multiaddresses and convert them to peer.AddrInfo
func GetPeersAddrInfo(peers []string) ([]peer.AddrInfo, error) {
	pinfos := make([]peer.AddrInfo, len(peers))
	for i, addr := range peers {
		maddr := multiaddr.StringCast(addr)
		p, err := peer.AddrInfoFromP2pAddr(maddr)
		if err != nil {
			return pinfos, err
		}
		pinfos[i] = *p
	}
	return pinfos, nil
}

// IDFromFetchAIPublicKey Get PeeID (multihash) from fetchai public key
func IDFromFetchAIPublicKey(public_key string) (peer.ID, error) {
	b, err := hex.DecodeString(public_key)
	if err != nil {
		return "", err
	}

	pub_bytes := make([]byte, 0, btcec.PubKeyBytesLenUncompressed)
	pub_bytes = append(pub_bytes, 0x4) // btcec.pubkeyUncompressed
	pub_bytes = append(pub_bytes, b...)

	pub_key, err := btcec.ParsePubKey(pub_bytes, btcec.S256())
	if err != nil {
		return "", err
	}

	multihash, err := peer.IDFromPublicKey((*crypto.Secp256k1PublicKey)(pub_key))
	if err != nil {
		return "", err
	}

	return multihash, nil
}
