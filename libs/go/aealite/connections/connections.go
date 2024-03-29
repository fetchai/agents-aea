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
	protocols "aealite/protocols"
)

type Socket interface {
	Connect() error
	Read() ([]byte, error)
	Write(data []byte) error
	Disconnect() error
}

type Connection interface {
	InitFromEnv(envFile string) error
	Connect() error
	Get() *protocols.Envelope
	Put(envelope *protocols.Envelope) error
	Disconnect() error
	Initialised() bool
}
