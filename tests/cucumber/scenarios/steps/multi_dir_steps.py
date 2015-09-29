"""
Author: Jakub Kudzia
Copyright (C) 2015 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Module implements pytest-bdd steps for operations on directories in multiclient environment.
"""

import pytest
from pytest_bdd import (given, when, then)
from pytest_bdd import parsers
import time

from environment import docker, env
from common import *

# TODO this  step is not used
# @given(parsers.parse('{clients} are in spaces {spaces}'))
# def goto_space(users, spaces, context):
#     clients = list_parser(users)
#     spaces = list_parser(spaces)
#     dict = zip(clients, spaces)
#     for user in dict:
#         context.space_path = make_path(context, "spaces/"+space)


@when(parsers.parse('{user} creates directories {dirs} on oneclient node {client_node}'))
@when(parsers.parse('{user} creates directories {dirs}\non oneclient node {client_node}'))
def create(user, dirs, client_node, context):
    dirs = list_parser(dirs)
    client = context.users[user].clients[client_node]
    for dir in dirs:
        ret = run_cmd(client, ["mkdir", make_path(dir, client)])
    save_op_code(context, user, ret)


@when(parsers.parse('{user} creates directory and parents {paths} on oneclient node {client_node}'))
@when(parsers.parse('{user} creates directory and parents {paths}\non oneclient node {client_node}'))
def create_parents(user, paths, client_node, context):
    client = get_client(client_node, user, context)
    paths = list_parser(paths)
    for path in paths:
        ret = run_cmd(client, ["mkdir", "-p", make_path(path, client)])
        save_op_code(context, user, ret)


@when(parsers.parse('{user} deletes empty directories {dirs} on oneclient node {client_node}'))
def delete_empty(user, dirs, client_node, context):
    client = get_client(client_node, user, context)
    dirs = list_parser(dirs)
    for dir in dirs:
        ret = run_cmd(client, ["rmdir", make_path(dir, client)])
        save_op_code(context, user, ret)


@when(parsers.parse('{user} deletes non-empty directories {dirs} on oneclient node {client_node}'))
def delete_non_empty(user, dirs, client_node, context):
    client = get_client(client_node, user, context)
    dirs = list_parser(dirs)
    for dir in dirs:
        ret = run_cmd(client, ["rm", "-rf", make_path(dir, client)])
        save_op_code(context, user, ret)


@when(parsers.parse('{user} deletes empty directory and parents {paths} on ' +
                    'oneclient node {client_node}'))
def delete_parents(user, paths, client_node, context):
    client = get_client(client_node, user, context)
    paths = list_parser(paths)
    for path in paths:
        ret = run_cmd(client, "cd " + client.mount_path + " && rmdir -p " + str(path))
        save_op_code(context, user, ret)


@when(parsers.parse('{user} copies directory {dir1} to {dir2} on oneclient node {client_node}'))
def copy_dir(user, dir1, dir2, client_node, context):
    client = get_client(client_node, user, context)
    ret = run_cmd(client, ["cp", "-r", make_path(dir1, client), make_path(dir2, client)])
    save_op_code(context, user, ret)
