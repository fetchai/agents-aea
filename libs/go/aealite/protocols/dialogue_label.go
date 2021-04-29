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
	"bytes"
	"encoding/json"
	"fmt"
	"strings"
)

type DialogueReference struct {
	dialogueStarterReference   string
	dialogueResponderReference string
}

func (dialogueReference *DialogueReference) DialogueStarterReference() string {
	return dialogueReference.dialogueStarterReference
}
func (dialogueReference *DialogueReference) DialogueResponderReference() string {
	return dialogueReference.dialogueResponderReference
}

type DialogueLabel struct {
	dialogueReference       DialogueReference
	dialogueOpponentAddress Address
	dialogueStarterAddress  Address
}

// DialogueReference Get the dialogue reference.
func (dialogueLabel *DialogueLabel) DialogueReference() DialogueReference {
	return dialogueLabel.dialogueReference
}

// DialogueStarterReference Get the dialogue starter reference.
func (dialogueLabel *DialogueLabel) DialogueStarterReference() string {
	return dialogueLabel.dialogueReference.DialogueStarterReference()
}

// DialogueResponderReference Get the dialogue responder reference.
func (dialogueLabel *DialogueLabel) DialogueResponderReference() string {
	return dialogueLabel.dialogueReference.DialogueResponderReference()
}

// DialogueOpponentAddress Get the dialogue opponent address.
func (dialogueLabel *DialogueLabel) DialogueOpponentAddress() Address {
	return dialogueLabel.dialogueOpponentAddress
}

// DialogueStarterAddress Get the dialogue starter address.
func (dialogueLabel *DialogueLabel) DialogueStarterAddress() Address {
	return dialogueLabel.dialogueStarterAddress
}

// IncompleteVersion Get the incomplete version of the label.
func (dialogueLabel *DialogueLabel) IncompleteVersion() DialogueLabel {
	return DialogueLabel{
		DialogueReference{dialogueLabel.DialogueStarterReference(), UnassignedDialogueReference},
		dialogueLabel.dialogueOpponentAddress,
		dialogueLabel.dialogueStarterAddress,
	}
}

// MarshalJSON custom DialogueLabel JSON serializer
func (dialogueLabel DialogueLabel) MarshalJSON() ([]byte, error) {
	data := map[string]string{
		"dialogue_starter_reference":   dialogueLabel.DialogueStarterReference(),
		"dialogue_responder_reference": dialogueLabel.DialogueResponderReference(),
		"dialogue_opponent_addr":       string(dialogueLabel.DialogueOpponentAddress()),
		"dialogue_starter_addr":        string(dialogueLabel.DialogueStarterAddress()),
	}
	buffer := bytes.NewBufferString("{")
	for key, value := range data {
		buffer.WriteString(fmt.Sprintf("\"%s\": \"%s\",", key, value))
	}
	buffer.Truncate(buffer.Len() - 1)
	buffer.WriteString("}")
	return buffer.Bytes(), nil
}

// UnmarshalJSON custom DialogueLabel JSON deserializer
func (dialogueLabel *DialogueLabel) UnmarshalJSON(b []byte) error {
	var data map[string]string
	err := json.Unmarshal(b, &data)
	if err != nil {
		return err
	}
	starterReference := data["dialogue_starter_reference"]
	responderReference := data["dialogue_responder_reference"]
	dialogueLabel.dialogueReference = DialogueReference{starterReference, responderReference}
	dialogueLabel.dialogueOpponentAddress = Address(data["dialogue_opponent_addr"])
	dialogueLabel.dialogueStarterAddress = Address(data["dialogue_starter_addr"])
	return nil
}

// String transform DialogueLabel to its string representation
func (dialogueLabel *DialogueLabel) String() string {
	return strings.Join([]string{dialogueLabel.DialogueStarterReference(),
		dialogueLabel.DialogueResponderReference(),
		string(dialogueLabel.dialogueOpponentAddress),
		string(dialogueLabel.dialogueStarterAddress)}, DialogueLabelStringSeparator)
}

// FromString update a DialogueLabel from a string representation
func (dialogueLabel *DialogueLabel) FromString(s string) error {
	result := strings.Split(s, DialogueLabelStringSeparator)
	if length := len(result); length != 4 {
		return fmt.Errorf("expected exactly 4 parts, got %d", length)
	}
	dialogueLabel.dialogueReference = DialogueReference{result[0], result[1]}
	dialogueLabel.dialogueOpponentAddress = Address(result[2])
	dialogueLabel.dialogueStarterAddress = Address(result[3])
	return nil
}
