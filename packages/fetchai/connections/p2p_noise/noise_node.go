package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	//"strings"
	"time"
	"errors"
	"github.com/perlin-network/noise"
	"github.com/perlin-network/noise/kademlia"
  	aea "./aea"
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

	// Create a new configured node.
  	host, port := agent.Uri()
  	key, err := noise.LoadKeysFromHex(agent.PrivateKey())
	
  	node, err := noise.NewNode(
		noise.WithNodeBindHost(host),
		noise.WithNodeBindPort(port),
		noise.WithNodeAddress(""),
    	noise.WithNodePrivateKey(key),
	)
	check(err)

	// Release resources associated to node at the end of the program.
	defer node.Close()

	// Register Envelope message
	node.RegisterMessage(aea.Envelope{}, aea.UnmarshalEnvelope)

	// Register a message handler to the node.
	node.Handle(func (ctx noise.HandlerContext) error {
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

	// Bind Kademlia to the node.
	node.Bind(overlay.Protocol())

	// Have the node start listening for new peers.
	check(node.Listen())

	//
	fmt.Printf("[noise-p2p][info] started node %s (%s).\n", node.ID().Address, node.ID().ID.String())

	// Ping entry node to initially bootstrap, if non genesis
	if len(agent.EntryUris()) > 0 {
		check(bootstrap(node, agent.EntryUris()...))
	}

	// Attempt to discover peers if we are bootstrapped to any nodes.
	go func() {
		for {
			discover(overlay)
			time.Sleep(2500*time.Millisecond)
		}
	}()

	// Once overlay setup, connect to agent
	check(agent.Connect())

	// Receive envelopes from agent
  	go func() {
    	for envel :=  range(agent.Queue()) {
			go send(*envel, node, overlay)
    	}
  	}()

	// Wait until Ctrl+C or a termination call is done.
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt)
	<-c

	// Empty println.
	println()
}

// Deliver an envelope 
func  send(envel aea.Envelope, node *noise.Node, overlay *kademlia.Protocol) error {
    //fmt.Printf("[noise-p2p][debug] Looking for %s...\n", envel.To)
    ids := overlay.Table().Peers()
    var dest *noise.ID = nil
    for _, id := range(ids) {
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

// Handle envelope from other peers
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
