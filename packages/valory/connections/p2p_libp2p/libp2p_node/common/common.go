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
package common

type PipeError struct {
	Err error
	Msg string
}

func (err *PipeError) Error() string {
	return err.Msg
}

func (err *PipeError) Unwrap() error {
	return err.Err
}

type Pipe interface {
	Connect() error
	Read() ([]byte, error)
	Write(data []byte) error
	Close() error
}
