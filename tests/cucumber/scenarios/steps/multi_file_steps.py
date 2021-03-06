"""Author: Jakub Kudzia
Copyright (C) 2015 ACK CYFRONET AGH
This software is released under the MIT license cited in 'LICENSE.txt'

Module implements common steps for operation on files (both regular files
and directories)in multiclient environment.
"""

import pytest
from pytest_bdd import (given, when, then)
from pytest_bdd import parsers

from environment import docker, env
from common import *


@when(parsers.parse('{user} updates {files} timestamps on {client_node}'))
@when(parsers.parse('{user} creates regular files {files} on {client_node}'))
def create_reg_file(user, files, client_node, context):
    client = get_client(client_node, user, context)
    files = list_parser(files)
    for file in files:
        ret = run_cmd(user, client, 'touch ' + make_path(file, client))
        save_op_code(context, user, ret)
        if ret == 0:
            context.update_timestamps(user, client, file)


@when(parsers.parse('{user} sees {files} in {path} on {client_node}'))
@then(parsers.parse('{user} sees {files} in {path} on {client_node}'))
def ls_present(user, files, path, client_node, context):
    client = get_client(client_node, user, context)
    cmd = 'ls ' + make_path(path, client)
    ls_files = run_cmd(user, client, cmd, output=True).split()
    files = list_parser(files)
    for file in files:
        assert file in ls_files


@when(parsers.parse('{user} doesn\'t see {files} in {path} on {client_node}'))
@then(parsers.parse('{user} doesn\'t see {files} in {path} on {client_node}'))
def ls_absent(user, files, path, client_node, context):
    client = get_client(client_node, user, context)
    cmd = 'ls ' + make_path(path, client)
    ls_files = run_cmd(user, client, cmd, output=True).split()
    files = list_parser(files)
    for file in files:
        assert file not in ls_files


@when(parsers.parse('{user} renames {file1} to {file2} on {client_node}'))
def rename(user, file1, file2, client_node, context):
    client = get_client(client_node, user, context)
    ret = run_cmd(user, client, "mv " + make_path(file1, client) + ' ' + make_path(file2, client))
    save_op_code(context, user, ret)
    if ret == 0:
        context.update_timestamps(user, client, file2)


@when(parsers.parse('{user} deletes files {files} on {client_node}'))
def delete_file(user, files, client_node, context):
    client = get_client(client_node, user, context)
    files = list_parser(files)
    for file in files:
        ret = run_cmd(user, client, "rm " + make_path(file, client))
        save_op_code(context, user, ret)


@then(parsers.parse('file type of {user}\'s {file} is {fileType} on {client_node}'))
def check_type(user, file, fileType, client_node, context):
    client = get_client(client_node, user, context)
    currFileType = run_cmd(user, client, 'stat ' + make_path(file, client) + ' --format=%F', output=True)
    assert fileType == currFileType


@then(parsers.parse('mode of {user}\'s {file} is {mode} on {client_node}'))
def check_mode(user, file, mode, client_node, context):
    client = get_client(client_node, user, context)
    curr_mode = run_cmd(user, client, 'stat --format=%a ' + make_path(file, client), output=True)
    assert mode == curr_mode


@when(parsers.parse('{user} changes {file} mode to {mode} on {client_node}'))
def change_mode(user, file, mode, client_node, context):
    client = get_client(client_node, user, context)
    mode = str(mode)
    ret = run_cmd(user, client, 'chmod ' + mode + ' ' + make_path(file, client))
    save_op_code(context, user, ret)
    if ret == 0:
        context.update_timestamps(user, client, file)


@when(parsers.parse('size of {user}\'s {file} is {size} bytes on {client_node}'))
@then(parsers.parse('size of {user}\'s {file} is {size} bytes on {client_node}'))
def check_size(user, file, size, client_node, context):
    client = get_client(client_node, user, context)
    curr_size = run_cmd(user, client,
                        "stat --format=%s " + make_path(file, client),
                        output=True)
    assert size == curr_size


@then(parsers.parse('{time1} time of {user}\'s {file} is {comparator} to {time2} time on {client_node}'))
@then(parsers.parse('{time1} time of {user}\'s {file} is {comparator} than {time2} time on {client_node}'))
def check_time(user, time1, time2, comparator, file, client_node, context):
    client = get_client(client_node, user, context)
    opt1 = get_time_opt(time1)
    opt2 = get_time_opt(time2)
    file = str(file)
    time1 = run_cmd(user, client, "stat --format=%" + opt1 + ' ' + make_path(file, client), output=True)
    time2 = run_cmd(user, client, "stat --format=%" + opt2 + ' ' + make_path(file, client), output=True)
    assert compare(int(time1), int(time2), comparator)


####################################################################################################


def get_time_opt(time):
    if time == "access":
        return 'X'
    elif time == "modification":
        return 'Y'
    elif time == "status-change":
        return 'Z'
    else:
        raise ValueError("Wrong argument to function get_time_opt")


def compare(val1, val2, comparator):
    if comparator == 'equal':
        return val1 == val2
    elif comparator == 'not equal':
        return val1 != val2
    elif comparator == 'greater':
        return val1 > val2
    elif comparator == 'less':
        return val1 < val2
    elif comparator == 'not greater':
        return val1 <= val2
    elif comparator == 'not less':
        return val1 >= val2
    else:
        raise ValueError("Wrong argument comparator to function compare")
