FROM ubuntu:22.04

RUN apt-get update && apt-get upgrade -y

RUN apt-get install sudo -y 
RUN apt-get install git -y

RUN adduser --disabled-password --gecos '' ubuntu
RUN adduser ubuntu sudo
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN apt install -y python3.10 python3.10-dev python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install pipenv

# utils
RUN apt install -y wget 

# golang
RUN wget https://dl.google.com/go/go1.13.8.linux-amd64.tar.gz && \
  tar -xzvf go1.13.8.linux-amd64.tar.gz -C /usr/local && \
  export PATH=$PATH:/usr/local/go/bin && echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc && \
  mkdir $HOME/go

USER ubuntu

ENV PATH="${PATH}:/usr/local/go/bin"
ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY user-image/openssl.cnf /etc/ssl

RUN echo 'PATH="$(python3.10 -m site --user-base)/bin:${PATH}"' >> ~/.bashrc
RUN echo "alias pip=pip3" >> ~/.bashrc
RUN echo "alias python=python3.10" >> ~/.bashrc


ENTRYPOINT [ "/bin/bash"]
