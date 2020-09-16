FROM ubuntu:18.04

USER root

RUN apt-get update && apt-get upgrade -y

RUN apt install -y python3 python3-pip

# utils
RUN apt install -y wget

# golang
RUN wget https://dl.google.com/go/go1.13.8.linux-amd64.tar.gz && \
  tar -xzvf go1.13.8.linux-amd64.tar.gz -C /usr/local && \
  export PATH=$PATH:/usr/local/go/bin && echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc && \
  mkdir $HOME/go

ENV PATH="${PATH}:/usr/local/go/bin"

# deployment scripts deps: needed only if configuration checks are enabled
RUN python3 -m pip install pymultihash ecdsa base58

WORKDIR /acn/

#RUN go build

#CMD [ "python3", "-u", "/acn/run_acn_node_standalone.py"]
ENTRYPOINT ["echo"]

