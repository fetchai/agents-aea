// +build linux darwin !windows

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
	"errors"
	"os"
)

type UnixPipe struct {
	msgin_path  string
	msgout_path string
	msgin       *os.File
	msgout      *os.File
}

func (pipe *UnixPipe) Connect() error {
	// open pipes
	var erro, erri error
	pipe.msgout, erro = os.OpenFile(pipe.msgout_path, os.O_WRONLY, os.ModeNamedPipe)
	pipe.msgin, erri = os.OpenFile(pipe.msgin_path, os.O_RDONLY, os.ModeNamedPipe)

	if erri != nil || erro != nil {
		if erri != nil {
			return erri
		}
		return erro
	}

	return nil
}

func (pipe *UnixPipe) Read() ([]byte, error) {
	buf := make([]byte, 4)
	_, err := pipe.msgin.Read(buf)
	if err != nil {
		return buf, errors.New("while receiving size" + err.Error())
	}
	size := binary.BigEndian.Uint32(buf)

	buf = make([]byte, size)
	_, err = pipe.msgin.Read(buf)
	return buf, err

}

func (pipe *UnixPipe) Write(data []byte) error {
	size := uint32(len(data))
	buf := make([]byte, 4, 4+size)
	binary.BigEndian.PutUint32(buf, size)
	buf = append(buf, data...)
	_, err := pipe.msgout.Write(buf)
	logger.Debug().Msgf("wrote data to pipe: %d bytes", size)
	return err
}

func (pipe *UnixPipe) Close() error {
	pipe.msgin.Close()
	pipe.msgout.Close()
	return nil
}

func NewPipe(msgin_path string, msgout_path string) Pipe {
	return &UnixPipe{msgin_path: msgin_path, msgout_path: msgout_path, msgin: nil, msgout: nil}
}
