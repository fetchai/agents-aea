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
	"net/http"
	"strconv"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type PrometheusGauge struct {
	gauge prometheus.Gauge
}

type PrometheusMonitoring struct {
	Namespace string
	Port      uint16

	running    bool
	httpServer http.Server
	//gaugeDict map[string]PrometheusGauge
	gaugeDict map[string]prometheus.Gauge
}

func NewPrometheusMonitoring(namespace string, port uint16) *PrometheusMonitoring {
	pmts := &PrometheusMonitoring{
		Namespace: namespace,
		Port:      port,
	}
	pmts.gaugeDict = map[string]prometheus.Gauge{}

	return pmts
}

func (pmts *PrometheusMonitoring) NewGauge(name string, description string) (Gauge, error) {
	gauge := promauto.NewGauge(prometheus.GaugeOpts{
		Namespace: pmts.Namespace,
		Name:      name,
		Help:      description,
	})
	pmts.gaugeDict[name] = gauge

	return gauge, nil
}

func (pmts *PrometheusMonitoring) GetGauge(name string) (Gauge, bool) {
	gauge, ok := pmts.gaugeDict[name]
	return gauge, ok
}

func (pmts *PrometheusMonitoring) Start() {
	if pmts.running {
		return
	}
	pmts.httpServer = http.Server{Addr: ":" + strconv.FormatInt(int64(pmts.Port), 10)}
	http.Handle("/metrics", promhttp.Handler())

	pmts.running = true
	pmts.httpServer.ListenAndServe()
}

func (pmts *PrometheusMonitoring) Stop() {
	pmts.httpServer.Close()
}

func (pmts *PrometheusMonitoring) Info() string {
	return "Prometheus at " + strconv.FormatInt(int64(pmts.Port), 10)
}
