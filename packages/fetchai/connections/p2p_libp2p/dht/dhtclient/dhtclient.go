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

// Package dhtclient provides implementation of a lightweight Agent Communication Network
// node. It doesn't particiapate in network maintenance. It doesn't require a public
// address as well, as it relays on a DHTPeer to communicate with other peers
package dhtclient

import (
	"context"
	"log"
	"math/rand"
	"strings"
	"time"

	"github.com/pkg/errors"

	"github.com/rs/zerolog"
	"google.golang.org/protobuf/proto"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p-core/crypto"
	"github.com/libp2p/go-libp2p-core/host"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/libp2p/go-libp2p-core/protocol"
	"github.com/multiformats/go-multiaddr"

	peerstore "github.com/libp2p/go-libp2p-core/peerstore"
	kaddht "github.com/libp2p/go-libp2p-kad-dht"
	routedhost "github.com/libp2p/go-libp2p/p2p/host/routed"

	aea "libp2p_node/aea"
	"libp2p_node/dht/dhtnode"
	utils "libp2p_node/utils"
)

func ignore(err error) {
	if err != nil {
		log.Println("IGNORED", err)
	}
}

const (
	newStreamTimeoutRelayPeer = 5 * 60 * time.Second // includes peer restart
	newStreamTimeout          = 1 * 60 * time.Second // doesn't include peer restart
	bootstrapTimeout          = 1 * 60 * time.Second // doesn't include peer restart
	sleepTimeDefaultDuration  = 100 * time.Millisecond
	sleepTimeIncreaseMFactor  = 2 // multiplicative increase
)

// Notifee Handle DHTClient network events
type Notifee struct {
	myRelayPeer peer.AddrInfo
	myHost      host.Host
	logger      zerolog.Logger
	closing     chan struct{}
}

// Listen called when network starts listening on an addr
func (notifee *Notifee) Listen(network.Network, multiaddr.Multiaddr) {}

// ListenClose called when network stops listening on an addr
func (notifee *Notifee) ListenClose(network.Network, multiaddr.Multiaddr) {}

// Connected called when a connection opened
func (notifee *Notifee) Connected(network.Network, network.Conn) {}

// Disconnected called when a connection closed
func (notifee *Notifee) Disconnected(net network.Network, conn network.Conn) {

	pinfo := notifee.myRelayPeer
	if conn.RemotePeer().Pretty() != pinfo.ID.Pretty() {
		return
	}

	notifee.myHost.Peerstore().AddAddrs(pinfo.ID, pinfo.Addrs, peerstore.PermanentAddrTTL)
	for {
		var err error
		select {
		case _, open := <-notifee.closing:
			if !open {
				return
			}
		default:
			notifee.logger.Warn().Msgf("Lost connection to relay peer %s, reconnecting...", pinfo.ID.Pretty())
			if err = notifee.myHost.Connect(context.Background(), pinfo); err == nil {
				break
			}
			time.Sleep(1 * time.Second)

		}
		if err == nil {
			break
		}
	}
	notifee.logger.Info().Msgf("Connection to relay peer %s reestablished", pinfo.ID.Pretty())
}

// OpenedStream called when a stream opened
func (notifee *Notifee) OpenedStream(network.Network, network.Stream) {}

// ClosedStream called when a stream closed
func (notifee *Notifee) ClosedStream(network.Network, network.Stream) {}

// DHTClient A restricted libp2p node for the Agents Communication Network
// It use a `DHTPeer` to communicate with other peers.
type DHTClient struct {
	bootstrapPeers []peer.AddrInfo
	relayPeer      peer.ID
	key            crypto.PrivKey
	publicKey      crypto.PubKey

	dht        *kaddht.IpfsDHT
	routedHost *routedhost.RoutedHost

	myAgentAddress  string
	myAgentRecord   *dhtnode.AgentRecord
	myAgentReady    func() bool
	processEnvelope func(*aea.Envelope) error

	closing chan struct{}
	logger  zerolog.Logger
}

