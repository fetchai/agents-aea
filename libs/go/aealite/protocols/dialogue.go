package protocols

type Address string
type Performative []string
type SomeMessageType string

const (
	NONCE_BYTES_NB = 32
)

// type Dialogue struct {
// 	_dialogues_storage
// 	_dialogues_stats
// 	_keep_terminal_state_dialogues
// 	_message_class
// 	_dialogue_class
// 	_role_from_first_message
// 	_self_address
// 	_outgoing_messages
// 	_incoming_messages
// }

type Role string

const (
	Role1 Role = "role1"
	Role2 Role = "role2"
)

type RuleType struct {
	initialPerformative  Performative
	terminalPerformative Performative
	// validReplies
}

type MessageId int
type Target []int
type DialogueInterface interface {
	initialize(selfAddress Address, counterParty Address, role Role)
	getSelfAddress() Address
	getRole() Role
	getRules() RuleType
	getMessageClass() AbstractMessage
	isSelfInitiated() bool
	getLastIncomingMessage() AbstractMessage
	getLastOutgoingMessage() AbstractMessage
	getLastMessage() AbstractMessage
	isEmpty() bool
	counterPartyForMessage(AbstractMessage) bool
	isMessageBySelf(AbstractMessage) bool
	isMessageByOther(AbstractMessage) bool
	getMessage(MessageId) AbstractMessage
	hasMessageId(MessageId) bool
	update(AbstractMessage)
	isBelongingToADialogue(AbstractMessage) bool
	reply(Performative, Target) AbstractMessage
	validateNextMessage(AbstractMessage) (bool, AbstractMessage)
	basicValidations(AbstractMessage) (bool, AbstractMessage)
	basicValidationInitialMessage(AbstractMessage) (bool, AbstractMessage)
	basicValidationNonInitialMessage(AbstractMessage) (bool, AbstractMessage)
	validateMessageTarget(AbstractMessage) string
	validateMessageId(AbstractMessage) string
	getMessageById(MessageId) AbstractMessage
	getOutgoingNextMessageId() int
	getIncomingNextMessageId() int
	updateDIalogueLabel(DialogueLabel)
	customValidation(AbstractMessage) (bool, string)
	getStringRepresentation() string
}

type DialoguesInterface interface {
	// initialize(dialogue DialogueLabel, endStates FrozenSet, _message_class InitialMessage, dialogueClass Dialogue, roleFromFirstMessage Role, keepTerminalStateDialogues bool)
	isKeepDIaloguesInTerminalState() bool
	selfAddress() Address
	messageClass() AbstractMessage
	dialogueClass() Dialogue
	getDialoguesWithCounterParty(counterPArty Address) []Dialogue
	isMessageBySelf(AbstractMessage) bool
	isMessageByOther(AbstractMessage) bool
	counterPartyFromMessage(AbstractMessage) Address
	newSelfInitiatedDialogueReference() [2]string
	create(counterParty Address, performative Performative, message SomeMessageType) (AbstractMessage, Dialogue)
	createWithMessage(counterParty Address, intitialMessage AbstractMessage) Dialogue
	createDialogue(counterParty Address, intitialMessage AbstractMessage) Dialogue
	update(AbstractMessage) Dialogue
	completeDialogueReference(AbstractMessage)
	getDialogue(AbstractMessage) Dialogue
	getLatestLabel(DialogueLabel) DialogueLabel
	getDialogueFromLabel(DialogueLabel) Dialogue
	createSelfInitiated(dialogueOpponentAddress Address, dialogueReference [2]string, role Role) Dialogue
	createOpponentInitiated(dialogueOpponentAddress Address, dialogueReference [2]string, role Role) Dialogue
	createInternal(incompleteDialogueLabel DialogueLabel, role Role, completeDialogueLabel DialogueLabel) Dialogue
	generateDialogueNonce() string
	setUpDialogueStorage()
	tearDownDialogueStorage()
}

type AbstractMessageInterface interface {
	initialize(diaglogReference [2]string, messagId int, target Target, performative Performative)
	validPerformatives() []string
	hasSender() bool
	sender() Address
	hasTo() bool
	to() Address
	dialogueReference() [2]string
	messageId() MessageId
	performative() Performative
	target() int
	equal(AbstractMessage) bool
}

type DialogueLabel struct {
	dialogueReference       [2]string
	dialogueOpponentAddress Address
	dialogueStarterAddress  Address
}

type Dialogue struct {
	dialogueLabel    DialogueLabel
	dialogueMessage  *AbstractMessage
	selfAddress      Address
	outGoingMessages []MessageId
	GoingMessages    []MessageId
	rules            RuleType
}
type AbstractMessage struct {
	dialogueReference [2]string
	message_id        int
	target            int
	performative      []string
	message           SomeMessageType
	to                Address
	sender            Address
}

// var dialogueStorage map[Address][]DialogueLabel

// func create(selfAddress Address, counterParty Address, performative Performative, message SomeMessageType) *Dialogue {

// 	if selfAddress == counterParty {
// 		fmt.Println("sender and receiver cannot be the same")
// 	}

// 	dialogueStorage = make(map[Address][]DialogueLabel)

// 	intitialMessage := &InitialMessage{
// 		message_id:   0,
// 		target:       1,
// 		performative: performative,
// 		message:      message,
// 		to:           counterParty,
// 		sender:       selfAddress,
// 	}
// 	intitialMessage.dialogueReference[0] = generateDialogueNonce()
// 	intitialMessage.dialogueReference[1] = ""

// 	// process dialogue creation
// 	dialogue := intitialMessage.createDialogue()

// 	return dialogue
// }

