/* -*- coding: utf-8 -*-
* ------------------------------------------------------------------------------
*
*   Copyright 2018-2021 Fetch.AI Limited
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
	"encoding/json"
	"bytes"
	"testing"
	"errors"
	"github.com/rs/zerolog"
	"github.com/stretchr/testify/assert"
	mocks "libp2p_node/mocks"
	gomock "github.com/golang/mock/gomock"

)

// Crypto operations


func TestEthereumCrypto(t *testing.T) {
	//privateKey := "0xb60fe8027fb82f1a1bd6b8e66d4400f858989a2c67428a4e7f589441700339b0"
	publicKey := "0xf753e5a9e2368e97f4db869a0d956d3ffb64672d6392670572906c786b5712ada13b6bff882951b3ba3dd65bdacc915c2b532efc3f183aa44657205c6c337225"
	address := "0xb8d8c62d4a1999b7aea0aebBD5020244a4a9bAD8"
	publicKeySignature := "0x304c2ba4ae7fa71295bfc2920b9c1268d574d65531f1f4d2117fc1439a45310c37ab75085a9df2a4169a4d47982b330a4387b1ded0c8881b030629db30bbaf3a1c"

	addFromPublicKey, err := EthereumAddressFromPublicKey(publicKey)
	if err != nil || addFromPublicKey != address {
		t.Error(
			"Error when computing address from public key or address and public key don't match",
		)
	}

	_, err = BTCPubKeyFromEthereumPublicKey(publicKey)
	if err != nil {
		t.Errorf("While building BTC public key from string: %s", err.Error())
	}

	/*
		ethSig, err := secp256k1.Sign(hashedPublicKey, hexutil.MustDecode(privateKey))
		if err != nil {
			t.Error(err.Error())
		}
		println(hexutil.Encode(ethSig))
		hash := sha3.NewLegacyKeccak256()
		_, err = hash.Write([]byte(publicKey))
		if err != nil {
			t.Error(err.Error())
		}
		sha3KeccakHash := hash.Sum(nil)
	*/

	valid, err := VerifyEthereumSignatureETH([]byte(publicKey), publicKeySignature, publicKey)
	if err != nil {
		t.Error(err.Error())
	}

	if !valid {
		t.Errorf("Signer address don't match %s", addFromPublicKey)
	}
}


func TestFetchAICrypto(t *testing.T) {
	publicKey := "02358e3e42a6ba15cf6b2ba6eb05f02b8893acf82b316d7dd9cda702b0892b8c71"
	address := "fetch19dq2mkcpp6x0aypxt9c9gz6n4fqvax0x9a7t5r"
	peerPublicKey := "027af21aff853b9d9589867ea142b0a60a9611fc8e1fae04c2f7144113fa4e938e"
	pySigStrCanonize := "N/GOa7/m3HU8/gpLJ88VCQ6vXsdrfiiYcqnNtF+c2N9VG9ZIiycykN4hdbpbOCGrChMYZQA3G1GpozsShrUBgg=="

	addressFromPublicKey, _ := FetchAIAddressFromPublicKey(publicKey)
	if address != addressFromPublicKey {
		t.Error("[ERR] Addresses don't match")
	} else {
		t.Log("[OK] Agent address matches its public key")
	}

	valid, err := VerifyFetchAISignatureBTC(
		[]byte(peerPublicKey),
		pySigStrCanonize,
		publicKey,
	)
	if !valid {
		t.Errorf("Signature using BTC don't match %s", err.Error())
	}
	valid, err = VerifyFetchAISignatureLibp2p(
		[]byte(peerPublicKey),
		pySigStrCanonize,
		publicKey,
	)
	if !valid {
		t.Errorf("Signature using LPP don't match %s", err.Error())
	}
}


func TestSetLoggerLevel(t *testing.T) {
	assert.Equal(t, logger.GetLevel(), zerolog.Level(0), "Initial log level is not 0")
	
	lvl := zerolog.InfoLevel
	SetLoggerLevel(lvl)
	
	assert.Equal(t, logger.GetLevel(), lvl, "Waited for logger level %d but got %d", lvl, logger.GetLevel())
}

func ExampleIgnore() {
	ignore(errors.New("Test"))
    // Output: IGNORED: Test
}

func TestNewDefaultLoggerWithFields(t *testing.T){
	fields := map[string]string{
		"test_field": "test_value",
	}
	var log_buffer bytes.Buffer
	logger := NewDefaultLoggerWithFields(fields).Output(&log_buffer)
	logger.Info().Msg("test")
	var json_result map[string]interface{}
    json.Unmarshal(log_buffer.Bytes(), &json_result)
	assert.Equal(t, json_result["test_field"], "test_value")
}

func TestComputeCID(t *testing.T){
	address := "fetch19dq2mkcpp6x0aypxt9c9gz6n4fqvax0x9a7t5r"
	cid, err := ComputeCID(address)
	assert.Equal(t, nil, err)
	assert.Equal(t, "QmZ6ryKyS9rSnesX8YnFLAmFwFuRMdHpE7pQ2V6SjXTbqM", cid.String())
}



func TestWriteBytes(t * testing.T) {
	mockCtrl := gomock.NewController(t)
    defer mockCtrl.Finish()
	mock_stream := mocks.NewMockStream(mockCtrl)
	mock_stream.EXPECT().Write([]byte{0, 0, 0, 5, 104, 101, 108, 108, 111}).Return(0, nil).Times(1)
	WriteBytes(mock_stream, []byte("hello"))
	
	mock_stream.EXPECT().Write([]byte{0, 0, 0, 4, 104, 101, 108, 108}).Return(8, errors.New("oops")).Times(1)
	err := WriteBytes(mock_stream, []byte("hell"))
	assert.NotEqual(t, err, nil)
	
	
}