// New creates a new DHTClient
func New(opts ...Option) (*DHTClient, error) {
	var err error
	dhtClient := &DHTClient{}

	for _, opt := range opts {
		if err := opt(dhtClient); err != nil {
			return nil, err
		}
	}

	dhtClient.closing = make(chan struct{})

	/* check correct configuration */

	// private key
	if dhtClient.key == nil {
		return nil, errors.New("private key must be provided")
	}

	// agent address is mandatory
	if dhtClient.myAgentAddress == "" {
		return nil, errors.New("missing agent address")
	}

	// agent record is mandatory
	if dhtClient.myAgentRecord == nil {
		return nil, errors.New("missing agent record")
	}

	// check if the PoR is delivered for my public  key
	myPublicKey, err := utils.FetchAIPublicKeyFromPubKey(dhtClient.publicKey)
	status, errPoR := dhtnode.IsValidProofOfRepresentation(
		dhtClient.myAgentRecord,
		dhtClient.myAgentRecord.Address,
		myPublicKey,
	)
	if err != nil || errPoR != nil || status.Code != dhtnode.Status_SUCCESS {
		msg := "Invalid AgentRecord"
		if err != nil {
			msg += " - " + err.Error()
		}
		if errPoR != nil {
			msg += " - " + errPoR.Error()
		}
		return nil, errors.New(msg)
	}

	// bootsrap peers
	if len(dhtClient.bootstrapPeers) < 1 {
		return nil, errors.New("at least one boostrap peer should be provided")
	}

	// select a relay node randomly from entry peers
	rand.Seed(time.Now().Unix())
	index := rand.Intn(len(dhtClient.bootstrapPeers))
	dhtClient.relayPeer = dhtClient.bootstrapPeers[index].ID

	dhtClient.setupLogger()
	_, _, linfo, ldebug := dhtClient.getLoggers()
	linfo().Msg("INFO Using as relay")

	/* setup libp2p node */
	ctx := context.Background()

	// libp2p options
	libp2pOpts := []libp2p.Option{
		libp2p.ListenAddrs(),
		libp2p.Identity(dhtClient.key),
		libp2p.DefaultTransports,
		libp2p.DefaultMuxers,
		libp2p.DefaultSecurity,
		libp2p.NATPortMap(),
		libp2p.EnableNATService(),
		libp2p.EnableRelay(),
	}

	// create a basic host
	basicHost, err := libp2p.New(ctx, libp2pOpts...)
	if err != nil {
		return nil, err
	}

	// create the dht
	dhtClient.dht, err = kaddht.New(ctx, basicHost, kaddht.Mode(kaddht.ModeClient))
	if err != nil {
		return nil, err
	}

	// make the routed host
	dhtClient.routedHost = routedhost.Wrap(basicHost, dhtClient.dht)
	dhtClient.setupLogger()

	// connect to the booststrap nodes
	err = dhtClient.bootstrapLoopUntilTimeout()
	if err != nil {
		dhtClient.Close()
		return nil, err
	}

	// bootstrap the host
	err = dhtClient.dht.Bootstrap(ctx)
	if err != nil {
		dhtClient.Close()
		return nil, err
	}

	// register my address to relay peer
	err = dhtClient.registerAgentAddress()
	if err != nil {
		dhtClient.Close()
		return nil, err
	}

	dhtClient.routedHost.Network().Notify(&Notifee{
		myRelayPeer: dhtClient.bootstrapPeers[index],
		myHost:      dhtClient.routedHost,
		logger:      dhtClient.logger,
		closing:     dhtClient.closing,
	})

	/* setup DHTClient message handlers */

	// aea address lookup
	ldebug().Msg("DEBUG Setting /aea-address/0.1.0 stream...")
	dhtClient.routedHost.SetStreamHandler(dhtnode.AeaAddressStream,
		dhtClient.handleAeaAddressStream)

	// incoming envelopes stream
	ldebug().Msg("DEBUG Setting /aea/0.1.0 stream...")
	dhtClient.routedHost.SetStreamHandler(dhtnode.AeaEnvelopeStream,
		dhtClient.handleAeaEnvelopeStream)

	return dhtClient, nil
}

func (dhtClient *DHTClient) bootstrapLoopUntilTimeout() error {
	lerror, _, _, _ := dhtClient.getLoggers()
	ctx, cancel := context.WithTimeout(context.Background(), bootstrapTimeout)
	defer cancel()
	err := utils.BootstrapConnect(
		ctx,
		dhtClient.routedHost,
		dhtClient.dht,
		dhtClient.bootstrapPeers,
	)
	sleepTime := sleepTimeDefaultDuration
	for err != nil {
		lerror(err).
			Str("op", "bootstrap").
			Msgf("couldn't open stream to bootstrap peer, retrying in %s", sleepTime)
		select {
		default:
			time.Sleep(sleepTime)
			sleepTime = sleepTime * sleepTimeIncreaseMFactor
			err = utils.BootstrapConnect(
				ctx,
				dhtClient.routedHost,
				dhtClient.dht,
				dhtClient.bootstrapPeers,
			)
		case <-ctx.Done():
			sleepTime = 0
			break
		}
		if sleepTime == 0 {
			break
		}
	}
	return err
}

