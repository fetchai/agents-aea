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
	"crypto/sha256"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"math"
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
	"golang.org/x/crypto/ripemd160" // nolint:staticcheck
	"golang.org/x/crypto/sha3"

	host "github.com/libp2p/go-libp2p-core/host"
	peerstore "github.com/libp2p/go-libp2p-core/peerstore"

	btcec "github.com/btcsuite/btcd/btcec"
	"github.com/btcsuite/btcutil/bech32"
	"github.com/ethereum/go-ethereum/common/hexutil"
	ethCrypto "github.com/ethereum/go-ethereum/crypto"
	proto "google.golang.org/protobuf/proto"

	"libp2p_node/aea"
)

const (
	maxMessageSizeDelegateConnection = 1024 * 1024 * 3 // 3Mb
)

var (
	addressFromPublicKeyTable = map[string]func(string) (string, error){
		"fetchai":  FetchAIAddressFromPublicKey,
		"cosmos":   CosmosAddressFromPublicKey,
		"ethereum": EthereumAddressFromPublicKey,
	}
	verifyLedgerSignatureTable = map[string]func([]byte, string, string) (bool, error){
		"fetchai":  VerifyFetchAISignatureBTC,
		"cosmos":   VerifyFetchAISignatureBTC,
		"ethereum": VerifyEthereumSignatureETH,
	}
)

var loggerGlobalLevel zerolog.Level = zerolog.DebugLevel

var logger zerolog.Logger = NewDefaultLogger()

// SetLoggerLevel set utils logger level
func SetLoggerLevel(lvl zerolog.Level) {
	logger = logger.Level(lvl)
}

func ignore(err error) {
	if err != nil {
		fmt.Println("IGNORED:", err)
	}
}

/*
	Logging
*/

