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

package utils

import (
	"bufio"
	"context"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"io"
	"net"
	"os"
	"sync"
	"time"

	"github.com/ipfs/go-cid"
	"github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	dht "github.com/libp2p/go-libp2p-kad-dht"
	"github.com/multiformats/go-multiaddr"
	"github.com/multiformats/go-multihash"
	"github.com/rs/zerolog"

	host "github.com/libp2p/go-libp2p-core/host"
	peerstore "github.com/libp2p/go-libp2p-core/peerstore"

	btcec "github.com/btcsuite/btcd/btcec"
	proto "google.golang.org/protobuf/proto"

	"libp2p_node/aea"
)

const (
	maxMessageSizeDelegateConnection = 1024 * 1024 * 3 // 3Mb
)

var loggerGlobalLevel zerolog.Level = zerolog.DebugLevel

var logger zerolog.Logger = NewDefaultLogger()

// SetLoggerLevel set utils logger level
func SetLoggerLevel(lvl zerolog.Level) {
	logger.Level(lvl)
}

/*
	Logging
*/

func newConsoleLogger() zerolog.Logger {
	zerolog.TimeFieldFormat = time.RFC3339Nano
	return zerolog.New(zerolog.ConsoleWriter{
		Out:        os.Stdout,
		NoColor:    false,
		TimeFormat: time.RFC3339Nano,
	})
}

// NewDefaultLogger basic zerolog console writer
func NewDefaultLogger() zerolog.Logger {
	return newConsoleLogger().
		With().Timestamp().
		Logger().Level(loggerGlobalLevel)
}

// NewDefaultLoggerWithFields zerolog console writer
func NewDefaultLoggerWithFields(fields map[string]string) zerolog.Logger {
	logger := newConsoleLogger().
		With().Timestamp()
	for key, val := range fields {
		logger = logger.Str(key, val)
	}
	return logger.Logger().Level(loggerGlobalLevel)

}

/*
	Helpers
*/

// BootstrapConnect connect to `peers` at bootstrap
// This code is borrowed from the go-ipfs bootstrap process
func BootstrapConnect(ctx context.Context, ph host.Host, kaddht *dht.IpfsDHT, peers []peer.AddrInfo) error {
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
			//defer logger.Debug().Msgf("%s bootstrapDial %s %s", ctx, ph.ID(), p.ID)
			logger.Debug().Msgf("%s bootstrapping to %s", ph.ID(), p.ID)

			ph.Peerstore().AddAddrs(p.ID, p.Addrs, peerstore.PermanentAddrTTL)
			if err := ph.Connect(ctx, p); err != nil {
				//logger.Error().
				//	Str("err", err.Error()).
				//	Msgf("failed to bootstrap with %v", p.ID)
				errs <- err
				return
			}

			logger.Debug().Msgf("bootstrapped with %v", p.ID)
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
		return errors.New("failed to bootstrap: " + err.Error())
	}

	// workaround: to avoid getting `failed to find any peer in table`
	//  when calling dht.Provide (happens occasionally)
	logger.Debug().Msg("waiting for bootstrap peers to be added to dht routing table...")
	for _, peer := range peers {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		for kaddht.RoutingTable().Find(peer.ID) == "" {
			select {
			case <-ctx.Done():
				return errors.New("timeout: entry peer haven't been added to DHT routing table " + peer.ID.Pretty())
			case <-time.After(time.Millisecond * 5):
			}
		}
	}

	return nil
}

// ComputeCID compute content id for ipfsDHT
func ComputeCID(addr string) (cid.Cid, error) {
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

/*
   Utils
*/

// WriteBytesConn send bytes to `conn`
func WriteBytesConn(conn net.Conn, data []byte) error {
	size := uint32(len(data))
	buf := make([]byte, 4, 4+size)
	binary.BigEndian.PutUint32(buf, size)
	buf = append(buf, data...)
	_, err := conn.Write(buf)
	return err
}

// ReadBytesConn receive bytes from `conn`
func ReadBytesConn(conn net.Conn) ([]byte, error) {
	buf := make([]byte, 4)
	_, err := conn.Read(buf)
	if err != nil {
		return buf, err
	}

	size := binary.BigEndian.Uint32(buf)
	if size > maxMessageSizeDelegateConnection {
		return nil, errors.New("Expected message size larger than maximum allowed")
	}

	buf = make([]byte, size)
	_, err = conn.Read(buf)
	return buf, err
}

// WriteEnvelopeConn send envelope to `conn`
func WriteEnvelopeConn(conn net.Conn, envelope *aea.Envelope) error {
	data, err := proto.Marshal(envelope)
	if err != nil {
		return err
	}
	return WriteBytesConn(conn, data)
}

// ReadEnvelopeConn receive envelope from `conn`
func ReadEnvelopeConn(conn net.Conn) (*aea.Envelope, error) {
	envelope := &aea.Envelope{}
	data, err := ReadBytesConn(conn)
	if err != nil {
		return envelope, err
	}
	err = proto.Unmarshal(data, envelope)
	return envelope, err
}

// ReadBytes from a network stream
func ReadBytes(s network.Stream) ([]byte, error) {
	rstream := bufio.NewReader(s)

	buf := make([]byte, 4)
	_, err := io.ReadFull(rstream, buf)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msg("while receiving size")
		return buf, err
	}

	size := binary.BigEndian.Uint32(buf)
	if size > maxMessageSizeDelegateConnection {
		return nil, errors.New("Expected message size larger than maximum allowed")
	}
	//logger.Debug().Msgf("expecting %d", size)

	buf = make([]byte, size)
	_, err = io.ReadFull(rstream, buf)

	return buf, err
}

// WriteBytes to a network stream
func WriteBytes(s network.Stream, data []byte) error {
	wstream := bufio.NewWriter(s)

	size := uint32(len(data))
	buf := make([]byte, 4)
	binary.BigEndian.PutUint32(buf, size)

	_, err := wstream.Write(buf)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msg("while sending size")
		return err
	}

	//logger.Debug().Msgf("writing %d", len(data))
	_, err = wstream.Write(data)
	wstream.Flush()
	return err
}

// ReadString from a network stream
func ReadString(s network.Stream) (string, error) {
	data, err := ReadBytes(s)
	return string(data), err
}

// WriteEnvelope to a network stream
func WriteEnvelope(envel *aea.Envelope, s network.Stream) error {
	wstream := bufio.NewWriter(s)
	data, err := proto.Marshal(envel)
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

// ReadEnvelope from a network stream
func ReadEnvelope(s network.Stream) (*aea.Envelope, error) {
	envel := &aea.Envelope{}
	rstream := bufio.NewReader(s)

	buf := make([]byte, 4)
	_, err := io.ReadFull(rstream, buf)

	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msg("while reading size")
		return envel, err
	}

	size := binary.BigEndian.Uint32(buf)
	if size > maxMessageSizeDelegateConnection {
		return nil, errors.New("Expected message size larger than maximum allowed")
	}
	//logger.Debug().Msgf("received size: %d %x", size, buf)
	buf = make([]byte, size)
	_, err = io.ReadFull(rstream, buf)
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msg("while reading data")
		return envel, err
	}

	err = proto.Unmarshal(buf, envel)
	return envel, err
}
