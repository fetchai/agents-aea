FROM ubuntu:20.04

RUN apt-get update &&                                                        \
    apt-get install -y dialog &&                                             \
    apt-get install -y apt-utils &&                                          \
    apt-get upgrade -y &&                                                    \
    apt-get install -y sudo

# This adds the 'default' user to sudoers with full privileges:
RUN HOME=/home/default &&                                                    \
    mkdir -p ${HOME} &&                                                      \
    GROUP_ID=1000 &&                                                         \
    USER_ID=1000 &&                                                          \
    groupadd -r default -f -g "$GROUP_ID" &&                                 \
    useradd -u "$USER_ID" -r -g default -d "$HOME" -s /sbin/nologin          \
    -c "Default Application User" default &&                                 \
    chown -R "$USER_ID:$GROUP_ID" ${HOME} &&                                 \
    usermod -a -G sudo default &&                                            \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y                                                       \
       build-essential                                                       \
       software-properties-common                                            \
       vim                                                                   \
       make                                                                  \
       git                                                                   \
       less                                                                  \
       curl                                                                  \
       wget                                                                  \
       zlib1g-dev                                                            \
       libssl-dev                                                            \
       libffi-dev                                                            \
       python3-venv                                                          \
       python3-pip                                                           \
       python3-dev


# matplotlib build dependencies
RUN apt-get install -y                                                       \
       libxft-dev															 \
       libfreetype6											                 \
       libfreetype6-dev


# needed by Pipenv
ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get install -y tox
RUN python3 -m pip install -U pipenv==2021.5.29

ENV PATH="/usr/local/bin:${PATH}"
USER default

RUN sudo mkdir /build
WORKDIR /build
COPY . /build
RUN sudo  chown -R default /build

RUN sudo make clean

RUN pipenv --python python3.8
RUN pipenv run pip3 install --upgrade pip
RUN pipenv install --dev --skip-lock
RUN pipenv run pip3 install .[all]

CMD ["/bin/bash"]
