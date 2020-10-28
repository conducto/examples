FROM hashicorp/terraform:light

RUN apk add --update zlib-dev alpine-sdk
RUN mkdir -p /root/python
RUN cd /root/python \
        && wget https://www.python.org/ftp/python/3.8.5/Python-3.8.5.tgz \
        && tar xzf Python-3.8.5.tgz

RUN cd /root/python/Python-3.8.5 \
        && ./configure --prefix=/usr/bin/python/3.8.5 \
        && make
RUN cd /root/python/Python-3.8.5 \
        && make install

COPY . /root/terraform

ENTRYPOINT /bin/sh
