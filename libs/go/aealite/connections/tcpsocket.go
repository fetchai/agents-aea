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

package connections

import (
	wallet "aealite/wallet"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"errors"
	"strconv"
)

type TCPSocketChannel struct {
	address       string
	port          uint16
	conn          *tls.Conn
	peerPublicKey string
}

func (sock *TCPSocketChannel) Connect() error {
	var err error
	conf := &tls.Config{
		InsecureSkipVerify: true,
	}

	sock.conn, err = tls.Dial("tcp", sock.address+":"+strconv.FormatInt(int64(sock.port), 10), conf)

	if err != nil {
		return err
	}

	state := sock.conn.ConnectionState()
	var cert *x509.Certificate

	for _, v := range state.PeerCertificates {
		cert = v
	}

	pub := cert.PublicKey.(*ecdsa.PublicKey)
	publicKeyBytes := elliptic.Marshal(pub.Curve, pub.X, pub.Y)

	signature, err := sock.Read()
	logger.Debug().Msgf("got signature %d bytes", len(signature))
	if err != nil {
		return err
	}

	pubkey, err := wallet.PubKeyFromFetchAIPublicKey(sock.peerPublicKey)
	if err != nil {
		return err
	}
	ok, err := pubkey.Verify(publicKeyBytes, signature)
	if err != nil {
		return err
	}
	if !ok {
		return errors.New("tls signature check failed")

	}
	return nil
}

func (sock *TCPSocketChannel) Read() ([]byte, error) {
	buf := make([]byte, 4)
	_, err := sock.conn.Read(buf)
	if err != nil {
		return buf, err
	}
	size := binary.BigEndian.Uint32(buf)

	buf = make([]byte, size)
	_, err = sock.conn.Read(buf)
	return buf, err
}

func (sock *TCPSocketChannel) Write(data []byte) error {
	size := uint32(len(data))
	buf := make([]byte, 4, 4+size)
	binary.BigEndian.PutUint32(buf, size)
	buf = append(buf, data...)
	_, err := sock.conn.Write(buf)
	logger.Debug().Msgf("wrote data to pipe: %d bytes", size)
	return err
}

func (sock *TCPSocketChannel) Disconnect() error {
	return sock.conn.Close()
}

func NewSocket(address string, port uint16, peerPublicKey string) Socket {
	return &TCPSocketChannel{address: address, port: port, peerPublicKey: peerPublicKey}
}
