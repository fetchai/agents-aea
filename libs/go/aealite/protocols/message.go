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
	"errors"
	"log"

	proto "google.golang.org/protobuf/proto"
	protoreflect "google.golang.org/protobuf/reflect/protoreflect"
)

type MessageId int
type Address string
type Performative string

type ProtocolMessageInterface interface {
	Sender() Address
	SetSender(Address) error
	To() Address
	SetTo(Address) error
	MessageId() MessageId
	DialogueReference() DialogueReference
	Target() MessageId
	Performative() Performative
	Body() map[string]interface{}
	HasSender() bool
	HasTo() bool
	GetField(name string) interface{}
	//ValidPerformatives() []Performative TODO temporarily removed
}

type DialogueMessageWrapper struct {
	to                Address
	sender            Address
	dialogueReference DialogueReference
	messageId         MessageId
	target            MessageId
	performative      Performative
	body              map[string]interface{}
	//validPerformatives helpers.Set TODO understand how to set this
}

// InitFromProtobufAndPerformative initializes a message from a DialogueMessage protobuf message and a performative.
//  It unpacks 'message id', 'target' and 'dialogue reference'; moreover,
//  it decodes the content as a JSON object.
//  Returns error if:
//  - the JSON decoding fails
//  - the body does not contain the 'performative'
//  It performs side-effect on the method receiver.
func (message *DialogueMessageWrapper) InitFromProtobufAndPerfofrmative(
	dialogueMessage *DialogueMessage,
	performativeStr string,
) error {
	message.messageId = MessageId(dialogueMessage.MessageId)
	message.target = MessageId(dialogueMessage.Target)
	message.dialogueReference = DialogueReference{
		dialogueMessage.DialogueStarterReference,
		dialogueMessage.DialogueResponderReference,
	}
	message.target = MessageId(dialogueMessage.Target)
	message.performative = Performative(performativeStr)
	return nil
}

func (message *DialogueMessageWrapper) Sender() Address {
	return message.sender
}

func (message *DialogueMessageWrapper) SetSender(newAddress Address) error {
	if message.sender != "" {
		return errors.New("'sender' field already set")
	}
	message.sender = newAddress
	return nil
}

func (message *DialogueMessageWrapper) To() Address {
	return message.to
}

func (message *DialogueMessageWrapper) SetTo(newAddress Address) error {
	if message.to != "" {
		return errors.New("'to' field already set")
	}
	message.to = newAddress
	return nil
}

func (message *DialogueMessageWrapper) MessageId() MessageId {
	return message.messageId
}

func (message *DialogueMessageWrapper) DialogueReference() DialogueReference {
	return message.dialogueReference
}

func (message *DialogueMessageWrapper) Target() MessageId {
	return message.target
}

func (message *DialogueMessageWrapper) Performative() Performative {
	return message.performative
}

func (message *DialogueMessageWrapper) Body() map[string]interface{} {
	return message.body
}

func (message *DialogueMessageWrapper) HasSender() bool {
	return message.sender != ""
}

func (message *DialogueMessageWrapper) HasTo() bool {
	return message.sender != ""
}

// GetField returns the value of the field associated with the name
//  provided in input. If not present, then nil is returned. As we
//  don't know the type, the callre has to do a type assertion
//  in order to process the returned value.
func (message *DialogueMessageWrapper) GetField(name string) interface{} {
	return message.body[name]
}

func GetPerformative(message MessageInterface) (string, error) {
	performative := ""
	m := message.ProtoReflect()
	m.Range(func(fd protoreflect.FieldDescriptor, v protoreflect.Value) bool {
		performative = fd.JSONName()
		return false
	})

	if performative == "" {
		return performative, errors.New("can not determine performative")
	}
	return performative, nil
}

type MessageInterface interface {
	ProtoReflect() protoreflect.Message
}

func GetDialogueMessageWrappedAndSetContentFromEnvelope(
	envelope *Envelope,
	content_message MessageInterface,
) (*DialogueMessageWrapper, error) {
	data := envelope.GetMessage()
	message := &Message{}
	err := proto.Unmarshal(data, message)
	if err != nil {
		log.Printf("can not unmarshal message: %s", err)
		return nil, err
	}
	dialogue_message := message.GetDialogueMessage()

	err = proto.Unmarshal(dialogue_message.GetContent(), content_message)
	if err != nil {
		log.Printf("err on decode message content: %s", err)
		return nil, err
	}

	performative, err := GetPerformative(content_message)
	if err != nil {
		log.Printf("can not get performative: %s", err)
		return nil, err
	}

	dialogue_message_wrapper := DialogueMessageWrapper{}
	err = dialogue_message_wrapper.InitFromProtobufAndPerfofrmative(dialogue_message, performative)
	if err != nil {
		log.Printf("can not init dialogue wrapper: %s", err)
		return nil, err
	}
	dialogue_message_wrapper.SetSender(Address(envelope.GetSender()))
	dialogue_message_wrapper.SetTo(Address(envelope.GetTo()))

	return &dialogue_message_wrapper, nil
}


func MakeResponseEnvelope(
	wrappedMsgDialogue ProtocolMessageInterface,
	protocolID string,
	content []byte,
) (*Envelope, error) {
	dialogueRef := wrappedMsgDialogue.DialogueReference()

	message := Message{
		Message: &Message_DialogueMessage{
			DialogueMessage: &DialogueMessage{
				MessageId:                  int32(wrappedMsgDialogue.MessageId()),
				DialogueStarterReference:   dialogueRef.DialogueStarterReference(),
				DialogueResponderReference: dialogueRef.DialogueResponderReference(),
				Target:                     int32(wrappedMsgDialogue.Target()),
				Content:                    content,
			},
		},
	}

	out, err := proto.Marshal(&message)
	if err != nil {
		log.Print("marshal dialogue messge failed")
		return nil, err
	}
	env := &Envelope{
		To:         string(wrappedMsgDialogue.To()),
		Sender:     string(wrappedMsgDialogue.Sender()),
		ProtocolId: protocolID,
		Message:    out,
		Uri:        "",
	}
	return env, nil
}
