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
	observe(value float64)
}

type Summary interface {
	observe(value float64)
}

type MonitoringService interface {
	NewGauge(name string, description string) (Gauge, error)
	GetGauge(name string) (Gauge, bool)
	//NewSummary(name string, description string, ) (Summary, error)
	Start()
	Stop()
	Info() string
}
