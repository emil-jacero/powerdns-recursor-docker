#!/bin/bash

#ip=`getent hosts $PDNS_AUTH_HOSTNAME | awk '{ print $1 }'`
echo ""
echo "Authoritive PDNS IP: $PDNS_AUTH_API_HOST"
echo ""

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
curl -H "X-API-KEY: $PDNS_AUTH_API_KEY" http://$PDNS_AUTH_API_HOST:$PDNS_AUTH_API_PORT/api/v1/servers/localhost/zones | jq '.[]|.name' | cut -d'"' -f2 | while read domain; do
  echo "Adding $domain=$PDNS_AUTH_API_HOST to forward config"
  echo "$domain=$PDNS_AUTH_API_HOST" >> /etc/powerdns/forward.conf
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

pdns_recursor --daemon=no --disable-syslog --write-pid=no