func (dhtClient *DHTClient) newStreamLoopUntilTimeout(
	peerID peer.ID,
	streamType protocol.ID,
	timeout time.Duration,
) (network.Stream, error) {
	lerror, _, _, _ := dhtClient.getLoggers()
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	stream, err := dhtClient.routedHost.NewStream(ctx, peerID, streamType)
	sleepTime := sleepTimeDefaultDuration
	disconnected := false
	for err != nil {
		disconnected = true
		lerror(err).
			Str("op", "route").
			Msgf("couldn't open stream to peer %s, retrying in %s", peerID.Pretty(), sleepTime)
		select {
		default:
			time.Sleep(sleepTime)
			sleepTime = sleepTime * sleepTimeIncreaseMFactor
			stream, err = dhtClient.routedHost.NewStream(ctx, peerID, streamType)
		case <-ctx.Done():
			sleepTime = 0
			break
		}
		if sleepTime == 0 {
			break
		}
	}
	// register again in case of disconnection
	if disconnected {
		err = dhtClient.registerAgentAddress()
	}
	return stream, err
}

func (dhtClient *DHTClient) setupLogger() {
	fields := map[string]string{
		"package": "DHTClient",
		"relayid": dhtClient.relayPeer.Pretty(),
	}
	if dhtClient.routedHost != nil {
		fields["peerid"] = dhtClient.routedHost.ID().Pretty()
	}
	dhtClient.logger = utils.NewDefaultLoggerWithFields(fields)
}

func (dhtClient *DHTClient) getLoggers() (func(error) *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event, func() *zerolog.Event) {
	ldebug := dhtClient.logger.Debug
	linfo := dhtClient.logger.Info
	lwarn := dhtClient.logger.Warn
	lerror := func(err error) *zerolog.Event {
		if err == nil {
			return dhtClient.logger.Error().Str("err", "nil")
		}
		return dhtClient.logger.Error().Str("err", err.Error())
	}

	return lerror, lwarn, linfo, ldebug
}

// Close stops the DHTClient
func (dhtClient *DHTClient) Close() []error {
	var err error
	var status []error

	_, _, linfo, _ := dhtClient.getLoggers()

	linfo().Msg("Stopping DHTClient...")
	close(dhtClient.closing)

	errappend := func(err error) {
		if err != nil {
			status = append(status, err)
		}
	}

	err = dhtClient.dht.Close()
	errappend(err)
	err = dhtClient.routedHost.Close()
	errappend(err)

	return status
}

// MultiAddr always return empty string
func (dhtClient *DHTClient) MultiAddr() string {
	return ""
}

