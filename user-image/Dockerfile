FROM ubuntu:22.10
SHELL [ "/bin/bash", "-c" ]

RUN apt-get update && apt-get upgrade -y

RUN apt-get install sudo -y

RUN adduser --disabled-password --gecos '' ubuntu
RUN adduser ubuntu sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN apt install -y python3 python3-pip
RUN pip3 install --upgrade pip

# python extensions
RUN apt install -y python3-dev

# utils
RUN apt install -y wget

# golang
RUN wget https://go.dev/dl/go1.20.linux-amd64.tar.gz && \
  tar -xzvf go1.20.linux-amd64.tar.gz -C /usr/local && \
  export PATH=$PATH:/usr/local/go/bin && echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc && \
  mkdir $HOME/go

# protobuf
RUN apt install -y protobuf-compiler

USER ubuntu

ENV PATH="${PATH}:/usr/local/go/bin"
ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# AEA framework
RUN pip3 install "aea[all]"

RUN echo 'PATH="/home/ubuntu/.local/bin:$PATH"' >> ~/.bashrc
RUN echo $'alias pip=pip3\nalias python=python3' >> ~/.bashrc

ENTRYPOINT [ "/bin/bash" ]
