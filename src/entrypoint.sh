#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo ""
echo "Authoritive PDNS IP: $PDNS_AUTH_API_HOST"
echo ""

echo ""
echo "Download latest named.root"
echo ""
wget https://www.internic.net/domain/named.root -O /var/named.root

LOOPS=0
until curl -H "X-API-KEY: $PDNS_AUTH_API_KEY" http://$PDNS_AUTH_API_HOST:$PDNS_AUTH_API_PORT/api/v1/servers; do
  >&2 echo "PDNS is unavailable - sleeping 5 sec"
  sleep 5
  LOOPS=$((LOOPS+1))
  if [ $LOOPS -eq 10 ]
  then
    break
  fi
done



if [ -f /etc/powerdns/forward.conf ]; then
  rm -f /etc/powerdns/forward.conf
fi
touch /etc/powerdns/forward.conf
echo ""
echo "Connecting to API on http://$PDNS_AUTH_API_HOST:$PDNS_AUTH_API_PORT/"
echo ""
curl -H "X-API-KEY: $PDNS_AUTH_API_KEY" http://$PDNS_AUTH_API_HOST:$PDNS_AUTH_API_PORT/api/v1/servers/localhost/zones  | jq '.[]|.name' | cut -d'"' -f2 | while read domain; do
  echo "Adding $domain=$PDNS_AUTH_API_HOST:$PDNS_AUTH_API_DNS_PORT to forward config"
  echo "$domain=$PDNS_AUTH_API_HOST:$PDNS_AUTH_API_DNS_PORT" >> /etc/powerdns/forward.conf
done


if [ ! -z ${EXTRA_FORWARD+x} ]; then
    echo $EXTRA_FORWARD |tr ',' '\n' >> /etc/powerdns/forward.conf
  fi


if [ -d "/etc/powerdns/recursor.d" ]; then
  rm -rf /etc/powerdns/recursor.d
  mkdir /etc/powerdns/recursor.d
  touch /etc/powerdns/recursor.d/forward.conf
else
  mkdir /etc/powerdns/recursor.d
  touch /etc/powerdns/recursor.d/forward.conf
fi


echo ""
echo "forward-zones-file=/etc/powerdns/forward.conf" > /etc/powerdns/recursor.d/forward.conf
echo "Starting PDNS Recursor"
echo ""

template () {
    arg1=$1
    arg2=$2
    python3 $DIR/lib/template.py --template $1 --output $2
}
template $DIR/templates/recursor.conf.j2 /etc/powerdns/recursor.conf

pdns_recursor --daemon=no --disable-syslog --write-pid=no
