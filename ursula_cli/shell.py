#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2015, Craig Tracey <craigtracey@gmail.com>
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations

import argparse
import logging
import os
import subprocess
import sys

LOG = logging.getLogger(__name__)
ANSIBLE_VERSION = '1.7.2-bbg'

def _initialize_logger(level=logging.DEBUG, logfile=None):
    global LOG
    LOG.setLevel(level)

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    LOG.addHandler(handler)


def _check_ansible_version():
    version_output = subprocess.check_output(
        ["ansible-playbook --version"], shell=True)
    version_output = version_output.split('\n')[0]
    version = version_output.split(' ')[1]
    if not version == ANSIBLE_VERSION:
        raise Exception("You are not using ansible-playbook '%s'. "
            "Current required version is: '%s'. You may install "
            "the correct version with 'pip install -U -r "
            "requirements.txt'" % (version, ANSIBLE_VERSION))


def _append_envvar(key, value):
    if key in os.environ:
        os.environ[key] = "%s %s" % (os.environ[key], value)
    else:
        os.environ[key] = value


def _set_default_env():
    _append_envvar('ANSIBLE_FORCE_COLOR', 'yes')
    _append_envvar('ANSIBLE_SSH_ARGS', '-o ControlMaster=auto')
    _append_envvar("ANSIBLE_SSH_ARGS",
                   "-o ControlPath=~/.ssh/controlmasters/u-%r@%h:%p")
    _append_envvar("ANSIBLE_SSH_ARGS", "-o ControlPersist=300")


def _run_ansible(inventory, playbook, user='root', module_path='./library', sudo=False,
                extra_args=[]):
    command = [
        'ansible-playbook',
        '--inventory-file',
        inventory,
        '--user',
        user,
        '--module-path',
        module_path,
        playbook,
    ]

    if sudo:
        command.append("--sudo")
    command += extra_args

    LOG.debug("Running command: %s", " ".join(command))
    proc = subprocess.Popen(command, env=os.environ.copy(),
                            stdout=subprocess.PIPE)
    while proc.poll() is None:
        output = proc.stdout.readline()
        print output,
        sys.stdout.flush()


def run(args, extra_args):
    _set_default_env()

    if not os.path.exists(args.environment):
        raise Exception("Environment '%s' does not exist", args.environment)

    inventory = os.path.join(args.environment, 'hosts')
    if not os.path.exists(inventory) or not os.path.isfile(inventory):
        raise Exception("Inventory file '%s' does not exist", inventory)

    if args.forward:
        _append_envvar("ANSIBLE_SSH_ARGS", "-o ForwardAgent=yes")

    _run_ansible(inventory, args.playbook, extra_args=extra_args)


def main():
    parser = argparse.ArgumentParser(description='A CLI wrapper for ansible')
    parser.add_argument('environment', help='The environment you want to use')
    parser.add_argument('playbook', help='The playbook to run')
    parser.add_argument('-f', '--forward', help='Forward SSH agent')
    parser.add_argument('-t', '--test', help='Test syntax for playbook')
    parser.add_argument('-x', '--extra-args', help='Additional arguments '
                                                   'for ansible')
    args, extra_args = parser.parse_known_args()

    try:
        _initialize_logger()
        _check_ansible_version()
        run(args, extra_args)
    except Exception as e:
        LOG.error(e)
        sys.exit(-1)


if __name__ == '__main__':
    main()