func newConsoleLogger() zerolog.Logger {
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
func BootstrapConnect(
	ctx context.Context,
	ph host.Host,
	kaddht *dht.IpfsDHT,
	peers []peer.AddrInfo,
) error {
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
				return errors.New(
					"timeout: entry peer haven't been added to DHT routing table " + peer.ID.Pretty(),
				)
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

/*
	FetchAI Crypto Helpers
*/

// PubKeyFromFetchAIPublicKey create libp2p public key from fetchai hex encoded secp256k1 key
func PubKeyFromFetchAIPublicKey(publicKey string) (crypto.PubKey, error) {
	hexBytes, _ := hex.DecodeString(publicKey)
	return crypto.UnmarshalSecp256k1PublicKey(hexBytes)
}

// FetchAIPublicKeyFromPubKey return FetchAI's format serialized public key
func FetchAIPublicKeyFromPubKey(publicKey crypto.PubKey) (string, error) {
	raw, err := publicKey.Raw()
	if err != nil {
		return "", err
	}
	return hex.EncodeToString(raw), nil
}

// BTCPubKeyFromFetchAIPublicKey from public key string
func BTCPubKeyFromFetchAIPublicKey(publicKey string) (*btcec.PublicKey, error) {
	pbkBytes, err := hex.DecodeString(publicKey)
	if err != nil {
		return nil, err
	}
	pbk, err := btcec.ParsePubKey(pbkBytes, btcec.S256())
	return pbk, err
}

// BTCPubKeyFromEthereumPublicKey create libp2p public key from ethereum uncompressed
//  hex encoded secp256k1 key
func BTCPubKeyFromEthereumPublicKey(publicKey string) (*btcec.PublicKey, error) {
	return BTCPubKeyFromUncompressedHex(publicKey[2:])
}

// ConvertStrEncodedSignatureToDER to convert signature to DER format
// References:
//  - https://github.com/fetchai/agents-aea/blob/main/aea/crypto/cosmos.py#L258
//  - https://github.com/btcsuite/btcd/blob/master/btcec/signature.go#L47
func ConvertStrEncodedSignatureToDER(signature []byte) []byte {
	rb := signature[:len(signature)/2]
	sb := signature[len(signature)/2:]
	length := 6 + len(rb) + len(sb)
	sigDER := make([]byte, length)
	sigDER[0] = 0x30
	sigDER[1] = byte(length - 2)
	sigDER[2] = 0x02
	sigDER[3] = byte(len(rb))
	offset := copy(sigDER[4:], rb) + 4
	sigDER[offset] = 0x02
	sigDER[offset+1] = byte(len(sb))
	copy(sigDER[offset+2:], sb)
	return sigDER
}

// ConvertDEREncodedSignatureToStr Convert signatue from der format to string
// References:
//  - https://github.com/fetchai/agents-aea/blob/main/aea/crypto/cosmos.py#L258
//  - https://github.com/btcsuite/btcd/blob/master/btcec/signature.go#L47
func ConvertDEREncodedSignatureToStr(signature []byte) ([]byte, error) {
	sig, err := btcec.ParseDERSignature(signature, btcec.S256())
	if err != nil {
		return []byte{}, err
	}
	return append(sig.R.Bytes(), sig.S.Bytes()...), nil
}

// ParseFetchAISignature create btcec Signature from base64 formated, string (not DER) encoded RFC6979 signature
func ParseFetchAISignature(signature string) (*btcec.Signature, error) {
	// First convert the signature into a DER one
	sigBytes, err := base64.StdEncoding.DecodeString(signature)
	if err != nil {
		return nil, err
	}
	sigDER := ConvertStrEncodedSignatureToDER(sigBytes)

	// Parse
	sigBTC, err := btcec.ParseSignature(sigDER, btcec.S256())
	return sigBTC, err
}

// VerifyLedgerSignature verify signature of message using public key for supported ledgers
func VerifyLedgerSignature(
	ledgerID string,
	message []byte,
	signature string,
	pubKey string,
) (bool, error) {
	verifySignature, found := verifyLedgerSignatureTable[ledgerID]
	if found {
		return verifySignature(message, signature, pubKey)
	}
	return false, errors.New("unsupported ledger")
}

// VerifyFetchAISignatureBTC verify the RFC6967 string-encoded signature of message using FetchAI public key
func VerifyFetchAISignatureBTC(message []byte, signature string, pubkey string) (bool, error) {
	// construct verifying key
	verifyKey, err := BTCPubKeyFromFetchAIPublicKey(pubkey)
	if err != nil {
		return false, err
	}

	// construct signature
	signatureBTC, err := ParseFetchAISignature(signature)
	if err != nil {
		return false, err
	}

	// verify signature
	messageHash := sha256.New()
	_, err = messageHash.Write([]byte(message))
	if err != nil {
		return false, err
	}

	return signatureBTC.Verify(messageHash.Sum(nil), verifyKey), nil
}

// VerifyFetchAISignatureLibp2p verify RFC6967 string-encoded signature of message using FetchAI public key
func VerifyFetchAISignatureLibp2p(message []byte, signature string, pubkey string) (bool, error) {
	// construct verifying key
	verifyKey, err := PubKeyFromFetchAIPublicKey(pubkey)
	if err != nil {
		return false, err
	}

	// Convert signature into DER encoding
	sigBytes, err := base64.StdEncoding.DecodeString(signature)
	if err != nil {
		return false, err
	}
	sigDER := ConvertStrEncodedSignatureToDER(sigBytes)

	// verify signature
	return verifyKey.Verify(message, sigDER)
}

// SignFetchAI signs message with private key
func SignFetchAI(message []byte, privKey string) (string, error) {
	signingKey, _, err := KeyPairFromFetchAIKey(privKey)
	if err != nil {
		return "", err
	}
	signature, err := signingKey.Sign(message)
	if err != nil {
		return "", err
	}
	strSignature, err := ConvertDEREncodedSignatureToStr(signature)
	if err != nil {
		return "", err
	}
	encodedSignature := base64.StdEncoding.EncodeToString(strSignature)
	return encodedSignature, nil
}

func signHashETH(data []byte) []byte {
	msg := fmt.Sprintf("\x19Ethereum Signed Message:\n%d%s", len(data), data)
	return ethCrypto.Keccak256([]byte(msg))
}

// RecoverAddressFromEthereumSignature verify the signature and returns the address of the signer
// references:
//  - https://github.com/ethereum/go-ethereum/blob/55599ee95d4151a2502465e0afc7c47bd1acba77/internal/ethapi/api.go#L452-L459
//  - https://github.com/ethereum/go-ethereum/blob/55599ee95d4151a2502465e0afc7c47bd1acba77/internal/ethapi/api.go#L404
func RecoverAddressFromEthereumSignature(message []byte, signature string) (string, error) {
	// prepare signature
	sigBytes, err := hexutil.Decode(signature)
	if err != nil {
		return "", err
	}

	if sigBytes[64] != 27 && sigBytes[64] != 28 {
		return "", errors.New("invalid Ethereum signature (V is not 27 or 28)")
	}
	sigBytes[64] -= 27 // Transform yellow paper V from 27/28 to 0/1

	// recover verify key
	recoveredPubKey, err := ethCrypto.SigToPub(signHashETH(message), sigBytes)
	if err != nil {
		return "", err
	}

	return ethCrypto.PubkeyToAddress(*recoveredPubKey).Hex(), nil
}

// VerifyEthereumSignatureETH verify ethereum signature using ethereum public key
func VerifyEthereumSignatureETH(message []byte, signature string, pubkey string) (bool, error) {
	// get expected signer address
	expectedAddress, err := EthereumAddressFromPublicKey(pubkey)
	if err != nil {
		return false, err
	}

	// recover signer address
	recoveredAddress, err := RecoverAddressFromEthereumSignature(message, signature)
	if err != nil {
		return false, err
	}

	if recoveredAddress != expectedAddress {
		return false, errors.New("recovered and expected addresses don't match")
	}

	return true, nil
}

// KeyPairFromFetchAIKey  key pair from hex encoded secp256k1 private key
func KeyPairFromFetchAIKey(key string) (crypto.PrivKey, crypto.PubKey, error) {
	pkBytes, err := hex.DecodeString(key)
	if err != nil {
		return nil, nil, err
	}

	btcPrivateKey, _ := btcec.PrivKeyFromBytes(btcec.S256(), pkBytes)
	prvKey, pubKey, err := crypto.KeyPairFromStdKey(btcPrivateKey)
	if err != nil {
		return nil, nil, err
	}

	return prvKey, pubKey, nil
}

// AgentAddressFromPublicKey get wallet address from public key associated with ledgerId
// format from: https://github.com/fetchai/agents-aea/blob/main/aea/crypto/cosmos.py#L120
func AgentAddressFromPublicKey(ledgerID string, publicKey string) (string, error) {
	if addressFromPublicKey, found := addressFromPublicKeyTable[ledgerID]; found {
		return addressFromPublicKey(publicKey)
	}
	return "", errors.New("Unsupported ledger " + ledgerID)
}

// FetchAIAddressFromPublicKey get wallet address from hex encoded secp256k1 public key
func FetchAIAddressFromPublicKey(publicKey string) (string, error) {
	return cosmosAddressFromPublicKeyWithPrefix("fetch", publicKey)
}

// CosmosAddressFromPublicKey get wallet address from hex encoded secp256k1 public key
func CosmosAddressFromPublicKey(publicKey string) (string, error) {
	return cosmosAddressFromPublicKeyWithPrefix("cosmos", publicKey)
}

// cosmosAddressFromPublicKeyWithPrefix get wallet address from hex encoded secp256k1 public key
// format from: https://github.com/fetchai/agents-aea/blob/main/aea/crypto/cosmos.py#L120
func cosmosAddressFromPublicKeyWithPrefix(prefix string, publicKey string) (string, error) {
	var addr string
	var err error
	hexBytes, err := hex.DecodeString(publicKey)
	if err != nil {
		return addr, err
	}
	hash := sha256.New()
	_, err = hash.Write(hexBytes)
	if err != nil {
		return addr, err
	}
	sha256Hash := hash.Sum(nil)
	hash = ripemd160.New()
	_, err = hash.Write(sha256Hash)
	if err != nil {
		return addr, err
	}
	ripemd160Hash := hash.Sum(nil)
	fiveBitsChar, err := bech32.ConvertBits(ripemd160Hash, 8, 5, true)
	if err != nil {
		return addr, err
	}
	addr, err = bech32.Encode(prefix, fiveBitsChar)
	return addr, err
}

// EthereumAddressFromPublicKey get wallet address from hex encoded secp256k1 public key
// references:
//  - https://github.com/fetchai/agents-aea/blob/main/aea/crypto/ethereum.py#L330
//  - https://github.com/ethereum/go-ethereum/blob/master/crypto/crypto.go#L263
func EthereumAddressFromPublicKey(publicKey string) (string, error) {
	var addr string
	var err error
	hexBytes, err := hex.DecodeString(publicKey[2:])
	if err != nil {
		return addr, err
	}
	hash := sha3.NewLegacyKeccak256()
	_, err = hash.Write(hexBytes)
	if err != nil {
		return addr, err
	}
	sha3KeccakHash := hash.Sum(nil)
	return encodeChecksumEIP55(sha3KeccakHash[12:]), nil
}

// encodeChecksumEIP55 EIP55-compliant hex string representation of the address
// source: https://github.com/ethereum/go-ethereum/blob/master/common/types.go#L210
// reference: https://github.com/ethereum/EIPs/blob/master/EIPS/eip-55.md
func encodeChecksumEIP55(address []byte) string {
	unchecksummed := hex.EncodeToString(address[:])
	sha := sha3.NewLegacyKeccak256()
	_, err := sha.Write([]byte(unchecksummed))
	ignore(err)
	hash := sha.Sum(nil)

	result := []byte(unchecksummed)
	for i := 0; i < len(result); i++ {
		hashByte := hash[i/2]
		if i%2 == 0 {
			hashByte = hashByte >> 4
		} else {
			hashByte &= 0xf
		}
		if result[i] > '9' && hashByte > 7 {
			result[i] -= 32
		}
	}
	return "0x" + string(result)
}

// IDFromFetchAIPublicKey Get PeeID (multihash) from fetchai public key
func IDFromFetchAIPublicKey(publicKey string) (peer.ID, error) {
	b, err := hex.DecodeString(publicKey)
	if err != nil {
		return "", err
	}

	pubKey, err := btcec.ParsePubKey(b, btcec.S256())
	if err != nil {
		return "", err
	}

	multihash, err := peer.IDFromPublicKey((*crypto.Secp256k1PublicKey)(pubKey))
	if err != nil {
		return "", err
	}

	return multihash, nil
}

// BTCPubKeyFromUncompressedHex get public key from secp256k1 hex encoded  uncompressed representation
func BTCPubKeyFromUncompressedHex(publicKey string) (*btcec.PublicKey, error) {
	b, err := hex.DecodeString(publicKey)
	if err != nil {
		return nil, err
	}

	pubBytes := make([]byte, 0, btcec.PubKeyBytesLenUncompressed)
	pubBytes = append(pubBytes, 0x4) // btcec.pubkeyUncompressed
	pubBytes = append(pubBytes, b...)

	return btcec.ParsePubKey(pubBytes, btcec.S256())
}

// IDFromFetchAIPublicKeyUncompressed Get PeeID (multihash) from fetchai public key
func IDFromFetchAIPublicKeyUncompressed(publicKey string) (peer.ID, error) {
	pubKey, err := BTCPubKeyFromUncompressedHex(publicKey)
	if err != nil {
		return "", err
	}

	multihash, err := peer.IDFromPublicKey((*crypto.Secp256k1PublicKey)(pubKey))
	if err != nil {
		return "", err
	}

	return multihash, nil
}

// FetchAIPublicKeyFromFetchAIPrivateKey get fetchai public key from fetchai private key
func FetchAIPublicKeyFromFetchAIPrivateKey(privateKey string) (string, error) {
	pkBytes, err := hex.DecodeString(privateKey)
	if err != nil {
		return "", err
	}
	_, btcPublicKey := btcec.PrivKeyFromBytes(btcec.S256(), pkBytes)

	return hex.EncodeToString(btcPublicKey.SerializeCompressed()), nil
}

/*
   Utils
*/

// WriteBytesConn send bytes to `conn`
func WriteBytesConn(conn net.Conn, data []byte) error {

	if len(data) > math.MaxInt32 {
		logger.Error().Msg("data size too large")
		return errors.New("data size too large")
	}
	if len(data) == 0 {
		logger.Error().Msg("No data to write")
		return nil
	}

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
		return nil, errors.New("expected message size larger than maximum allowed")
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
	if s == nil {
		panic("CRITICAL can not write to nil stream")
	}

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
		return nil, errors.New("expected message size larger than maximum allowed")
	}

	//logger.Debug().Msgf("expecting %d", size)

	buf = make([]byte, size)
	_, err = io.ReadFull(rstream, buf)

	return buf, err
}

// WriteBytes to a network stream
func WriteBytes(s network.Stream, data []byte) error {
	if len(data) > math.MaxInt32 {
		logger.Error().Msg("data size too large")
		return errors.New("data size too large")
	}
	if len(data) == 0 {
		logger.Error().Msg("No data to write")
		return nil
	}

	if s == nil {
		panic("CRITICAL, can not write to nil stream")
	}

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
	if err != nil {
		logger.Error().
			Str("err", err.Error()).
			Msg("Error on data write")
		return err
	}
	if s == nil {
		panic("CRITICAL, can not flush nil stream")
	}

	err = wstream.Flush()
	return err
}

type ConnPipe struct {
	Conn net.Conn
}

func (conPipe ConnPipe) Connect() error {
	return nil
}
func (conPipe ConnPipe) Read() ([]byte, error) {
	return ReadBytesConn(conPipe.Conn)
}
func (conPipe ConnPipe) Write(data []byte) error {
	return WriteBytesConn(conPipe.Conn, data)
}
func (conPipe ConnPipe) Close() error {
	return nil
}

type StreamPipe struct {
	Stream network.Stream
}

func (streamPipe StreamPipe) Connect() error {
	return nil
}
func (streamPipe StreamPipe) Read() ([]byte, error) {
	return ReadBytes(streamPipe.Stream)
}
func (streamPipe StreamPipe) Write(data []byte) error {
	return WriteBytes(streamPipe.Stream, data)
}
func (streamPipe StreamPipe) Close() error {
	return nil
}