// func (dialogue *Dialogue) update(selfAddress Address) {

// 	if dialogue.dialogueMessage.sender != "" || dialogue.dialogueMessage.to != "" {
// 		fmt.Println("Error : dialogue sender & receiver should not be empty")
// 	}

// 	if selfAddress != dialogue.selfAddress {
// 		fmt.Println("Error : Sender should be dialogue initiator")
// 	}

// 	if dialogue.dialogueMessage.sender == dialogue.dialogueMessage.to {
// 		fmt.Println("Error : Sender and receiver cannot be the same")
// 	}

// 	// check if diaglogReference is invalid
// 	invalid_label := dialogue.dialogueMessage.dialogueReference[0] != "" || dialogue.dialogueMessage.dialogueReference[1] != ""

// 	// check if dialog is new
// 	new_dialogue := dialogue.dialogueMessage.dialogueReference[0] != "" && dialogue.dialogueMessage.dialogueReference[1] == "" && dialogue.dialogueMessage.message_id == 1

// 	// check if dialogue is incomplete and having non-initial message
// 	incompleteLableAndNonInitialMessage := dialogue.dialogueMessage.dialogueReference[0] != "" && dialogue.dialogueMessage.dialogueReference[1] == "" && dialogue.dialogueMessage.message_id != 0 || dialogue.dialogueMessage.message_id != 1

// 	if invalid_label {
// 		// dialogue = empty
// 		return
// 	} else if new_dialogue {
// 		dialogue.createOpponentInitiated()
// 	} else if incompleteLableAndNonInitialMessage {
// 		dialogue.getDialogue()
// 	} else {
// 		dialogue.completeDialogurReference()
// 		dialogue.dialogueMessage.getDialogue()
// 	}
// 	if dialogue != nil {
// 		dialogue.internalUpdate()
// 		// if errors remove from storage
// 	}
// }

// func (dialogue *Dialogue) createOpponentInitiated() {
// 	if dialogue.dialogueMessage.dialogueReference[0] != "" && dialogue.dialogueMessage.dialogueReference[1] == "" {
// 		fmt.Println("Cannot initiate dialogue with preassigned dialogue responder")
// 	}
// 	dialogue.dialogueMessage.dialogueReference[0] = generateDialogueNonce()
// 	dialogue.dialogueMessage.createDialogue()
// }

// func (dialogue *Dialogue) getDialogue() {
// 	// self_inititalted_dialogue_label
// 	self_inititiated_dialogue_label := &DialogueLabel{
// 		dialogueReference:       dialogue.dialogueLabel.dialogueReference,
// 		dialogueOpponentAddress: dialogue.dialogueMessage.to,
// 		dialogueStarterAddress:  dialogue.selfAddress,
// 	}
// 	// other inititalted_dialogue label
// 	other_inititiated_dialogue_label := &DialogueLabel{
// 		dialogueReference:       dialogue.dialogueLabel.dialogueReference,
// 		dialogueOpponentAddress: dialogue.dialogueMessage.to,
// 		dialogueStarterAddress:  dialogue.dialogueMessage.to,
// 	}
// 	// get latest self initiated dialogur label
// 	pair := dialogue.dialogueMessage.sender + dialogue.dialogueMessage.to
// 	if len(dialogueStorage[pair]) > 0 {
// 		index := len(dialogueStorage[pair])
// 		dialogueStorage[pair][index]
// 	}

// 	// get other initiated dialogue label
// 	// get delf initiated dialogue from label
// 	// get other initiated dialogue from label
// }

// func (data *InitialMessage) createDialogue() *Dialogue {

// 	// TODO
// 	// define dialog ROLE for dialog initiator

// 	incompleteDialogueLabel := data.checkAndProcessLabels()
// 	pair := data.sender + data.to
// 	if len(dialogueStorage[pair]) > 0 {
// 		for _, dialogue := range dialogueStorage[pair] {
// 			if incompleteDialogueLabel == dialogue {
// 				fmt.Println("Error : incomplete dialogue label already present in storage")
// 				return nil
// 			}
// 		}
// 	}
// 	dialogueLabel := incompleteDialogueLabel

// 	// TODO
// 	// initialize completeLabel
// 	// if completeLabel != nil {
// 	// 	dialogueLabel = completeDialogueLabel
// 	// }

// 	if len(dialogueStorage[data.sender+data.to]) > 0 {
// 		for _, dialogue := range dialogueStorage[data.sender+data.to] {
// 			if dialogueLabel == dialogue {
// 				fmt.Println("Error : Dialogue label already present in storage")
// 				return nil
// 			}
// 		}
// 	}

// 	dialogue := &Dialogue{
// 		dialogueLabel:   dialogueLabel,
// 		dialogueMessage: data,
// 		selfAddress:     data.sender,
// 	}

// 	return dialogue

// }

// func (data *InitialMessage) checkAndProcessLabels() DialogueLabel {
// 	if !(data.dialogueReference[0] != "" && data.dialogueReference[1] == "") {
// 		fmt.Println("Error : Reference address label already exists")
// 	}
// 	return DialogueLabel{
// 		dialogueReference:       data.dialogueReference,
// 		dialogueOpponentAddress: data.to,
// 		dialogueStarterAddress:  data.sender,
// 	}
// }

// func generateDialogueNonce() string {
// 	hexValue := randomHex(NONCE_BYTES_NB)
// 	return hexValue
// }

// func randomHex(n int) string {
// 	bytes := make([]byte, n)
// 	if _, err := rand.Read(bytes); err != nil {
// 		return ""
// 	}
// 	return hex.EncodeToString(bytes)
// }
