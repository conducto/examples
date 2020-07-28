FROM debian:bullseye-20200720-slim
RUN apt-get update && apt-get install -y git cowsay
RUN git clone http://github.com/possatti/pokemonsay
RUN cd pokemonsay && ./install.sh
ENV PATH "/usr/games:/root/bin:${PATH}"
