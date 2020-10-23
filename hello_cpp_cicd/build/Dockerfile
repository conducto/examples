FROM debian:buster
RUN apt-get update
RUN apt-get -y install git g++ make cmake libboost-program-options-dev libboost-test-dev
RUN git clone https://github.com/MatrixManAtYrService/hello-cpp-linwin
WORKDIR hello-cpp-linwin
RUN git submodule update --init