// RouteEnvelope to its destination
func (dhtClient *DHTClient) RouteEnvelope(envel *aea.Envelope) error {
	lerror, lwarn, _, ldebug := dhtClient.getLoggers()

	//
	if envel.Sender != dhtClient.myAgentAddress {
		err := errors.New("Sender (" + envel.Sender + ") must match registered address")
		lerror(err).Str("addr", dhtClient.myAgentAddress).
			Msgf("while routing envelope")
		return err
	}

	target := envel.To

	// TODO(LR) check if the record is valid
	if target == dhtClient.myAgentAddress {
		ldebug().
			Str("op", "route").
			Str("target", target).
			Msg("envelope destinated to my local agent...")
		for !dhtClient.myAgentReady() {
			ldebug().
				Str("op", "route").
				Str("target", target).
				Msg("agent not ready yet, sleeping for some time ...")
			time.Sleep(time.Duration(100) * time.Millisecond)
		}
		if dhtClient.processEnvelope != nil {
			err := dhtClient.processEnvelope(envel)
			if err != nil {
				return err
			}
		} else {
			lwarn().
				Str("op", "route").
				Str("target", target).
				Msgf("ProcessEnvelope not set, ignoring envelope %s", envel.String())
			return nil
		}
	}

	//ldebug().
	//	Str("op", "route").
	//	Str("target", target).
	//	Msg("looking up peer ID for agent Address")

	// client can get addresses only through bootstrap peer
	stream, err := dhtClient.newStreamLoopUntilTimeout(
		dhtClient.relayPeer,
		dhtnode.AeaAddressStream,
		newStreamTimeoutRelayPeer,
	)
	if err != nil {
		return err
	}

	ldebug().
		Str("op", "route").
		Str("target", target).
		Msg("requesting agent record from relay...")

	lookupRequest := &dhtnode.LookupRequest{AgentAddress: target}
	msg := &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_LookupRequest{LookupRequest: lookupRequest},
	}
	buf, err := proto.Marshal(msg)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("while serializing LookupRequest message")
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}
	err = utils.WriteBytes(stream, buf)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("while sending LookupRequest message")
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}

	buf, err = utils.ReadBytes(stream)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("while receiving response acn message")
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}

	response := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, response)
	if err != nil {
		lerror(err).Str("op", "route").Str("target", target).
			Msgf("couldn't deserialize agent lookup response")
		return err
	}

	// response is either a LookupResponse or Status
	var lookupResponse *dhtnode.LookupResponse = nil
	var status *dhtnode.Status = nil
	switch pl := response.Payload.(type) {
	case *dhtnode.AcnMessage_LookupResponse:
		lookupResponse = pl.LookupResponse
	case *dhtnode.AcnMessage_Status:
		status = pl.Status
	default:
		err = errors.New("Unexpected Acn Message")
		lerror(err).Str("op", "route").Str("target", target).
			Msgf("couldn't deserialize agent lookup response")
		return err
	}

	if status != nil {
		err = errors.New(status.Code.String() + " : " + strings.Join(status.Msgs, ":"))
		lerror(err).Str("op", "route").Str("target", target).
			Msgf("failed agent lookup")
		return err
	}

	// lookupResponse must be set
	record := lookupResponse.AgentRecord
	valid, err := dhtnode.IsValidProofOfRepresentation(record, target, record.PeerPublicKey)
	if err != nil || valid.Code != dhtnode.Status_SUCCESS {
		errMsg := status.Code.String() + " : " + strings.Join(status.Msgs, ":")
		if err == nil {
			err = errors.New(errMsg)
		} else {
			err = errors.Wrap(err, status.Code.String()+" : "+strings.Join(status.Msgs, ":"))
		}
		lerror(err).Str("op", "route").Str("target", target).
			Msgf("invalid agent record")
		return err
	}

	stream.Close()

	peerID, err := utils.IDFromFetchAIPublicKey(record.PeerPublicKey)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msgf("CRITICAL couldn't get peer ID from message %s", msg)
		return errors.New("CRITICAL route - couldn't get peer ID from record peerID:" + err.Error())
	}

	ldebug().
		Str("op", "route").
		Str("target", target).
		Msgf("got peer ID %s for agent Address", peerID.Pretty())

	// TODO(LR): test if representative peer is relay peer, and skip the Connect if it is the case
	multiAddr := "/p2p/" + dhtClient.relayPeer.Pretty() + "/p2p-circuit/p2p/" + peerID.Pretty()
	relayMultiaddr, err := multiaddr.NewMultiaddr(multiAddr)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msgf("while creating relay multiaddress %s", multiAddr)
		return err
	}
	peerRelayInfo := peer.AddrInfo{
		ID:    peerID,
		Addrs: []multiaddr.Multiaddr{relayMultiaddr},
	}

	ldebug().
		Str("op", "route").
		Str("target", target).
		Msgf("connecting to target through relay %s", relayMultiaddr)

	if err = dhtClient.routedHost.Connect(context.Background(), peerRelayInfo); err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msgf("couldn't connect to target %s", peerID)
		return err
	}

	ldebug().
		Str("op", "route").
		Str("target", target).
		Msgf("opening stream to target %s", peerID)
	stream, err = dhtClient.newStreamLoopUntilTimeout(
		peerID,
		dhtnode.AeaEnvelopeStream,
		newStreamTimeout,
	)
	if err != nil {
		return err
	}

	envelBytes, err := proto.Marshal(envel)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("couldn't serialize envelope")
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}
	// TODO(LR) check if source is my agent
	aeaEnvelope := &dhtnode.AeaEnvelope{
		Envel:  envelBytes,
		Record: dhtClient.myAgentRecord,
	}
	msg = &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_AeaEnvelope{AeaEnvelope: aeaEnvelope},
	}
	buf, err = proto.Marshal(msg)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("couldn't serialize envelope")
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}

	ldebug().
		Str("op", "route").
		Str("target", target).
		Msg("sending envelope to target...")
	err = utils.WriteBytes(stream, buf)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("couldn't send envelope")
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}

	// wait for response
	buf, err = utils.ReadBytes(stream)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("while getting confirmation")
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}

	stream.Close()

	response = &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, response)
	if err != nil {
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("while deserializing acn confirmation message")
		return err
	}

	// response is expected to be a Status
	status = nil
	switch pl := response.Payload.(type) {
	case *dhtnode.AcnMessage_Status:
		status = pl.Status
	default:
		err = errors.New("Unexpected Acn Message")
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("while deserializing acn confirmation message")
		return err
	}

	if status.Code != dhtnode.Status_SUCCESS {
		err = errors.New(status.Code.String() + " : " + strings.Join(status.Msgs, ":"))
		lerror(err).
			Str("op", "route").
			Str("target", target).
			Msg("failed to deliver envelope")
		return err
	}

	return err
}

