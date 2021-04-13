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

package protocols

import (
	"encoding/json"
	"gotest.tools/assert"
	"testing"
)

// get a default dialogue label for testing purposes
func getTestDialogueLabel() DialogueLabel {
	return DialogueLabel{
		DialogueReference{starterReference, responderReference},
		counterPartyAddress,
		senderAddress,
	}
}

// Test DialogueLabel initialization and getters
func TestDialogueLabelGetters(t *testing.T) {
	starterReference := "starterReference"
	responderReference := "responderReference"
	dialogueReference := DialogueReference{starterReference, responderReference}
	label := DialogueLabel{
		dialogueReference,
		counterPartyAddress,
		senderAddress,
	}

	assert.Equal(t, label.DialogueOpponentAddress(), counterPartyAddress)
	assert.Equal(t, label.DialogueStarterAddress(), senderAddress)
	assert.Equal(t, label.DialogueStarterReference(), starterReference)
	assert.Equal(t, label.DialogueResponderReference(), responderReference)
	assert.Equal(t, label.DialogueReference(), dialogueReference)

}

// Test getIncompleteVersion function
func TestGetIncompleteVersion(t *testing.T) {
	label := getTestDialogueLabel()
	actualIncompleteVersion := label.IncompleteVersion()
	expectedIncompleteVersion := DialogueLabel{
		DialogueReference{label.DialogueStarterReference(), UnassignedDialogueReference},
		label.DialogueOpponentAddress(),
		label.DialogueStarterAddress(),
	}

	assert.Equal(
		t,
		actualIncompleteVersion,
		expectedIncompleteVersion,
		"getIncompleteVersion gave unexpected result.",
	)
}

// Test marshalling and unmarshalling
func TestMarshalAndUnmarshal(t *testing.T) {
	label := getTestDialogueLabel()

	data, err := json.Marshal(label)
	if err != nil {
		t.Fatalf("DialogueLabel JSON marshalling failed with error: %s", err.Error())
	}

	result := DialogueLabel{}
	err = json.Unmarshal(data, &result)
	if err != nil {
		t.Fatalf("DialogueLabel JSON unmarshalling failed with error: %s", err.Error())
	}
	assert.Equal(
		t,
		result,
		label,
		"the DialogueLabel parsed from JSON is not the same of the original one.",
	)
}

// Test ToString and FromString methods.
func TestToStringAndFromString(t *testing.T) {
	label := getTestDialogueLabel()
	result := DialogueLabel{}
	err := result.FromString(label.String())
	if err != nil {
		t.Fatalf("Cannot parse string: %s", err.Error())
	}
	if label != result {
		t.Fatal("the DialogueLabel parsed from string is not the same of the original one.")
	}
}
