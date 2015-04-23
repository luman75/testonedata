from tests import testutil
import json
import socket
import time
import os
import sys

appmock_dir = os.path.join(os.getcwd(), 'appmock')
sys.path.insert(0, appmock_dir)
bamboos_dir = os.path.join(os.getcwd(), 'bamboos', 'docker')
sys.path.insert(0, bamboos_dir)
from appmock import appmock_client
from environment import docker, env


class TestEnvUp:
    @classmethod
    # Run the evn_up.py script, capture and parse the output
    def setup_class(cls):
        cls.result = env.up(testutil.test_file('env.json'))

    @classmethod
    # Clean up removing all dockers created in the test
    def teardown_class(cls):
        docker.remove(cls.result['docker_ids'], force=True, volumes=True)

    # Test if the env_up.py script works as expected.
    def test_env_up(self):
        # For shorter code
        res = self.result
        # Check if number of started dockers is correct
        # The number should be:
        # 2 for skydns and skydock
        # 3 OP nodes
        # 1 Riak node for OP
        # 2 GR nodes
        # 2 DBs for GR nodes
        # 2 appmock nodes
        # 2 client nodes
        # ------------
        # 14 nodes
        assert 14 == len(res['docker_ids'])
        # Get the DNS ip
        dns = res['dns']
        # Will throw if the dns address is not legal
        socket.inet_aton(dns)
        # Check connectivity to system components using the DNS
        # Check GR nodes
        # gr_node is in form name@name.timestamp.dev.docker
        for gr_node in res['gr_nodes']:
            (gr_name, sep, gr_hostname) = gr_node.partition('@')
            gr_ip = testutil.dns_lookup(gr_hostname, dns)
            assert testutil.ping(gr_ip)
            assert check_http_connectivity(gr_ip, 443, '/', 200, number_of_retries=50)

        # Check GR DB nodes
        # gr_db_node is in form name@name.timestamp.dev.docker
        for gr_db_node in res['gr_db_nodes']:
            (gr_db_name, sep, gr_db_hostname) = gr_db_node.partition('@')
            gr_db_ip = testutil.dns_lookup(gr_db_hostname, dns)
            assert testutil.ping(gr_db_ip)
            assert check_http_connectivity(gr_db_ip, 5984, '/_utils/', 200, use_ssl=False, number_of_retries=50)

        # Check OP CCM nodes
        # ccm_node is in form name@name.timestamp.dev.docker
        for ccm_node in res['op_ccm_nodes']:
            (ccm_name, sep, ccm_hostname) = ccm_node.partition('@')
            ccm_ip = testutil.dns_lookup(ccm_hostname, dns)
            assert testutil.ping(ccm_ip)

        # Check OP worker nodes
        # w_node is in form name@name.timestamp.dev.docker
        for w_node in res['op_worker_nodes']:
            (w_name, sep, w_hostname) = w_node.partition('@')
            w_ip = testutil.dns_lookup(w_hostname, dns)
            assert testutil.ping(w_ip)
            assert check_http_connectivity(w_ip, 443, '/', 200, number_of_retries=50)

        # Check appmock nodes
        # am_node is in form name@name.timestamp.dev.docker
        for am_node in res['appmock_nodes']:
            (am_name, sep, am_hostname) = am_node.partition('@')
            am_ip = testutil.dns_lookup(am_hostname, dns)
            assert testutil.ping(am_ip)
            assert check_http_connectivity(am_ip, 443, '/test2', 200, number_of_retries=50)

        # Check client nodes
        # oc_node is in form name.timestamp.dev.docker
        for oc_node in res['client_nodes']:
            oc_ip = testutil.dns_lookup(oc_node, dns)
            assert testutil.ping(oc_ip)


# Helper function to check https connectivity
# Retries once a second, up to given number of times.
def check_http_connectivity(ip, port, path, expected_code, use_ssl=True, number_of_retries=20):
    if number_of_retries == 0:
        protocol = 'https' if use_ssl else 'http'
        raise Exception('{0}://{1}:{2}{3} is unreachable.'.format(protocol, ip, port, path))
    else:
        try:
            status_code, _, _ = testutil.http_get(ip, port, path, use_ssl)
            return expected_code == status_code
        except:
            time.sleep(1)
            return check_http_connectivity(ip, port, path, expected_code, use_ssl, number_of_retries - 1)

