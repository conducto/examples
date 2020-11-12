FROM alpine:3.12
RUN apk add bash parallel gzip
RUN head -c 50m </dev/urandom >payload1.dat
RUN head -c 100m </dev/urandom >payload2.dat
RUN head -c 150m </dev/urandom >payload3.dat
RUN head -c 200m </dev/urandom >payload4.dat
RUN head -c 250m </dev/urandom >payload5.dat

RUN bash -c 'echo "yes\nwill cite" | parallel --citation || true'
#  Special thanks to:
#  Tange, O. (2020, May 22). GNU Parallel 20200522 ('Kraftwerk').
#  Zenodo. https://doi.org/10.5281/zenodo.3841377
