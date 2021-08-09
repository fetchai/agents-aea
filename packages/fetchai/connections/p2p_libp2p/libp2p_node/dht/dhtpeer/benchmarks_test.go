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
	"bufio"
	"flag"
	"net"
	"os"
	"testing"

	"libp2p_node/acn"
	"libp2p_node/aea"
	"libp2p_node/utils"

	"github.com/rs/zerolog"
)

/* **********
* How to run
* ***********

	$ go test -p 1 -count 20 libp2p_node/dht/dhtpeer/ -run=XXX  -bench .  -benchtime=20x -peers-keys-file=/path/to/file/benchmark_peers_keys.txt -agents-keys-file=/path/to/file/benchmark_agents_keys.txt

*/

var peersKeysFilePath string
var agentsKeysFilePath string
var tcpUri = "localhost:12345"

func init() {
	flag.StringVar(&peersKeysFilePath, "peers-keys-file", "", "File with list of EC private keys")
	flag.StringVar(
		&agentsKeysFilePath,
		"agents-keys-file",
		"",
		"File with list of agents EC private keys",
	)
}

/* **********************************
 * baseline TCP connection benchmark
 * ********************************** */

// helpers

func acceptAndEcho(server net.Listener) {
	for {
		conn, err := server.Accept()
		if err != nil {
			return
		}
		go func() {
			for {
				buf, err := utils.ReadBytesConn(conn)
				if err != nil {
					return
				}
				err = utils.WriteBytesConn(conn, buf)
				if err != nil {
					return
				}

			}
		}()
	}
}

func connect(uri string, b *testing.B) net.Conn {
	conn, err := net.Dial("tcp", uri)
	if err != nil {
		b.Fatal(err.Error())
	}
	return conn

}
func sendAndReceive(conn net.Conn, buf []byte, b *testing.B) {
	err := utils.WriteBytesConn(conn, buf)
	if err != nil {
		b.Fatal(err.Error())
	}
	_, err = utils.ReadBytesConn(conn)
	if err != nil {
		b.Fatal(err.Error())
	}
}

func connectAndSend(buf []byte, b *testing.B) {
	conn := connect(tcpUri, b)
	sendAndReceive(conn, buf, b)
	conn.Close()
}

// benchs

func BenchmarkBaselineTCPEcho(b *testing.B) {

	tcpServer, err := net.Listen("tcp", tcpUri)
	if err != nil {
		b.Fatal(err.Error())
	}
	go acceptAndEcho(tcpServer)
	buf := make([]byte, 200)
	conn := connect(tcpUri, b)

	for i := 0; i < b.N; i++ {
		sendAndReceive(conn, buf, b)
	}
	b.StopTimer()
	tcpServer.Close()
	b.StartTimer()

}

func BenchmarkBaselineTCPConnectAndEcho(b *testing.B) {

	tcpServer, err := net.Listen("tcp", tcpUri)
	if err != nil {
		b.Fatal(err.Error())
	}
	go acceptAndEcho(tcpServer)
	buf := make([]byte, 200)

	for i := 0; i < b.N; i++ {
		//var elapsed time.Duration
		//start := time.Now()
		b.ResetTimer()
		connectAndSend(buf, b)
		b.StopTimer()
		//elapsed = time.Since(start)
		//fmt.Println("Elapsed ", elapsed.String())
		b.StartTimer()
	}
	b.StopTimer()
	tcpServer.Close()
	b.StartTimer()

}

/* **********************************
 * Peer DHT operations benchmark
 * ********************************** */

// helpers

func getKeysAndAddrs(b *testing.B) (peers []string, agents []string) {
	peersKeysFile, err := os.Open(peersKeysFilePath)
	if err != nil {
		b.Fatal(err)
	}
	defer peersKeysFile.Close()
	agentsKeysFile, err := os.Open(agentsKeysFilePath)
	if err != nil {
		b.Fatal(err)
	}
	defer agentsKeysFile.Close()

	ksc := bufio.NewScanner(peersKeysFile)
	asc := bufio.NewScanner(agentsKeysFile)

	peers = []string{}
	agents = []string{}
	for ksc.Scan() && asc.Scan() {
		peers = append(peers, ksc.Text())
		agents = append(agents, asc.Text())
	}
	return peers, agents
}

