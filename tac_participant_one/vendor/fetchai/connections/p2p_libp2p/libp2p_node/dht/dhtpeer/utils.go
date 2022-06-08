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

package dhtpeer

import (
	utils "libp2p_node/utils"
	"net"
)

type TLSListener struct {
	Listener  net.Listener
	Signature []byte
}

func (listener TLSListener) Accept() (net.Conn, error) {
	con, err := listener.Listener.Accept()

	if err != nil {
		return con, err
	}

	err = utils.WriteBytesConn(con, listener.Signature)
	return con, err
}

func (listener TLSListener) Close() error {
	return listener.Listener.Close()
}

func (listener TLSListener) Addr() net.Addr {
	return listener.Listener.Addr()
}
