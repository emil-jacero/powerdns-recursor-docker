FROM ubuntu:18.04

MAINTAINER Emil Larsson <emil@jacero.se>

ENV DEBIAN_FRONTEND=noninteractive
ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn

RUN apt update && apt install -y ca-certificates curl wget gnupg2 jq dnsutils python3 python3-pip && apt -y upgrade

ARG PDNS_VERSION=42

RUN touch /etc/apt/sources.list.d/pdns.list && echo deb [arch=amd64] http://repo.powerdns.com/ubuntu bionic-auth-$PDNS_VERSION main >> /etc/apt/sources.list.d/pdns.list
RUN echo "Package: pdns-*" >> /etc/apt/preferences.d/pdns && \
    echo "Pin: origin repo.powerdns.com" >> /etc/apt/preferences.d/pdns && \
    echo "Pin-Priority: 600" >> /etc/apt/preferences.d/pdns
RUN wget -O- https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add - && apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install pdns-recursor

ADD src /app
ADD src/recursor.conf /etc/powerdns/recursor.conf

EXPOSE 53/tcp 53/udp

WORKDIR /app
ENTRYPOINT /app/entrypoint.sh
