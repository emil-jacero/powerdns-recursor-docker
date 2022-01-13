# powerdns-recursor-docker

PowerDNS recursor docker image

## Supported Architectures

The images are built and tested on multiple platforms.

| Architecture | Tag |
| :----: | --- |
| x86-64 | amd64-latest |
| arm64 | arm64v8-latest |
| armv7l | armhf-latest |

## Version Tags

This image provides various versions that are available via tags. `latest` tag provides the latest stable version.

<span style="color:red">**NOTE: Sadly PowerDNS does not support arm on 4.5 yet.**</span>.

| Tag | Description |
| :----: | --- |
| amd64-latest | Latest stable version |
| amd64-4.5.x | Latest micro release of 4.5 |
| amd64-4.4.x | Latest micro release of 4.4 |
| arm64v8-latest | Latest stable version |
| arm64v8-4.4.x | Latest micro release of 4.4 |
| armhf-latest | Latest stable version |
| armhf-4.4.x | Latest micro release of 4.4 |

## Configuration

You configure using environment variables only. The environment variable will be converted to the nameing scheme PowerDNS is using.

**Example:**

**Docker env:** ENV_FORWARD_ZONES_FILE

**PDNS config:** forward-zones-file

### Required environment variables

| Name | Value | Default |
| :----: | --- | --- |
| `PDNS_AUTH_API_HOST` | Authorative DNS IP | 127.0.0.1 |
| `PDNS_AUTH_API_DNS_PORT` | Authorative DNS IP | N/A |
| `PDNS_AUTH_API_PORT` | Authorative DNS API Port | 8001 |
| `PDNS_AUTH_API_KEY` | Authorative DNS API Key | N/A |

## Examples

### Single authoritative secondary with SQLite and PowerDNS recursor

```
version: '3'
services:
  pdns-auth:
    container_name: pdns-auth
    image: emiljacero/powerdns-auth-docker:amd64-latest
    restart: always
    network_mode: host
    environment:
      TZ: Etc/UTC
      AUTOSECONDARY_IP: 192.168.100.10
      AUTOSECONDARY_NAMESERVER: ns1.example.com
      AUTOSECONDARY_ACCOUNT: Example
      ENV_secondary: "yes"
      ENV_autosecondary: "yes"
      ENV_launch: gsqlite3
      ENV_gsqlite3_database: "/var/lib/powerdns/auth.db"
      ENV_gsqlite3_pragma_synchronous: 0
      ENV_entropy_source: /dev/urandom
      ENV_socket_dir: /var/run/powerdns-authorative
      ENV_local_address: 192.168.100.20
      ENV_local_port: 5300
    volumes:
      - ./db:/var/lib/powerdns

  pdns-recursor:
    container_name: pdns-recursor
    image: emiljacero/powerdns-recursor-docker:amd64-latest
    restart: always
    depends_on:
      - pdns-auth
    network_mode: host
    environment:
      TZ: Etc/UTC
      ENV_ALLOW_FROM: 127.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 169.254.0.0/16,
        192.168.0.0/16, 172.16.0.0/12, ::1/128, fc00::/7, fe80::/10
      ENV_HINT_FILE: /var/named.root
      ENV_INCLUDE_DIR: /etc/powerdns/recursor.d
      ENV_FORWARD_ZONES_FILE: /etc/powerdns/forward.conf
      ENV_ENTROPY_SOURCE: /dev/urandom
      ENV_SOCKET_DIR: /var/run/powerdns-recursor
      ENV_SOCKET_MODE: 660
      ENV_LOCAL_ADDRESS: 192.168.100.20
      ENV_LOCAL_PORT: 53
      ENV_USE_INCOMING_EDNS_SUBNET: "yes"
      ENV_ECS_IPV4_BITS: 32
      ENV_ECS_IPV6_BITS: 128
      ENV_QUIET: "yes"
      ENV_SETGID: pdns
      ENV_SETUID: pdns
      ENV_DNSSEC: "off"
      ENV_WEBSERVER: "yes"
      ENV_WEBSERVER_PASSWORD: CHANGEME_PASSWORD
      ENV_WEBSERVER_ADDRESS: 0.0.0.0
      ENV_WEBSERVER_ALLOW_FROM: 0.0.0.0/0
      ENV_WEBSERVER_PORT: 8002
      ENV_API_KEY: CHANGEME_PASSWORD
      PDNS_AUTH_API_HOST: 127.0.0.1
      PDNS_AUTH_API_DNS_PORT: 5300
      PDNS_AUTH_API_PORT: 8001
      PDNS_AUTH_API_KEY: CHANGEME_PASSWORD
      EXTRA_FORWARD: ""
```