func setupLocalDHTPeerForBench(
	key string,
	agentKey string,
	dhtPort uint16,
	delegatePort uint16,
	entry []string,
) (*DHTPeer, func(), error) {
	/*
		peer, peerCleanup, err := SetupLocalDHTPeer(key, addr, dhtPort, delegatePort, entry)
		if err == nil {
			peer.SetLogLevel(zerolog.Disabled)
			utils.SetLoggerLevel(zerolog.Disabled)
		}
		return peer, peerCleanup, err
	*/

	opts := []Option{
		LocalURI(DefaultLocalHost, dhtPort),
		PublicURI(DefaultLocalHost, dhtPort),
		IdentityFromFetchAIKey(key),
		EnableRelayService(),
		BootstrapFrom(entry),
	}

	if agentKey != "" {
		agentPubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(agentKey)
		if err != nil {
			return nil, nil, err
		}

		agentAddress, err := utils.FetchAIAddressFromPublicKey(agentPubKey)
		if err != nil {
			return nil, nil, err
		}

		peerPubKey, err := utils.FetchAIPublicKeyFromFetchAIPrivateKey(key)
		if err != nil {
			return nil, nil, err
		}

		signature, err := utils.SignFetchAI([]byte(peerPubKey), agentKey)
		if err != nil {
			return nil, nil, err
		}

		record := &acn.AgentRecord{}
		record.Address = agentAddress
		record.PublicKey = agentPubKey
		record.PeerPublicKey = peerPubKey
		record.Signature = signature

		opts = append(opts, RegisterAgentAddress(record, func() bool { return true }))
	}

	if delegatePort != 0 {
		opts = append(opts, EnableDelegateService(delegatePort))
	}

	dhtPeer, err := New(opts...)
	if err != nil {
		return nil, nil, err
	}

	utils.SetLoggerLevel(zerolog.Disabled)

	return dhtPeer, func() { dhtPeer.Close() }, nil
}

func deployPeers(number uint16, b *testing.B) ([]*DHTPeer, []string) {
	peerKeys, agentsKeys := getKeysAndAddrs(b)
	peers := make([]*DHTPeer, 0, number)
	for i := uint16(0); i < number; i++ {
		entry := []string{}
		if i > 0 {
			entry = append(entry, peers[i-1].MultiAddr())
		}
		peer, _, err := setupLocalDHTPeerForBench(
			peerKeys[i], agentsKeys[i], DefaultLocalPort+i, 0,
			entry,
		)
		if err != nil {
			b.Fatal("Failed to initialize DHTPeer:", err)
		}
		peers = append(peers, peer)
	}
	return peers, agentsKeys
}

func closePeers(peers ...*DHTPeer) {
	for _, peer := range peers {
		peer.Close()
	}
}

func setupEchoServicePeers(peers ...*DHTPeer) {
	for _, peer := range peers {
		peer.ProcessEnvelope(func(envel *aea.Envelope) error {
			err := peer.RouteEnvelope(&aea.Envelope{
				To:     envel.Sender,
				Sender: envel.To,
			})
			return err
		})
	}
}

// benchs

func benchmarkAgentRegistration(npeers uint16, b *testing.B) {
	peers, addrs := deployPeers(npeers, b)
	ensureAddressAnnounced(peers...)
	defer closePeers(peers...)

	peer, peerCleanup, err := setupLocalDHTPeerForBench(
		FetchAITestKeys[1], "", DefaultLocalPort+npeers+1, 0,
		[]string{peers[0].MultiAddr()},
	)
	if err != nil {
		b.Fatal(err.Error())
	}
	defer peerCleanup()

	for i := 0; i < b.N; i++ {
		b.ResetTimer()
		err = peer.RegisterAgentAddress(addrs[len(addrs)-1-i%len(addrs)])
		if err != nil {
			b.Fail()
		}
	}
}

func benchmarkAgentLookup(npeers uint16, b *testing.B) {
	peers, addrs := deployPeers(npeers, b)
	ensureAddressAnnounced(peers...)
	defer closePeers(peers...)

	peer, peerCleanup, err := setupLocalDHTPeerForBench(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+npeers+1, 0,
		[]string{peers[len(peers)-1].MultiAddr()},
	)
	if err != nil {
		b.Fatal(err.Error())
	}
	defer peerCleanup()
	ensureAddressAnnounced(peer)

	for i := 0; i < b.N; i++ {
		b.ResetTimer()
		_, _, err = peer.lookupAddressDHT(addrs[len(peers)-1-i%len(peers)])
		if err != nil {
			b.Fail()
		}
	}
}