func (dhtClient *DHTClient) handleAeaEnvelopeStream(stream network.Stream) {
	lerror, lwarn, _, ldebug := dhtClient.getLoggers()

	//ldebug().Msgf("Got a new aea envelope stream")
	buf, err := utils.ReadBytes(stream)
	if err != nil {
		lerror(err).Msg("while reading envelope from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	// get envelope
	msg := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		lerror(err).Msg("while deserializing acn aea envelope message")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_SERIALIZATION}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	// payload is expected to be AeaEnvelope
	var aeaEnvelope *dhtnode.AeaEnvelope
	switch pl := msg.Payload.(type) {
	case *dhtnode.AcnMessage_AeaEnvelope:
		aeaEnvelope = pl.AeaEnvelope
	default:
		err = errors.New("Unexpected payload")
		lerror(err).Msg("while deserializing acn aea envelope message")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNEXPECTED_PAYLOAD}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	envel := &aea.Envelope{}
	err = proto.Unmarshal(aeaEnvelope.Envel, envel)
	if err != nil {
		lerror(err).Msg("while deserializing acn aea envelope message")
		status := &dhtnode.Status{
			Code: dhtnode.Status_ERROR_SERIALIZATION,
			Msgs: []string{err.Error()},
		}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	remotePubkey, err := utils.FetchAIPublicKeyFromPubKey(stream.Conn().RemotePublicKey())
	ignore(err)
	status, err := dhtnode.IsValidProofOfRepresentation(
		aeaEnvelope.Record,
		aeaEnvelope.Record.Address,
		remotePubkey,
	)
	if err != nil || status.Code != dhtnode.Status_SUCCESS {
		if err == nil {
			err = errors.New(status.Code.String() + ":" + strings.Join(status.Msgs, ":"))
		}
		lerror(err).Msg("incoming envelope PoR is not valid")
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	ldebug().Msgf("Received envelope from peer %s", envel.String())

	if envel.To == dhtClient.myAgentAddress && dhtClient.processEnvelope != nil {
		err = dhtClient.processEnvelope(envel)
		if err != nil {
			lerror(err).Msgf("while processing envelope by agent")
			status := &dhtnode.Status{Code: dhtnode.Status_ERROR_AGENT_NOT_READY}
			response := &dhtnode.AcnMessage{
				Version: dhtnode.CurrentVersion,
				Payload: &dhtnode.AcnMessage_Status{Status: status},
			}
			buf, err = proto.Marshal(response)
			ignore(err)
			err = utils.WriteBytes(stream, buf)
			ignore(err)
			err = stream.Close()
			ignore(err)
			return
		}
	} else {
		lwarn().Msgf("ignored envelope %s", envel.String())
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNKNOWN_AGENT_ADDRESS}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	status = &dhtnode.Status{Code: dhtnode.Status_SUCCESS}
	response := &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_Status{Status: status},
	}
	buf, err = proto.Marshal(response)
	ignore(err)
	err = utils.WriteBytes(stream, buf)
	ignore(err)
	err = stream.Close()
	ignore(err)
}

func (dhtClient *DHTClient) handleAeaAddressStream(stream network.Stream) {
	lerror, _, _, ldebug := dhtClient.getLoggers()

	//ldebug().Msg("Got a new aea address stream")

	// get LookupRequest
	buf, err := utils.ReadBytes(stream)
	if err != nil {
		lerror(err).Str("op", "resolve").
			Msg("while reading message from stream")
		err = stream.Reset()
		ignore(err)
		return
	}

	msg := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, msg)
	if err != nil {
		lerror(err).Str("op", "resolve").Msg("couldn't deserialize acn registration message")
		// TOFIX(LR) setting Msgs to err.Error is potentially a security vulnerability
		status := &dhtnode.Status{
			Code: dhtnode.Status_ERROR_SERIALIZATION,
			Msgs: []string{err.Error()},
		}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	// Get LookupRequest message
	var lookupRequest *dhtnode.LookupRequest
	switch pl := msg.Payload.(type) {
	case *dhtnode.AcnMessage_LookupRequest:
		lookupRequest = pl.LookupRequest
	default:
		err = errors.New("Unexpected payload")
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNEXPECTED_PAYLOAD, Msgs: []string{err.Error()}}
		response := &dhtnode.AcnMessage{Version: dhtnode.CurrentVersion, Payload: &dhtnode.AcnMessage_Status{Status: status}}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err)
		err = stream.Close()
		ignore(err)
		return
	}

	reqAddress := lookupRequest.AgentAddress

	ldebug().
		Str("op", "resolve").
		Str("target", reqAddress).
		Msg("Received query for addr")
	if reqAddress != dhtClient.myAgentAddress {
		lerror(err).
			Str("op", "resolve").
			Str("target", reqAddress).
			Msgf("requested address different from advertised one %s", dhtClient.myAgentAddress)
		status := &dhtnode.Status{Code: dhtnode.Status_ERROR_UNKNOWN_AGENT_ADDRESS}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_Status{Status: status},
		}
		buf, err = proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		ignore(err) // TODO(LR) stream.Reset() if err
		err = stream.Close()
		ignore(err)
		return
	} else {
		lookupResponse := &dhtnode.LookupResponse{AgentRecord: dhtClient.myAgentRecord}
		response := &dhtnode.AcnMessage{
			Version: dhtnode.CurrentVersion,
			Payload: &dhtnode.AcnMessage_LookupResponse{LookupResponse: lookupResponse},
		}
		buf, err := proto.Marshal(response)
		ignore(err)
		err = utils.WriteBytes(stream, buf)
		if err != nil {
			lerror(err).Str("op", "resolve").Str("addr", reqAddress).
				Msg("while sending agent record to peer")
			err = stream.Reset()
			ignore(err)
		}
	}

}

