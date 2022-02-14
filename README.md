[![GitHub license](https://img.shields.io/github/license/emil-jacero/powerdns-recursor-docker)](https://github.com/emil-jacero/powerdns-recursor-docker/blob/master/LICENSE) [![GitHub stars](https://img.shields.io/github/stars/emil-jacero/powerdns-recursor-docker)](https://github.com/emil-jacero/powerdns-recursor-docker/stargazers) [![GitHub issues](https://img.shields.io/github/issues/emil-jacero/powerdns-recursor-docker)](https://github.com/emil-jacero/powerdns-recursor-docker/issues)

# powerdns-auth-docker

This is a PowerDNS authoritative docker image designed to handle minor and major updates seamlessly.

## Related projects

- [powerdns-recursor-docker](https://github.com/emil-jacero/powerdns-recursor-docker)
- [powerdns-dnsdist-docker](https://github.com/emil-jacero/powerdns-dnsdist-docker)

## Supported Architectures

The images are built and tested on x86-64 only with the exception for PowerDNS 4.4 on `amrhf` (Raspberry pi 32bit) for which there is a specific dockerfile named `Dockerfile.armhf`. This has to be built manually.

| Architecture |
| :----: |
| x86-64 |

## Configuration

You configure using environment variables only. The environment variable will be converted to the nameing scheme PowerDNS is using.

**Example:**

Environment variable: `ENV_LOCAL_ADDRESS=0.0.0.0` or `ENV_LOCAL_ADDRESS: 0.0.0.0`

PowerDNS config: `local-address`

## Required environment variables

These variables are used to connect to the PowerDNS authorative instance and get the zones to add to the `forward-zones-file`.

| Name | Default | Description |
| :----: | --- | --- |
|`PDNS_AUTH_API_HOST`|`127.0.0.1`|Authorative DNS IP|
|`PDNS_AUTH_API_PORT`|`8001`|Authorative DNS API Port|
|`PDNS_AUTH_API_KEY`|`CHANGEME`|Authorative DNS API Key|
|`PDNS_AUTH_DNS_PORT`|`5300`|Authorative DNS Port|

## Optional environment variables

| Name | Default | Description |
| :----: | --- | --- |
|`NAMED_ROOT_URL`|`"https://www.internic.net/domain/named.root"`|Where to download named.root from|
|`HTTP_PROXY`|`N/A`|Set this if a proxy is needed for the `named.root` download|
|`HTTPS_PROXY`|`N/A`|Set this if a proxy is needed for the `named.root` download|
|`PDNS_AUTH_DNS_PORT`|`5300`|To overwrite the host to foward to. For example in K8s the api host may not be the same as the PowerDNS auth host|

## Examples

### Single authoritative secondary with SQLite and PowerDNS recursor

```yaml
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
      ENV_LOCAL_ADDRESS: 192.168.100.20
      ENV_LOCAL_PORT: 53
      ENV_QUIET: "yes"
      ENV_SETGID: 101
      ENV_SETUID: 101
      ENV_DNSSEC: "off"
      ENV_WEBSERVER: "yes"
      ENV_WEBSERVER_PASSWORD: CHANGEME_PASSWORD
      ENV_WEBSERVER_ADDRESS: 0.0.0.0
      ENV_WEBSERVER_ALLOW_FROM: 0.0.0.0/0
      ENV_WEBSERVER_PORT: 8002
      ENV_API_KEY: CHANGEME_PASSWORD
      PDNS_AUTH_API_HOST: 127.0.0.1
      PDNS_AUTH_API_PORT: 8001
      PDNS_AUTH_API_KEY: CHANGEME_PASSWORD
      PDNS_AUTH_DNS_PORT: 5300
      EXTRA_FORWARD: ""
      ENV_FORWARD_ZONES_RECURSE: ".=1.1.1.1,.=1.0.0.1"  # This redirect all other queries
```
