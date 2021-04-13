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

package helpers

// Generic a generic type (every type implements at least zero methods).
type Generic interface{}

/*
Set implementation of a set of generic types.
It uses the built-in 'map' type, which is
based on hash tables:
    https://golang.org/src/runtime/map.go
This guarantees (amortized) constant-time complexity
for addition, deletion, and lookup.
*/
type Set struct {
	container map[Generic]bool // container: a private container.
}

// Init initialize a set.
func (set *Set) Init() {
	set.container = make(map[Generic]bool)
}

func (set *Set) AddFromArray(array []Generic) {
	for _, element := range array {
		set.Add(element)
	}
}

// Add add an element.
func (set *Set) Add(element Generic) {
	set.container[element] = true
}

// Remove remove an element.
func (set *Set) Remove(element Generic) {
	delete(set.container, element)
}

// In check an element is in the set.
func (set *Set) In(element Generic) bool {
	val, ok := set.container[element]
	return val && ok
}

// Size return the size of the set.
func (set *Set) Size() int {
	return len(set.container)
}
