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

import (
	"testing"
)

func checkExpectedSize(t *testing.T, set *Set, expectedSize int) {
	if actualSize := set.Size(); actualSize != expectedSize {
		t.Fatalf("expected size %d, got %d", expectedSize, actualSize)
	}
}

func checkIn(t *testing.T, set *Set, element Generic) {
	if !set.Contains(element) {
		t.Fatalf("expected to find element %s, but not found it", element)
	}
}
func checkNotIn(t *testing.T, set *Set, element Generic) {
	if set.Contains(element) {
		t.Fatalf("expected to find element %s, but not found it", element)
	}
}

func TestSet(t *testing.T) {
	set := NewSet()

	element1 := "hello"
	element2 := 42
	element3 := struct {
		Name    string
		Surname string
	}{"Alan", "Turing"}

	checkNotIn(t, &set, element1)
	checkNotIn(t, &set, element2)
	checkNotIn(t, &set, element3)
	checkExpectedSize(t, &set, 0)

	set.Add(element1)
	checkIn(t, &set, element1)
	checkNotIn(t, &set, element2)
	checkNotIn(t, &set, element3)
	checkExpectedSize(t, &set, 1)

	set.Add(element2)
	set.Add(element3)
	checkIn(t, &set, element1)
	checkIn(t, &set, element2)
	checkIn(t, &set, element3)
	checkExpectedSize(t, &set, 3)

	set.Remove(element1)
	set.Remove(element2)
	set.Remove(element3)
	checkNotIn(t, &set, element1)
	checkNotIn(t, &set, element2)
	checkNotIn(t, &set, element3)
	checkExpectedSize(t, &set, 0)
}

func TestSetFromArray(t *testing.T) {
	elements := []interface{}{"hello", 42, "world", "world"}
	set := NewSetFromArray(elements)

	expectedSize := 3
	actualSize := set.Size()
	if expectedSize != actualSize {
		t.Fatalf("expected %v, found %v", expectedSize, actualSize)
	}
}
