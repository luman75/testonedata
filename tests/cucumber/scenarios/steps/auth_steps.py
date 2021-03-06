"""
Author: Piotr Ociepka
Author: Jakub Kudzia
Copyright (C) 2015 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Module implements pytest-bdd steps for authorization and mounting oneclient.
"""

import pytest
from pytest_bdd import (given, when, then)
from pytest_bdd import parsers

import subprocess
import sys
import time

from environment import docker, env
from common import *


@given(parsers.parse('{users} start oneclients {client_instances} in\n' +
                     '{mount_paths} on client_hosts\n' +
                     '{client_hosts} respectively,\n' +
                     'using {tokens}'))
def multi_mount(users, client_instances, mount_paths, client_hosts, tokens, environment, context, client_ids):

    users = list_parser(users)
    client_instances = list_parser(client_instances)
    mount_paths = list_parser(mount_paths)
    client_hosts = list_parser(client_hosts)
    tokens = list_parser(tokens)

    # current version is for environment with one GR
    gr_node = environment['gr_nodes'][0]

    set_dns(environment)

    client_data = environment['client_data']

    for i in range(len(users)):
        user = str(users[i])
        client_instance = str(client_instances[i])
        mount_path = str(mount_paths[i])
        client_host = client_hosts[i]
        data = client_data[client_host][client_instance]

        token_arg = str(tokens[i])

        # get token for user
        token = get_token(token_arg, user, gr_node)

        # create client object
        client = Client(client_ids[client_host], mount_path)

        # clean if there is directory in the mount_path
        if run_cmd(user, client, "ls " + mount_path) == 0:
            clean_mount_path(user, client)

        token_path = "/tmp/token"

        cmd = 'mkdir -p ' + mount_path + \
              ' && export GLOBAL_REGISTRY_URL=' + data['gr_domain'] + \
              ' && export PROVIDER_HOSTNAME=' + data['op_domain'] + \
              ' && export X509_USER_CERT=' + data['user_cert'] + \
              ' && export X509_USER_KEY=' + data['user_key'] + \
              ' && echo ' + token + ' > ' + token_path + \
              ' && ./oneclient --authentication token --no_check_certificate ' + mount_path + \
              ' < ' + token_path + \
              ' && rm ' + token_path

        ret = run_cmd(user, client, cmd)

        if token_arg != "bad token":
            # if token was different than "bad token", check if logging succeeded
            assert ret == 0

        if user in context.users:
            context.users[user].clients[client_instance] = client
        else:
            context.users[user] = User(client_instance, client)

        # remove accessToken to mount many clients on one docker
        run_cmd(user, client,
                "rm -rf " + os.path.join(os.path.dirname(mount_path), ".local"))

        save_op_code(context, user, ret)


@given(parsers.parse('{user} starts oneclient in {mount_path} using {token}'))
def default_mount(user, mount_path, token, environment, context, client_ids):
    multi_mount(make_arg_list(user), make_arg_list("client1"), make_arg_list(mount_path),
                make_arg_list('client_host_1'), make_arg_list(token), environment, context, client_ids)


@then(parsers.parse('{spaces} are mounted for {user}'))
def check_spaces(spaces, user, context):
    time.sleep(3)
    # sleep to be sure that environment is up
    spaces = list_parser(spaces)
    user = str(user)
    for client_instance, client in context.users[user].clients.items():
        spaces_in_client = run_cmd(user, client, 'ls ' + make_path("spaces", client), output=True)
        spaces_in_client = spaces_in_client.split("\n")
        for space in spaces:
            assert space in spaces_in_client


####################################################################################################


def clean_mount_path(user, client):

    # if directory spaces exists
    if run_cmd(user, client, 'ls ' + make_path('spaces', client)) == 0:
        spaces = run_cmd(user, client, 'ls ' + make_path('spaces', client), output=True)
        spaces = spaces.split("\n")
        # clean spaces
        for space in spaces:
            run_cmd(user, client, "rm -rf " + make_path('spaces/' + space + '/*', client))

    # get pid of running oneclient node
    pid = run_cmd('root', client,
                  " | ".join(
                      ["ps aux",
                       "grep './oneclient --authentication token --no_check_certificate '" + client.mount_path,
                       "grep -v 'grep'",
                       "awk '{print $2}'"]),
                  output=True)

    if pid != "":
        # kill oneclient process
        run_cmd("root", client, "kill -KILL " + str(pid))

    # unmount onedata
    run_cmd(user, client, "fusermount -u " + client.mount_path)

    # remove onedata dir
    run_cmd("root", client, "rm -rf " + client.mount_path)


def set_dns(environment):
    with open("/etc/resolv.conf", "w") as conf:
        dns = environment['dns']
        conf.write("nameserver " + dns)


def get_token(token, user, gr_node):
    if token == "bad token":
        token = "bad_token"
    elif token == "token":
        token = subprocess.check_output(
            ['./tests/cucumber/scenarios/utils/get_token.escript', gr_node, user],
            stderr=subprocess.STDOUT)
    return token
