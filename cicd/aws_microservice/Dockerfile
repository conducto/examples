FROM python:3.8-slim

RUN apt-get update && apt-get install -y curl vim less zip
RUN curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip \
  -o /tmp/awscliv2.zip && \
  unzip /tmp/awscliv2.zip && \
  ./aws/install && \
  rm -rf ./aws

WORKDIR conducto-demo
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
COPY cloudformation cloudformation
COPY service service

CMD ["/bin/bash"]
