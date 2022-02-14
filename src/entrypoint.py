#!/usr/bin/env python3

from multiprocessing.connection import wait
import os
import subprocess
import json
import requests
import time
import socket

from lib.logger import logger as log
from lib.template import Template

# Set working directory
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# PATHS
base_dir = os.path.dirname(os.path.realpath(__file__))
template_path = os.path.join(base_dir, 'templates')
render_recursor_conf = "/etc/powerdns/recursor.conf"
render_forward_conf = "/etc/powerdns/forward.conf"
named_root_path = "/var/named.root"

if os.getenv('DEV') == "true":
    template_path = os.path.join(base_dir, 'templates')
    render_recursor_conf = f"{base_dir}/dev/recursor.conf"
    render_forward_conf = f"{base_dir}/dev/forward.conf"
    named_root_path = f"{base_dir}/dev/named.root"

log.debug(base_dir)
log.debug(template_path)
log.debug(render_recursor_conf)
log.debug(render_forward_conf)
log.debug(named_root_path)

# Init
renderer = Template()


def get_from_environment(env_search_term="ENV_"):
    enviroment = {}
    log.info("Getting configuration from environment variables")
    for k, v in os.environ.items():
        if f"{env_search_term}" in k:
            k = k.replace(f"{env_search_term}", "").replace("_", "-").lower()
            obj = {k: v}
            enviroment.update(obj)
    # log.debug(enviroment)
    return enviroment


def get_from_file(file):
    conf_list = []
    pdns_config = {}
    log.info("Getting configuration from file")
    try:
        f = open(file, "r")
        conf_list = list(map(lambda s: s.strip(), f))
        conf_list = [x for x in conf_list if x]
        for line in conf_list:
            split_line = line.split("=")
            obj = {split_line[0]: split_line[1]}
            pdns_config.update(obj)
        # log.debug(pdns_config)
    except IOError as error:
        log.warning(f"Could not find  '/recursor.conf', moving on...")
    except Exception as error:
        log.error(error)
    return pdns_config


def merge_dicts_overwrite(defaults_dict, dict_list):
    log.info(f"Merging configurations")
    for dict in dict_list:
        defaults_dict.update(dict)
    log.debug(json.dumps(defaults_dict, indent=2))
    return defaults_dict


def download_named_root():
    named_root_url = "https://www.internic.net/domain/named.root"
    if os.getenv('NAMED_ROOT_URL'):
        named_root_url = os.getenv('NAMED_ROOT_URL')
    try:
        if os.getenv('HTTP_PROXY') is None or os.getenv('HTTPS_PROXY') is None:
            proxies = {
                'http': os.getenv('HTTP_PROXY'),
                'https': os.getenv('HTTPS_PROXY')
            }
            request = requests.get(
                named_root_url, allow_redirects=True, timeout=10, proxies=proxies)
        else:
            request = requests.get(
                named_root_url, allow_redirects=True, timeout=5)
        open(named_root_path, 'wb').write(request.content)
        log.info(
            f"Attempting download of {named_root_url} to {named_root_path}")
    except requests.exceptions.ConnectionError as error:
        log.error(
            f"Could not connect to server for download of named.root ({named_root_url})")
    except Exception as error:
        log.error(error)


def parse_recursor_conf():
    recursor_defaults = {
        "setuid": 101,
        "setgid": 101,
        "local-address": "0.0.0.0",
        "local-port": 53,
        "hint-file": "/var/named.root",
        "include-dir": "/etc/powerdns/recursor.d",
        "forward-zones-file": "/etc/powerdns/forward.conf",
        "forward-zones-file": render_forward_conf,
        "entropy-source": "/dev/urandom",
        "socket-dir": "/var/run/powerdns-recursor",
        "socket-mode": 660
    }
    log.debug(json.dumps(recursor_defaults, indent=2))
    recursor_file_conf = get_from_file("/recursor.conf")
    recursor_env_conf = get_from_environment("ENV_")
    recursor_conf = merge_dicts_overwrite(
        recursor_defaults, [recursor_file_conf, recursor_env_conf])
    return recursor_conf


