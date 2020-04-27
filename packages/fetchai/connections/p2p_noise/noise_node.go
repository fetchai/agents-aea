package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"

	//"strings"
	"errors"
	aea "noise_aea/aea"
	"time"

	"github.com/perlin-network/noise"
	"github.com/perlin-network/noise/kademlia"
)

// check panics if err is not nil.
func check(err error) {
	if err != nil {
		panic(err)
	}
}

// An initial noise p2p node for AEA's fetchai/p2p-noise/0.1.0 connection
func main() {

	// Create connection to aea
	agent := aea.AeaApi{}
	check(agent.Init())
	fmt.Printf("[noise-p2p][info] successfully initialised API to AEA!\n")

	// Create a new configured node.
	host, port := agent.Uri()
	key, err := noise.LoadKeysFromHex(agent.PrivateKey())
	check(err)

	node, err := noise.NewNode(
		noise.WithNodeBindHost(host),
		noise.WithNodeBindPort(port),
		noise.WithNodeAddress(""),
		noise.WithNodePrivateKey(key),
	)
	check(err)
	fmt.Printf("[noise-p2p][info] successfully created noise node!\n")

	// Release resources associated to node at the end of the program.
	defer node.Close()

	// Register Envelope message
	node.RegisterMessage(aea.Envelope{}, aea.UnmarshalEnvelope)

	// Register a message handler to the node.
	node.Handle(func(ctx noise.HandlerContext) error {
		return handle(ctx, agent)
	})

	// Instantiate Kademlia.
	events := kademlia.Events{
		OnPeerAdmitted: func(id noise.ID) {
			fmt.Printf("[noise-p2p][info] Learned about a new peer %s(%s).\n", id.Address, id.ID.String())
		},
		OnPeerEvicted: func(id noise.ID) {
			fmt.Printf("[noise-p2p][info] Forgotten a peer %s(%s).\n", id.Address, id.ID.String())
		},
	}

	overlay := kademlia.New(kademlia.WithProtocolEvents(events))
	fmt.Printf("[noise-p2p][info] successfully created overlay!\n")

	// Bind Kademlia to the node.
	node.Bind(overlay.Protocol())
	fmt.Printf("[noise-p2p][info] started node %s (%s).\n", node.ID().Address, node.ID().ID.String())

	// Have the node start listening for new peers.
	check(node.Listen())
	fmt.Printf("[noise-p2p][info] successfully listening...\n")

	// Ping entry node to initially bootstrap, if non genesis
	if len(agent.EntryUris()) > 0 {
		check(bootstrap(node, agent.EntryUris()...))
		fmt.Printf("[noise-p2p][info] successfully bootstrapped.\n")
	}

	// Once overlay setup, connect to agent
	check(agent.Connect())
	fmt.Printf("[noise-p2p][info] successfully connected to AEA!\n")

	// Attempt to discover peers if we are bootstrapped to any nodes.
	go func() {
		fmt.Printf("[noise-p2p][debug] discovering...\n")
		for {
			discover(overlay)
			time.Sleep(2500 * time.Millisecond)
		}
	}()

	// Receive envelopes from agent and forward to peer
	go func() {
		for envel := range agent.Queue() {
			go send(*envel, node, overlay)
		}
	}()

	// Wait until Ctrl+C or a termination call is done.
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c

	// remove sum file
	sum_file := "go.sum"
	file_err := os.Remove(sum_file)
	if file_err != nil {
		fmt.Println(err)
		return
	}
	fmt.Printf("File %s successfully deleted\n", sum_file)

	fmt.Println("[noise-p2p][info] node stopped")
}

// Deliver an envelope from agent to receiver peer
func send(envel aea.Envelope, node *noise.Node, overlay *kademlia.Protocol) error {
	//fmt.Printf("[noise-p2p][debug] Looking for %s...\n", envel.To)
	ids := overlay.Table().Peers()
	var dest *noise.ID = nil
	for _, id := range ids {
		if id.ID.String() == envel.To {
			dest = &id
			break
		}
	}

	if dest == nil {
		fmt.Printf("[noise-p2p][error] Couldn't locate peer with id %s\n", envel.To)
		return errors.New("Couldn't locate peer")
	}

	fmt.Printf("[noise-p2p][debug] Sending to %s:%s...\n", dest.Address, envel)
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	err := node.SendMessage(ctx, dest.Address, envel)
	cancel()

	if err != nil {
		fmt.Printf("[noise-p2p][error] Failed to send message to %s. Skipping... [error: %s]\n",
			envel.To,
			err,
		)
		return errors.New("Failed to send message")
	}

	return nil
}

// Handle envelope from other peers for agent
func handle(ctx noise.HandlerContext, agent aea.AeaApi) error {
	if ctx.IsRequest() {
		return nil
	}

	obj, err := ctx.DecodeMessage()
	if err != nil {
		return nil
	}

	envel, ok := obj.(aea.Envelope)
	if !ok {
		return nil
	}

	// Deliver envelope to agent
	fmt.Printf("[noise-p2p][debug] Received envelope %s(%s) - %s\n", ctx.ID().Address, ctx.ID().ID.String(), envel)
	agent.Put(&envel)

	return nil
}

// bootstrap pings and dials an array of network addresses which we may interact with and  discover peers from.
func bootstrap(node *noise.Node, addresses ...string) error {
	for _, addr := range addresses {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		_, err := node.Ping(ctx, addr)
		cancel()

		if err != nil {
			fmt.Printf("[noise-p2p][error] Failed to ping bootstrap node (%s). Skipping... [error: %s]\n", addr, err)
			return err
		}
	}
	return nil
}

// discover uses Kademlia to discover new peers from nodes we already are aware of.
func discover(overlay *kademlia.Protocol) {
	ids := overlay.Discover()

	var str []string
	for _, id := range ids {
		str = append(str, fmt.Sprintf("%s(%s)", id.Address, id.ID.String()))
	}

	// TOFIX(LR) keeps printing already known peers
	if len(ids) > 0 {
		//fmt.Printf("[noise-p2p][debug] Discovered %d peer(s): [%v]\n", len(ids), strings.Join(str, ", "))
	} else {
		//fmt.Printf("[noise-p2p][debug] Did not discover any peers.\n")
	}
}
