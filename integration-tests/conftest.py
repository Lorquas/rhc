import pytest
import logging
import sh
import json

"""
curl https://cert.console.redhat.com/api/inventory/v1/hosts?insights_id=<insights-client/machine_id> \
      --cert /etc/pki/consumer/cert.pem \
      --key /etc/pki/consumer/key.pem \
      -k
"""


@pytest.fixture
def fetch_from_inventory(test_config):
    def _wrapper(insights_id):
        hostname = test_config.get("console","host")
        output=sh.curl(f'''https://{hostname}/api/inventory/v1/hosts?insights_id={insights_id}
                           --cert /etc/pki/consumer/cert.pem
                           --key /etc/pki/consumer/key.pem
                           -k'''.split())
        data = json.loads(output)
        return data
    yield _wrapper


@pytest.fixture
def subscription_manager():
    def _wrapper(*args):
        output=sh.subscription_manager(*args)
        return output
    yield _wrapper