func (dhtClient *DHTClient) registerAgentAddress() error {
	lerror, _, _, ldebug := dhtClient.getLoggers()

	ldebug().
		Str("op", "register").
		Str("addr", dhtClient.myAgentAddress).
		Msg("opening stream aea-register to relay peer...")

	ctx, cancel := context.WithTimeout(context.Background(), newStreamTimeoutRelayPeer)
	defer cancel()
	stream, err := dhtClient.routedHost.NewStream(
		ctx,
		dhtClient.relayPeer,
		dhtnode.AeaRegisterRelayStream,
	)
	if err != nil {
		lerror(err).
			Str("op", "register").
			Str("addr", dhtClient.myAgentAddress).
			Msg("timeout, couldn't open stream to relay peer")
		return err
	}

	ldebug().
		Str("op", "register").
		Str("addr", dhtClient.myAgentAddress).
		Msgf("registering addr and peerID to relay peer")

	registration := &dhtnode.Register{Record: dhtClient.myAgentRecord}
	msg := &dhtnode.AcnMessage{
		Version: dhtnode.CurrentVersion,
		Payload: &dhtnode.AcnMessage_Register{Register: registration},
	}
	buf, err := proto.Marshal(msg)
	ignore(err)

	err = utils.WriteBytes(stream, buf)
	if err != nil {
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}
	buf, err = utils.ReadBytes(stream)
	if err != nil {
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}
	response := &dhtnode.AcnMessage{}
	err = proto.Unmarshal(buf, response)
	if err != nil {
		errReset := stream.Reset()
		ignore(errReset)
		return err
	}

	// Get Status message
	var status *dhtnode.Status
	switch pl := response.Payload.(type) {
	case *dhtnode.AcnMessage_Status:
		status = pl.Status
	default:
		errReset := stream.Close()
		ignore(errReset)
		return err
	}

	if status.Code != dhtnode.Status_SUCCESS {
		errReset := stream.Close()
		ignore(errReset)
		return errors.New("Registration failed: " + strings.Join(status.Msgs, ":"))
	}

	stream.Close()
	return nil

}

//ProcessEnvelope register a callback function
func (dhtClient *DHTClient) ProcessEnvelope(fn func(*aea.Envelope) error) {
	dhtClient.processEnvelope = fn
}
