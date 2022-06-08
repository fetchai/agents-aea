package dhtpeer

import (
	"context"
	"crypto/tls"
	"io/ioutil"
	acn "libp2p_node/acn"
	aea "libp2p_node/aea"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"google.golang.org/protobuf/proto"
)

func (mailboxServer *MailboxServer) apiRegister(res http.ResponseWriter, req *http.Request) {
	var data []byte
	var body []byte
	var err error

	if req.Method != "POST" {
		data = []byte("invalid method")
		res.WriteHeader(400)
		_, err = res.Write(data)
		ignore(err)
		return
	}
	body, err = ioutil.ReadAll(req.Body)
	if err != nil {
		res.WriteHeader(400)
		_, err = res.Write([]byte(err.Error()))
		ignore(err)
		return

	}
	//get por
	if len(body) == 0 {
		res.WriteHeader(400)
		_, err = res.Write([]byte("Empty body"))
		ignore(err)
		return
	}
	record := &acn.AgentRecord{}
	err = proto.Unmarshal(body, record)
	if err != nil {
		res.WriteHeader(400)
		_, err = res.Write([]byte("Error on agent record deserialize"))
		ignore(err)
		return
	}
	addr := record.Address

	// TODO: double register fix!!!

	//check por
	status, err := mailboxServer.dhtPeer.CheckPOR(record)
	if err != nil || status.Code != acn.SUCCESS {
		res.WriteHeader(400)
		_, err = res.Write([]byte("Invalid PoR"))
		ignore(err)
		return
	}
	uuid := strings.ReplaceAll(uuid.NewString(), "-", "")
	if mailboxServer.dhtPeer.IsAddressAnnouncementEnabled() {
		err = mailboxServer.dhtPeer.RegisterAgentAddress(addr)
		if err != nil {
			res.WriteHeader(400)
			_, err = res.Write([]byte("failed to register address over dht"))
			ignore(err)
			return
		}
	}

	mailboxServer.lock.Lock()
	mailboxServer.agentRecords[addr] = record
	mailboxServer.sessions[uuid] = addr
	mailboxServer.envelopes[addr] = make([]*aea.Envelope, 0)
	mailboxServer.lock.Unlock()

	res.WriteHeader(200)
	_, err = res.Write([]byte(uuid))
	ignore(err)
}

func (mailboxServer *MailboxServer) apiUnregister(res http.ResponseWriter, req *http.Request) {
	var data []byte
	var err error
	var addr string
	var sessionId string

	if req.Method != "GET" {
		data = []byte("invalid method")
		res.WriteHeader(400)
		_, err = res.Write(data)
		ignore(err)
		return
	}
	session_header, exists := req.Header["Session-Id"]

	if exists {
		sessionId = session_header[0]
		mailboxServer.lock.Lock()
		addr, exists = mailboxServer.sessions[sessionId]
		mailboxServer.lock.Unlock()
	}

	if !exists {
		res.WriteHeader(400)
		_, err = res.Write([]byte("invalid session_id header"))
		ignore(err)
		return
	}

	mailboxServer.lock.Lock()
	delete(mailboxServer.agentRecords, addr)
	delete(mailboxServer.sessions, sessionId)
	delete(mailboxServer.envelopes, addr)
	mailboxServer.lock.Unlock()

}

func (mailboxServer *MailboxServer) apiGetSignature(res http.ResponseWriter, req *http.Request) {
	var err error
	if req.Method != "GET" {
		res.WriteHeader(400)
		_, err = res.Write([]byte("invalid method"))
		ignore(err)
		return
	}
	res.WriteHeader(200)
	_, err = res.Write(mailboxServer.signature)
	ignore(err)
}

func (mailboxServer *MailboxServer) apiSendEnvelope(res http.ResponseWriter, req *http.Request) {
	var err error
	if req.Method != "POST" {
		res.WriteHeader(400)
		_, err = res.Write([]byte("invalid method"))
		ignore(err)
		return
	}

	session_header, exists := req.Header["Session-Id"]

	if exists {
		sessionId := session_header[0]
		mailboxServer.lock.Lock()
		_, exists = mailboxServer.sessions[sessionId]
		mailboxServer.lock.Unlock()
	}

	if !exists {
		res.WriteHeader(400)
		_, err = res.Write([]byte("invalid session_id header"))
		ignore(err)
		return
	}

	body, err := ioutil.ReadAll(req.Body)
	if err != nil {
		res.WriteHeader(400)
		_, err = res.Write([]byte(err.Error()))
		ignore(err)
		return
	}
	//getenvelope
	if len(body) == 0 {
		res.WriteHeader(400)
		_, err = res.Write([]byte("Empty body"))
		ignore(err)
		return
	}
	envelope := &aea.Envelope{}
	err = proto.Unmarshal(body, envelope)
	if err != nil {
		res.WriteHeader(400)
		_, err = res.Write([]byte(err.Error()))
		ignore(err)
		return
	}
	err = mailboxServer.dhtPeer.RouteEnvelope(envelope)
	if err != nil {
		res.WriteHeader(400)
		_, err = res.Write([]byte(err.Error()))
		ignore(err)
	}
}

