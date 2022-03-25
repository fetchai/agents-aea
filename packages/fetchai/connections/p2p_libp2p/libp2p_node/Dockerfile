FROM golang:1.17.5-buster as builder

USER root

WORKDIR /build

COPY ./ ./

RUN go build

FROM scratch AS export-stage
COPY --from=builder /build/libp2p_node libp2p_node