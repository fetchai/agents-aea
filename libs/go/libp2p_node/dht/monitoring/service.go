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
	"errors"
	"log"
	"sync"
	"time"
)

type Gauge interface {
	Set(value float64)
	Inc()
	Dec()
	Add(count float64)
	Sub(count float64)
}

type Counter interface {
	Inc()
	Add(count float64)
}

type Histogram interface {
	Observe(value float64)
}

type Summary interface {
	Observe(value float64)
}

type Timer struct {
	list map[string]time.Time
	lock sync.RWMutex
}

func (tm *Timer) NewTimer() time.Time {
	return time.Now()
}

func (tm *Timer) GetTimer(timer time.Time) time.Duration {
	end := time.Now()
	return end.Sub(timer)
}

func (tm *Timer) NewTimerNamed(name string) string {
	tm.lock.Lock()
	defer tm.lock.Unlock()
	tm.list[name] = time.Now()
	return name
}

func (tm *Timer) GetTimerNamed(timer string) (time.Duration, error) {
	end := time.Now()
	tm.lock.RLock()
	start, ok := tm.list[timer]
	tm.lock.RUnlock()
	if !ok {
		return time.Duration(0), errors.New("Unknown timer " + timer)
	}
	tm.lock.Lock()
	delete(tm.list, timer)
	tm.lock.Unlock()
	return end.Sub(start), nil
}

type MonitoringService interface {
	NewCounter(name string, description string) (Counter, error)
	GetCounter(name string) (Counter, bool)
	NewGauge(name string, description string) (Gauge, error)
	GetGauge(name string) (Gauge, bool)
	NewHistogram(name string, description string, buckets []float64) (Histogram, error)
	GetHistogram(name string) (Histogram, bool)
	//NewSummary(name string, description string, objectives map[float64]float64) (Summary, error)
	//GetSummary(name string) (Summary, bool)
	Start()
	Stop()
	Info() string
	Timer() *Timer
}

func ignore(err error) {
	if err != nil {
		log.Println("IGNORED", err)
	}
}
