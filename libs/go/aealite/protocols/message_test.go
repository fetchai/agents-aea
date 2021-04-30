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
	"testing"

	"gotest.tools/assert"
)

const (
	DialogueStarterReference   = "DialogueStarterReference"
	DialogueResponderReference = "DialogueResponderReference"
)

func TestMessage(t *testing.T) {
	message := DialogueMessage{}
	message.MessageId = int32(StartingMessageId)
	message.DialogueStarterReference = DialogueStarterReference
	message.DialogueResponderReference = DialogueResponderReference
	message.Target = int32(StartingTarget)
	message.Content = []byte(`{"performative": "request", "data": "hello"}`)

	result := DialogueMessageWrapper{}
	err := result.InitFromProtobufAndPerfofrmative(&message, "request")
	if err != nil {
		t.Fatalf("Error: %s", err.Error())
	}

	assert.Equal(t, result.messageId, StartingMessageId)
	assert.Equal(t, result.dialogueReference.dialogueStarterReference, DialogueStarterReference)
	assert.Equal(t, result.dialogueReference.dialogueResponderReference, DialogueResponderReference)
	assert.Equal(t, result.target, StartingTarget)
	assert.Equal(t, result.performative, Performative("request"))
}
