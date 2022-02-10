FROM ubuntu:20.04

LABEL maintainer="emil@jacero.se"

ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn
# Build arguments with sane defaults
ARG PDNS_VERSION=45

RUN apt update && apt -y install tzdata
RUN apt install -y ca-certificates curl wget gnupg2 jq dnsutils python3 python3-pip python3-psycopg2 && apt -y upgrade

# NOTE: DO NOT OVERWRITE THIS VARIABLE... EVER!
ENV POWERDNS_VERSION=$PDNS_VERSION
# Sane Defaults
ENV ENV_HINT_FILE=/var/named.root
ENV ENV_INCLUDE_DIR=/etc/powerdns/recursor.d
ENV ENV_FORWARD_ZONES_FILE=/etc/powerdns/forward.conf
ENV ENV_ENTROPY_SOURCE=/dev/urandom
ENV ENV_SOCKET_DIR=/var/run/powerdns-recursor

RUN touch /etc/apt/sources.list.d/pdns.list && echo deb [arch=amd64] http://repo.powerdns.com/ubuntu focal-rec-$PDNS_VERSION main >> /etc/apt/sources.list.d/pdns.list
RUN echo "Package: pdns-*" >> /etc/apt/preferences.d/pdns && \
    echo "Pin: origin repo.powerdns.com" >> /etc/apt/preferences.d/pdns && \
    echo "Pin-Priority: 600" >> /etc/apt/preferences.d/pdns
RUN curl -fsSL https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add - && apt update
RUN apt -y install pdns-recursor

ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Installing python modules
ADD requirements.txt /
RUN pip3 install -r requirements.txt

# Prepare directories for PowerDNS
RUN touch /recursor.conf && chown -R 101:101 /recursor.conf
RUN mkdir -p /var/run/pdns-recursor && chown -R 101:101 /var/run/pdns-recursor
RUN mkdir -p /var/run/powerdns-recursor && chown -R 101:101 /var/run/powerdns-recursor

# Add src
ADD src /app
RUN chown -R 101:101 /app

EXPOSE 53/tcp 53/udp

WORKDIR /app
ENTRYPOINT /app/entrypoint.sh
