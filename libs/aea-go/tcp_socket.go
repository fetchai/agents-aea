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

package aea

import (
	"encoding/binary"
	"net"
	"strconv"
)

type TCPSocketChannel struct {
	address string
	port    uint16
	conn    net.Conn
}

func (sock *TCPSocketChannel) Connect() error {
	var err error
	sock.conn, err = net.Dial("tcp", sock.address+":"+strconv.FormatInt(int64(sock.port), 10))

	if err != nil {
		return err
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

func (sock *TCPSocketChannel) Close() error {
	return sock.conn.Close()
}

func NewSocket(address string, port uint16) Socket {
	return &TCPSocketChannel{address: address, port: port}
}
