FROM alpine:latest
RUN apk update && apk add git cowsay \
        --update-cache \
        --repository https://alpine.global.ssl.fastly.net/alpine/edge/community \
        --repository https://alpine.global.ssl.fastly.net/alpine/edge/main \
        --repository https://dl-3.alpinelinux.org/alpine/edge/testing
RUN git clone http://github.com/possatti/pokemonsay
RUN cd pokemonsay && ./install.sh
ENV PATH "/usr/games:/root/bin:${PATH}"