func (mailboxServer *MailboxServer) apiGetEnvelope(res http.ResponseWriter, req *http.Request) {
	var buf []byte
	var envelopesList []*aea.Envelope
	var err error
	var addr string

	if req.Method != "GET" {
		res.WriteHeader(400)
		_, err = res.Write([]byte("invalid method"))
		ignore(err)
		return
	}

	session_header, exists := req.Header["Session-Id"]

	mailboxServer.lock.Lock()
	defer mailboxServer.lock.Unlock()
	if exists {
		sessionId := session_header[0]
		addr, exists = mailboxServer.sessions[sessionId]
	}
	if !exists {
		res.WriteHeader(400)
		_, err = res.Write([]byte("invalid session_id header"))
		ignore(err)
		return
	}
	envelopesList = mailboxServer.envelopes[addr]

	if len(envelopesList) == 0 {
		res.WriteHeader(200)
		return
	}
	envelope := envelopesList[0]
	buf, err = proto.Marshal(envelope)
	if err != nil {
		//log error
		return
	}
	res.WriteHeader(200)

	_, err = res.Write(buf)
	if err == nil {
		// all ok, remove the first envelope from slice
		mailboxServer.envelopes[addr] = mailboxServer.envelopes[addr][1:]
	}
}

type MailboxServer struct {
	addr           string
	dhtPeer        *DHTPeer
	httpServer     *http.Server
	sessions       map[string]string
	agentRecords   map[string]*acn.AgentRecord
	envelopes      map[string]([]*aea.Envelope)
	lock           sync.RWMutex
	envelopesLimit int
	cert           *tls.Certificate
	signature      []byte
}

func (mailboxServer *MailboxServer) start() {
	var err error
	lerror, _, _, _ := mailboxServer.dhtPeer.GetLoggers()
	mailboxServer.envelopes = map[string][]*aea.Envelope{}
	mailboxServer.agentRecords = map[string]*acn.AgentRecord{}
	mailboxServer.sessions = map[string]string{}
	mailboxServer.lock = sync.RWMutex{}
	mailboxServer.envelopesLimit = 1000
	mailboxServer.cert, mailboxServer.signature = mailboxServer.dhtPeer.GetCertAndSignature()

	mux := http.NewServeMux()
	mux.HandleFunc("/register", mailboxServer.apiRegister)
	mux.HandleFunc("/unregister", mailboxServer.apiUnregister)
	mux.HandleFunc("/get_envelope", mailboxServer.apiGetEnvelope)
	mux.HandleFunc("/send_envelope", mailboxServer.apiSendEnvelope)
	mux.HandleFunc("/ssl_signature", mailboxServer.apiGetSignature)

	tlsConfig := &tls.Config{Certificates: []tls.Certificate{*mailboxServer.cert}}

	mailboxServer.httpServer = &http.Server{
		Addr:      mailboxServer.addr,
		Handler:   mux,
		TLSConfig: tlsConfig,
	}
	listener, err := tls.Listen("tcp", mailboxServer.addr, tlsConfig)
	if err != nil {
		lerror(err).Msgf("while setting mailbox tls")
	}
	err = mailboxServer.httpServer.Serve(listener)
	if err != nil {
		lerror(err).Msgf("while running mailbox http server")
	}
}

func (mailboxServer *MailboxServer) stop() {
	var err error
	lerror, _, _, _ := mailboxServer.dhtPeer.GetLoggers()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	err = mailboxServer.httpServer.Shutdown(ctx)
	if err != nil {
		lerror(err).Msg("Error on mailbox http server shutdown")
	}
}

func (mailboxServer *MailboxServer) RouteEnvelope(envelope *aea.Envelope) bool {
	target := envelope.To
	_, _, linfo, _ := mailboxServer.dhtPeer.GetLoggers()
	linfo().Msgf("route to %s", target)

	mailboxServer.lock.Lock()
	defer mailboxServer.lock.Unlock()
	envelopesList, listExist := mailboxServer.envelopes[target]

	if !listExist {
		linfo().Msgf("route to %s. no target", target)
		return false
	}
	// check chan is full
	if mailboxServer.envelopesLimit != 0 &&
		len(mailboxServer.envelopes[target]) >= mailboxServer.envelopesLimit {
		linfo().Msgf("Envelopes queue for  %s is full. (%d envelopes)", target, mailboxServer.envelopesLimit)
		return false
	}

	mailboxServer.envelopes[target] = append(envelopesList, envelope)

	linfo().Msgf("route to %s. added to queue!", target)
	return true
}

func (mailboxServer *MailboxServer) IsAddrRegistered(addr string) bool {
	mailboxServer.lock.Lock()
	defer mailboxServer.lock.Unlock()
	_, listExist := mailboxServer.envelopes[addr]
	return listExist
}

func (mailboxServer *MailboxServer) GetAgentRecord(addr string) *acn.AgentRecord {
	if !mailboxServer.IsAddrRegistered(addr) {
		return nil
	}
	mailboxServer.lock.Lock()
	defer mailboxServer.lock.Unlock()
	return mailboxServer.agentRecords[addr]
}
