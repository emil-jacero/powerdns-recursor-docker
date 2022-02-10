FROM ubuntu:20.04

LABEL maintainer="emil@jacero.se"

ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn
# Build arguments with sane defaults
ARG PDNS_VERSION=45

RUN apt-get update && apt-get -y install tzdata
RUN apt install -y ca-certificates curl wget gnupg2 jq dnsutils python3 python3-pip python3-psycopg2 && apt -y upgrade

# NOTE: DO NOT OVERWRITE THIS VARIABLE... EVER!
ENV POWERDNS_VERSION=$PDNS_VERSION

RUN touch /etc/apt/sources.list.d/pdns.list && echo deb [arch=amd64] http://repo.powerdns.com/ubuntu focal-rec-$PDNS_VERSION main >> /etc/apt/sources.list.d/pdns.list
RUN echo "Package: pdns-*" >> /etc/apt/preferences.d/pdns && \
    echo "Pin: origin repo.powerdns.com" >> /etc/apt/preferences.d/pdns && \
    echo "Pin-Priority: 600" >> /etc/apt/preferences.d/pdns
RUN wget -O- https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add - && apt-get update
RUN apt-get -y install pdns-recursor

ENV TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Installing python modules
ADD requirements.txt /
RUN pip3 install -r requirements.txt

# Prepare directories for PowerDNS
RUN mkdir -p /var/run/pdns-recursor && chown -R 101:101 /var/run/pdns-recursor
RUN mkdir -p /var/run/powerdns-recursor && chown -R 101:101 /var/run/powerdns-recursor

# Add src
ADD src /app
RUN chown -R 101:101 /app

EXPOSE 53/tcp 53/udp

WORKDIR /app
ENTRYPOINT /app/entrypoint.sh
