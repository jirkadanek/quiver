#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import sys as _sys

from plano import *
from quiver.common import *

def open_test_session(session):
    set_message_threshold("warn")

def test_common_options(session):
    commands = [
        "quiver",
        "quiver-arrow",
        "quiver-bench",
        "quiver-launch",
        "quiver-server",
    ]

    for command in commands:
        call("{} --help", command)
        call("{} --version", command)

def test_quiver_arrow(session):
    call("quiver-arrow send q0 --init-only")
    call("quiver-arrow --init-only receive q0")

    for impl in ARROW_IMPLS:
        if impl_exists(impl):
            call("quiver-arrow --impl {} --impl-info", impl)

def test_quiver_server(session):
    for impl in SERVER_IMPLS:
        if not impl_exists(impl):
            continue

        call("quiver-server --impl {} --impl-info", impl)

        if impl == "activemq-artemis":
            # XXX Permissions problem
            continue

        with _TestServer(impl=impl) as server:
            call("quiver {} --count 1", server.url)

def disabled_test_quiver_launch_client_server(session):
    with _TestServer() as server:
        call("quiver-launch {} --count 2 --options \"--count 1\" --verbose", server.url)

def disabled_test_quiver_launch_peer_to_peer(session):
    call("quiver-launch --sender-options=\"--count 1\" --receiver-options=\"--count 1 --server --passive\" --verbose {}", _test_url())

def test_quiver_matching_pairs_client_server_count(session):
    for impl in AMQP_ARROW_IMPLS:
        if not impl_exists(impl):
            continue

        with _TestServer() as server:
            call("quiver {} --arrow {} --count 1 --verbose", server.url, impl)

def test_quiver_matching_pairs_client_server_duration(session):
    for impl in AMQP_ARROW_IMPLS:
        if not impl_exists(impl):
            continue

        if impl in ("qpid-jms", "vertx-proton"):
            # XXX Trouble
            continue

        with _TestServer() as server:
            call("quiver {} --arrow {} --duration 1 --verbose", server.url, impl)

def test_quiver_mixed_pairs_peer_to_peer_count(session):
    for sender_impl in AMQP_ARROW_IMPLS:
        if not impl_exists(sender_impl):
            continue

        for receiver_impl in PEER_TO_PEER_ARROW_IMPLS:
            if not impl_exists(receiver_impl):
                continue

            if sender_impl in ("qpid-proton-c", "qpid-messaging-cpp", "qpid-messaging-python"):
                if receiver_impl in ("rhea"):
                    # XXX Trouble
                    continue

            call("quiver {} --sender {} --receiver {} --count 1 --peer-to-peer --verbose",
                 _test_url(), sender_impl, receiver_impl)

def test_quiver_mixed_pairs_peer_to_peer_duration(session):
    for sender_impl in AMQP_ARROW_IMPLS:
        if not impl_exists(sender_impl):
            continue

        for receiver_impl in PEER_TO_PEER_ARROW_IMPLS:
            if not impl_exists(receiver_impl):
                continue

            if sender_impl in ("qpid-proton-c", "qpid-messaging-cpp", "qpid-messaging-python"):
                if receiver_impl in ("rhea"):
                    # XXX Trouble
                    continue

            if sender_impl in ("qpid-proton-c"):
                # XXX More trouble
                continue

            call("quiver {} --sender {} --receiver {} --duration 1 --peer-to-peer --verbose",
                 _test_url(), sender_impl, receiver_impl)

def test_quiver_bench_client_server(session):
    with temp_dir() as output:
        command = [
            "quiver-bench",
            "--count", "1",
            "--client-server",
            "--include-servers", "builtin",
            "--exclude-servers", "none",
            "--verbose",
            "--output", output,
        ]

        call(command)

def test_quiver_bench_peer_to_peer(session):
    with temp_dir() as output:
        command = [
            "quiver-bench",
            "--count", "1",
            "--peer-to-peer",
            "--verbose",
            "--output", output,
        ]

        call(command)

class _TestServer(object):
    def __init__(self, impl="builtin", **kwargs):
        port = random_port()

        if impl == "activemq":
            port = "5672"

        self.url = "//127.0.0.1:{}/q0".format(port)
        self.ready_file = make_temp_file()

        command = [
            "quiver-server", self.url,
            "--verbose",
            "--ready-file", self.ready_file,
            "--impl", impl,
        ]

        self.proc = start_process(command, **kwargs)
        self.proc.url = self.url

    def __enter__(self):
        for i in range(30):
            if read(self.ready_file) == "ready\n":
                break

            sleep(0.2)

        return self.proc

    def __exit__(self, exc_type, exc_value, traceback):
        stop_process(self.proc)
        remove(self.ready_file)

def _test_url():
    return "//127.0.0.1:{}/q0".format(random_port())
