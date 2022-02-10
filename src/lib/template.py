#!/usr/bin/env python3
import os
import argparse
import jinja2
import logging
import json

logger_name = 'template'
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_levels = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR
}
env_log_level = os.getenv('LOG_LEVEL')

if env_log_level in log_levels.keys():
    log_level = log_levels[env_log_level]
else:
    log_level = logging.INFO

logger = logging.getLogger(logger_name)
logger.setLevel(log_level)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


def is_list(value):
    return isinstance(value, list)


def get_from_environment(env_search_term="ENV"):
    enviroment = {}
    for k, v in os.environ.items():
        if f"{env_search_term}_" in k:
            k = k.replace(f"{env_search_term}_", "").replace("_", "-").lower()
            obj = {k: v}
            enviroment.update(obj)
    logger.debug(f"Getting environment variables")
    logger.debug(json.dumps(enviroment, indent=2))
    return enviroment


def get_from_file(file):
    conf_list = []
    pdns_config = {}
    try:
        f = open(file, "r")
        conf_list = list(map(lambda s: s.strip(), f))
        conf_list = [x for x in conf_list if x]
        for line in conf_list:
            split_line = line.split("=")
            obj = {split_line[0]: split_line[1]}
            pdns_config.update(obj)
        logger.debug(f"Getting file configuration")
        logger.debug(json.dumps(pdns_config, indent=2))
    except Exception as error:
        logger.error(error)
    return pdns_config


def merge_dicts(defaults_dict, dict_list):
    for dict in dict_list:
        defaults_dict.update(dict)
    logger.debug(f"Final configuration")
    logger.debug(json.dumps(defaults_dict, indent=2))
    return defaults_dict


# Default pdns config as dict
defaults = {
    "setuid": 101,
    "setgid": 101,
    "local-address": "0.0.0.0",
    "local-port": 53,
    "hint-file": "/var/named.root",
    "include-dir": "/etc/powerdns/recursor.d",
    "forward-zones-file": "/etc/powerdns/forward.conf",
    "entropy-source": "/dev/urandom",
    "socket-dir": "/var/run/powerdns-recursor",
    "socket-mode": 660
}

# Read config from file (/recursor.conf) and parse to dict
file_conf = get_from_file("/recursor.conf")

# Read config from Environment variables (ENV_) and parse to dict
env_conf = get_from_environment("ENV")

pdns_conf = merge_dicts(defaults, [file_conf, env_conf])


class Template:
    def __init__(self):
        self.log_name = f'{logger_name}.{self.__class__.__name__}'
        self.log = logging.getLogger(self.log_name)
        self.path = None
        self.name = None
        self.variables = pdns_conf

    def render_template(self, template, output_file):
        """
            Takes template, output file and dictionary of variables.
            Renders template with variables to the specified output file.
        """
        self.path = os.path.dirname(template)
        self.name = os.path.basename(template)
        self.log.debug(
            f"Template path: {'Path_not_provided' if self.path is '' else self.path}"
        )
        self.log.debug(f"Template name: {self.name}")
        # Remove file if exists
        if os.path.exists(output_file):
            self.log.info(f"Removing old file [{output_file}]")
            os.remove(output_file)

        # Write rendered template into file
        self.log.info(f"Rendering template {template} to {output_file}")
        data = self.variables
        with open(output_file, 'w') as f:
            f.write(
                self._load_template(self.name, self.path).render(data=data))

    def _load_template(self, name, path=None):
        """
            Takes template name and a path to the template directory
        """
        # Guessing templates directory
        if path is None or path == "":
            path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                'templates')
            self.log.info(f"Missing path to templates. Using default...")
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(path))
        env.filters['is_list'] = is_list
        return env.get_template(name)


def main(template, output_file):
    temp = Template()
    temp.render_template(template=template, output_file=output_file)


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(
        description='Generate files from jinja templates')
    my_parser.add_argument('--template',
                           dest='template',
                           type=str,
                           help='Choose a template')
    my_parser.add_argument('--output',
                           dest='output_file',
                           type=str,
                           help='Choose a destination')
    args = my_parser.parse_args()
    main(template=args.template, output_file=args.output_file)
