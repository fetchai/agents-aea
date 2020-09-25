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

package monitoring

import (
	"fmt"
	"os"
	"time"
)

type FileGauge struct {
	value float64
}

func (fm *FileGauge) Set(value float64) {
	fm.value = value
}

func (fm FileGauge) Get() float64 {
	return fm.value
}

func (fm *FileGauge) Inc() {
	fm.value += 1.
}

func (fm *FileGauge) Dec() {
	fm.value -= 1.
}

func (fm *FileGauge) Add(count float64) {
	fm.value += count
}

func (fm *FileGauge) Sub(count float64) {
	fm.value -= count
}

type FileMonitoring struct {
	Namespace string
	gaugeDict map[string]*FileGauge

	path    string
	closing chan struct{}
}

func NewFileMonitoring(namespace string) *FileMonitoring {
	fm := &FileMonitoring{
		Namespace: namespace,
	}

	fm.gaugeDict = map[string]*FileGauge{}
	cwd, _ := os.Getwd()
	fm.path = cwd + "/" + fm.Namespace + ".stats"

	return fm
}

func (fm *FileMonitoring) NewGauge(name string, description string) (Gauge, error) {
	gauge := &FileGauge{}
	fm.gaugeDict[name] = gauge

	return gauge, nil
}

func (fm *FileMonitoring) GetGauge(name string) (Gauge, bool) {
	gauge, ok := fm.gaugeDict[name]
	return gauge, ok
}

func (fm *FileMonitoring) Start() {
	if fm.closing != nil {
		return
	}
	fm.closing = make(chan struct{})

	file, _ := os.OpenFile(fm.path, os.O_WRONLY|os.O_CREATE, 0666)
	for {
		select {
		case <-fm.closing:
			file.Close()
			break
		default:
			file.Truncate(0)
			file.Seek(0, 0)
			file.WriteString(fm.getStats())
			time.Sleep(5 * time.Second)
		}
	}
}

func (fm *FileMonitoring) Stop() {
	close(fm.closing)
}

func (fm FileMonitoring) getStats() string {
	var stats string
	for name, value := range fm.gaugeDict {
		strValue := fmt.Sprintf("%e", value.Get())
		stats += fm.Namespace + "_" + name + " " + strValue + "\n"
	}
	return stats
}

func (fm *FileMonitoring) Info() string {
	return "FileMonitoring on " + fm.path
}