func benchmarkPeerJoin(npeers uint16, b *testing.B) {
	peers, _ := deployPeers(npeers, b)
	ensureAddressAnnounced(peers...)
	defer closePeers(peers...)

	for i := 0; i < b.N; i++ {
		b.ResetTimer()
		peer, peerCleanup, err := setupLocalDHTPeerForBench(
			FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+npeers+1, 0,
			[]string{peers[i%len(peers)].MultiAddr()},
		)
		if err != nil {
			b.Fatal(err.Error())
		}
		ensureAddressAnnounced(peer)
		b.StopTimer()
		peerCleanup()
		b.StartTimer()
	}
}

func benchmarkPeerEcho(npeers uint16, b *testing.B) {
	peers, addrs := deployPeers(npeers, b)
	ensureAddressAnnounced(peers...)
	defer closePeers(peers...)
	setupEchoServicePeers(peers...)

	peer, peerCleanup, err := setupLocalDHTPeerForBench(
		FetchAITestKeys[1], AgentsTestKeys[1], DefaultLocalPort+npeers+1, 0,
		[]string{peers[len(peers)-1].MultiAddr()},
	)
	if err != nil {
		b.Fatal(err.Error())
	}
	defer peerCleanup()
	ensureAddressAnnounced(peer)
	rxPeer := make(chan *aea.Envelope, 10)
	peer.ProcessEnvelope(func(envel *aea.Envelope) error {
		rxPeer <- envel
		return nil
	})

	for i := 0; i < b.N; i++ {
		envel := &aea.Envelope{
			To:      addrs[len(peers)-1-i%len(peers)],
			Sender:  AgentsTestAddresses[1],
			Message: make([]byte, 101),
		}
		b.ResetTimer()
		err = peer.RouteEnvelope(envel)
		if err != nil {
			b.Error("Failed to RouteEnvelope from peer 2 to peer 1:", err)
		}
		<-rxPeer
	}
}

func BenchmarkAgentRegistration2(b *testing.B)   { benchmarkAgentRegistration(2, b) }
func BenchmarkAgentRegistration8(b *testing.B)   { benchmarkAgentRegistration(8, b) }
func BenchmarkAgentRegistration32(b *testing.B)  { benchmarkAgentRegistration(32, b) }
func BenchmarkAgentRegistration128(b *testing.B) { benchmarkAgentRegistration(128, b) }
func BenchmarkAgentRegistration256(b *testing.B) { benchmarkAgentRegistration(256, b) }

func BenchmarkAgentLookup2(b *testing.B)   { benchmarkAgentLookup(2, b) }
func BenchmarkAgentLookup8(b *testing.B)   { benchmarkAgentLookup(8, b) }
func BenchmarkAgentLookup32(b *testing.B)  { benchmarkAgentLookup(32, b) }
func BenchmarkAgentLookup128(b *testing.B) { benchmarkAgentLookup(128, b) }
func BenchmarkAgentLookup256(b *testing.B) { benchmarkAgentLookup(256, b) }

func BenchmarkPeerJoin2(b *testing.B)   { benchmarkPeerJoin(2, b) }
func BenchmarkPeerJoin8(b *testing.B)   { benchmarkPeerJoin(8, b) }
func BenchmarkPeerJoin32(b *testing.B)  { benchmarkPeerJoin(32, b) }
func BenchmarkPeerJoin128(b *testing.B) { benchmarkPeerJoin(128, b) }
func BenchmarkPeerJoin256(b *testing.B) { benchmarkPeerJoin(256, b) }

func BenchmarkPeerEcho2(b *testing.B)   { benchmarkPeerEcho(2, b) }
func BenchmarkPeerEcho8(b *testing.B)   { benchmarkPeerEcho(8, b) }
func BenchmarkPeerEcho32(b *testing.B)  { benchmarkPeerEcho(32, b) }
func BenchmarkPeerEcho128(b *testing.B) { benchmarkPeerEcho(128, b) }
func BenchmarkPeerEcho256(b *testing.B) { benchmarkPeerEcho(256, b) }
