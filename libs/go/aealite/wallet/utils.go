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

package wallet

import (
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"

	"github.com/libp2p/go-libp2p-core/crypto"
	"golang.org/x/crypto/ripemd160" // nolint:staticcheck
	"golang.org/x/crypto/sha3"

	btcec "github.com/btcsuite/btcd/btcec"
	"github.com/btcsuite/btcutil/bech32"
	"github.com/ethereum/go-ethereum/common/hexutil"
	ethCrypto "github.com/ethereum/go-ethereum/crypto"
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

// BTCPubKeyFromFetchAIPublicKey
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

// ConvertStrEncodedSignatureToDER
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

// ConvertDEREncodedSignatureToStr
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
	ledgerId string,
	message []byte,
	signature string,
	pubkey string,
) (bool, error) {
	verifySignature, found := verifyLedgerSignatureTable[ledgerId]
	if found {
		return verifySignature(message, signature, pubkey)
	}
	return false, errors.New("Unsupported ledger")
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
		return false, errors.New("Recovered and expected addresses don't match")
	}

	return true, nil
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

// AgentAddressFromPublicKey get wallet address from public key associated with ledgerId
// format from: https://github.com/fetchai/agents-aea/blob/main/aea/crypto/cosmos.py#L120
func AgentAddressFromPublicKey(ledgerId string, publicKey string) (string, error) {
	if addressFromPublicKey, found := addressFromPublicKeyTable[ledgerId]; found {
		return addressFromPublicKey(publicKey)
	}
	return "", errors.New("Unsupported ledger " + ledgerId)
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
	if err != nil {
		fmt.Println("IGNORED:", err)
	}
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

func FetchAIPublicKeyFromFetchAIPrivateKey(privateKey string) (string, error) {
	pkBytes, err := hex.DecodeString(privateKey)
	if err != nil {
		return "", err
	}
	_, btcPublicKey := btcec.PrivKeyFromBytes(btcec.S256(), pkBytes)

	return hex.EncodeToString(btcPublicKey.SerializeCompressed()), nil
}
