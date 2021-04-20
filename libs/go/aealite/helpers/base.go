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

//AddFromArray adds elements to the set from an array
func (set *Set) AddFromArray(array []Generic) {
	for _, element := range array {
		set.Add(element)
	}
}

// ToArray gives an array of 'interface{}' built from the set.
func (set *Set) ToArray() []interface{} {
	keys := make([]interface{}, 0, len(set.container))
	for k := range set.container {
		keys = append(keys, k)
	}
	return keys
}

// Add adds an element.
func (set *Set) Add(element Generic) {
	set.container[element] = true
}

// Remove removes an element.
func (set *Set) Remove(element Generic) {
	delete(set.container, element)
}

// Contains checks an element is in the set.
func (set *Set) Contains(element Generic) bool {
	val, ok := set.container[element]
	return val && ok
}

// Size returns the size of the set.
func (set *Set) Size() int {
	return len(set.container)
}

// Copy instantiate a new copy of the set.
func (set *Set) Copy() Set {
	newSet := NewSet()
	for element := range set.container {
		newSet.Add(element)
	}
	return newSet
}

// Difference computes the difference from set 1 to set 2
func Difference(set1 Set, set2 Set) Set {
	result := set1.Copy()
	for element := range set2.container {
		result.Remove(element)
	}
	return result
}

// NewSet returns a new set.
func NewSet() Set {
	result := Set{}
	result.container = make(map[Generic]bool)
	return result
}

// NewSetFromArray returns a new set initialized from an array.
func NewSetFromArray(array []interface{}) Set {
	result := NewSet()
	result.AddFromArray(fromInterfaceToGenericArray(array))
	return result
}

func fromInterfaceToGenericArray(array []interface{}) []Generic {
	newArray := make([]Generic, len(array))
	for index, element := range array {
		newArray[index] = element
	}
	return newArray
}