def get_forward_zones(base_url, headers, dns_host, dns_port, timeout=30):
    zones_list = []
    sleep_time = 5
    time_end = time.time() + timeout
    url = f"{base_url}/api/v1/servers"
    hostname = None
    try:
        hostname = socket.gethostbyname(dns_host)
        while not connect_check(url, headers) == 200:
            if time.time() > time_end:
                log.warning("Could not connect PowerDNS Authorative API")
                log.warning(
                    "Going up without getting forward zones from PowerDNS Authorative :(")
                break
            log.info(
                f"Waiting for PowerDNS Authorative API at ({url}) to come online... sleep {sleep_time} seconds")
            time.sleep(sleep_time)
        if connect_check(url, headers) == 200:
            url = f"{base_url}/api/v1/servers/localhost/zones"
            response = requests.get(url, headers=headers)
            for zone in response.json():
                # zones_list.append(f"{zone['name'][:-1]}={hostname}:{dns_port}")
                zones_list.append(f"{zone['name']}={hostname}:{dns_port}")
    except:
        log.warning(
            f"Unable to resolve hostname ({dns_host}) from PDNS_AUTH_API_HOST. Cannot populate forward.conf :(")

    return zones_list


def parse_forward_zones_conf():
    """
    Get configuration from environment variables which overwrites defaults.
    It will attempt to download the latest named.root. If HTTP_PROXY or HTTPS_PROXY is specified it will attempt to use that.

    Returns:
        [type]: [description]
    """
    forward_conf_list = []
    # Get forward zones from PowerDNS auth
    auth_api_defaults = {
        "auth-api-protocol": "http://",
        "auth-api-host": "127.0.0.1",
        "auth-api-port": 8000,
        "auth-api-dns-port": 5300,
        "auth-api-key": "CHANGEME"
    }
    api_conf = merge_dicts_overwrite(
        auth_api_defaults, [get_from_environment("PDNS_")])

    auth_api_protocol = api_conf['auth-api-protocol']
    auth_api_host = api_conf['auth-api-host']
    auth_api_port = api_conf['auth-api-port']
    auth_api_dns_port = api_conf['auth-api-dns-port']
    auth_api_key = api_conf['auth-api-key']

    if api_conf['auth-api-dns-host']:
        auth_api_dns_host = api_conf['auth-api-dns-host']
        forward_conf_list = get_forward_zones(
            f"{auth_api_protocol}{auth_api_host}:{auth_api_port}",
            {"X-API-KEY": auth_api_key},
            auth_api_dns_host,
            auth_api_dns_port)
    else:
        forward_conf_list = get_forward_zones(
            f"{auth_api_protocol}{auth_api_host}:{auth_api_port}",
            {"X-API-KEY": auth_api_key},
            auth_api_host,
            auth_api_dns_port)

    if not os.getenv('EXTRA_FORWARD') is None:
        forward_conf_list = forward_conf_list + \
            os.getenv('EXTRA_FORWARD').replace(" ", "").split(",")
    return forward_conf_list


def connect_check(url, headers):
    response = None
    try:
        response = requests.get(url, headers=headers).status_code
    except requests.exceptions.ConnectionError as error:
        log.error(f"Got connection error. Check the url ({url})")
        log.debug(error)
    except Exception as error:
        log.error(error)
    return response


def main():
    # Download named.root
    download_named_root()

    recursor_conf = parse_recursor_conf()
    forward_conf = parse_forward_zones_conf()

    # Write templates
    template = os.path.join(template_path, "recursor.conf.j2")
    renderer.render_template(template=template,
                             output_file=render_recursor_conf,
                             data=recursor_conf)

    template = os.path.join(template_path, "forward.conf.j2")
    renderer.render_template(template=template,
                             output_file=render_forward_conf,
                             data=forward_conf)

    log.info("------------------------------------------")
    log.info("PowerDNS forward config")
    log.info("------------------------------------------")
    for line in open("/etc/powerdns/forward.conf"):
        log.info(line.strip())
    log.info("------------------------------------------")

    if os.getenv('LOG_LEVEL') == "DEBUG":
        log.debug("------------------------------------------")
        log.debug("PowerDNS config")
        log.debug("------------------------------------------")
        for line in open("/etc/powerdns/recursor.conf"):
            log.debug(line.strip())
        log.debug("------------------------------------------")

    # Launch PowerDNS
    log.info("Starting PowerDNS")
    process = subprocess.Popen([
        "pdns_recursor", "--daemon=no", "--disable-syslog", "--write-pid=no"
    ], shell=False)
    process.wait()
    log.info("PowerDNS stopped")


if __name__ == "__main__":
    main()
