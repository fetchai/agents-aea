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
)

type MessageId int
type Address string
type Performative string

type AbstractMessage interface {
	Sender() Address
	SetSender(Address)
	To() Address
	SetTo(Address)
	MessageId() MessageId
	DialogueReference() DialogueReference
	Target() MessageId
	Performative() Performative
	Body() map[string]interface{}
	ValidPerformatives() []string
	HasSender() bool
	HasTo() bool
	GetField(name string) interface{}
}

type DialogueMessageWrapper struct {
	to                Address
	sender            Address
	dialogueReference DialogueReference
	messageId         MessageId
	target            MessageId
	body              map[string]interface{}
}

func (message *DialogueMessageWrapper) InitFromProtobuf(dialogueMessage *DialogueMessage) error {
	message.messageId = MessageId(dialogueMessage.MessageId)
	message.target = MessageId(dialogueMessage.Target)
	message.dialogueReference = DialogueReference{
		dialogueMessage.DialogueStarterReference,
		dialogueMessage.DialogueResponderReference,
	}

	content := dialogueMessage.Content
	var data map[string]interface{}
	err := json.Unmarshal(content, &data)
	if err != nil {
		return err
	}
	message.body = data
	return nil
}

func (message DialogueMessageWrapper) HasSender() bool {
	return message.sender != ""
}

func (message DialogueMessageWrapper) HasTo() bool {
	return message.sender != ""
}

//func InitializeMessage(
//	counterParty Address,
//	selfAddress Address,
//	performative Performative,
//	content []byte,
//	ref [2]string,
//	messageId MessageId,
//	target MessageId,
//) AbstractMessage {
//	var reference [2]string
//	if ref[0] != "" || ref[1] != "" {
//		reference = ref
//	} else {
//		reference = [2]string{
//			generateDialogueNonce(), "",
//		}
//	}
//	initialMessage := AbstractMessage{
//		dialogueReference: reference,
//		messageId:         messageId,
//		target:            target,
//		performative:      performative,
//		to:                counterParty,
//		sender:            selfAddress,
//		message:           content,
//	}
//	return initialMessage
//}
