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
	"sync"
	"time"
)

type FileGauge struct {
	value float64
	lock  sync.RWMutex
}

func (fg *FileGauge) Set(value float64) {
	fg.lock.Lock()
	fg.value = value
	fg.lock.Unlock()

}

func (fg *FileGauge) Get() float64 {
	return fg.value

}

func (fg *FileGauge) Inc() {
	fg.Add(1.)
}

func (fg *FileGauge) Dec() {
	fg.Sub(1)
}

func (fg *FileGauge) Add(count float64) {
	fg.lock.Lock()
	fg.value += count
	fg.lock.Unlock()

}

func (fg *FileGauge) Sub(count float64) {
	fg.lock.Lock()
	fg.value -= count
	fg.lock.Unlock()

}

type FileCounter struct {
	value float64
	lock  sync.RWMutex
}

func (fc *FileCounter) Inc() {
	fc.Add(1.)

}

func (fc *FileCounter) Add(count float64) {
	fc.lock.Lock()
	fc.value += count
	fc.lock.Unlock()
}

func (fc *FileCounter) Get() float64 {
	return fc.value
}

type FileHistogram struct {
	buckets []float64
	counts  []uint64
	lock    sync.RWMutex
}

func (fh *FileHistogram) Observe(value float64) {
	fh.lock.Lock()
	var i int = 0
	for i < len(fh.buckets) {
		if value <= fh.buckets[i] {
			fh.counts[i] += 1
		}
		i++
	}
	fh.counts[i] += 1
	fh.lock.Unlock()
}

type FileMonitoring struct {
	Namespace   string
	gaugeDict   map[string]*FileGauge
	counterDict map[string]*FileCounter
	histoDict   map[string]*FileHistogram

	timer *Timer

	path    string
	write   bool
	closing chan struct{}
}

func NewFileMonitoring(namespace string, write bool) *FileMonitoring {
	fm := &FileMonitoring{
		Namespace: namespace,
	}

	fm.counterDict = map[string]*FileCounter{}
	fm.gaugeDict = map[string]*FileGauge{}
	fm.histoDict = map[string]*FileHistogram{}

	fm.timer = &Timer{
		list: map[string]time.Time{},
		lock: sync.RWMutex{},
	}

	cwd, _ := os.Getwd()
	fm.path = cwd + "/" + fm.Namespace + ".stats"
	fm.write = write

	return fm
}

func (fm *FileMonitoring) NewCounter(name string, description string) (Counter, error) {
	counter := &FileCounter{}
	fm.counterDict[name] = counter

	return counter, nil

}

func (fm *FileMonitoring) GetCounter(name string) (Counter, bool) {
	counter, ok := fm.counterDict[name]
	return counter, ok
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

func (fm *FileMonitoring) NewHistogram(
	name string,
	description string,
	buckets []float64,
) (Histogram, error) {
	histogram := &FileHistogram{
		buckets: buckets,
		counts:  make([]uint64, len(buckets)+1),
	}
	fm.histoDict[name] = histogram

	return histogram, nil
}

func (fm *FileMonitoring) GetHistogram(name string) (Histogram, bool) {
	histo, ok := fm.histoDict[name]
	return histo, ok
}

func (fm *FileMonitoring) Start() {
	if fm.closing != nil || !fm.write {
		return
	}
	fm.closing = make(chan struct{})

	file, _ := os.OpenFile(fm.path, os.O_WRONLY|os.O_CREATE, 0666)
L:
	for {
		select {
		case <-fm.closing:
			file.Close()
			break L
		default:
			ignore(file.Truncate(0))
			_, err := file.Seek(0, 0)
			ignore(err)
			_, err = file.WriteString(fm.getStats())
			ignore(err)
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
	for name, value := range fm.counterDict {
		strValue := fmt.Sprintf("%e", value.Get())
		stats += fm.Namespace + "_" + name + " " + strValue + "\n"
	}
	// TODO: report histograms
	return stats
}

func (fm *FileMonitoring) Info() string {
	return "FileMonitoring on " + fm.path
}

func (fm *FileMonitoring) Timer() *Timer {
	return fm.timer
}
