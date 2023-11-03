import pytest
import logging
import sh
import json
import os
import toml
import shutil

"""
curl https://cert.console.redhat.com/api/inventory/v1/hosts?insights_id=<insights-client/machine_id> \
      --cert /etc/pki/consumer/cert.pem \
      --key /etc/pki/consumer/key.pem \
      -k
"""


@pytest.fixture
def fetch_from_inventory(test_config):
    def _wrapper(insights_id):
        hostname = test_config.get("console", "host")
        output = sh.curl(f'''https://{hostname}/api/inventory/v1/hosts?insights_id={insights_id}
                           --cert /etc/pki/consumer/cert.pem
                           --key /etc/pki/consumer/key.pem
                           -k'''.split())
        data = json.loads(output)
        return data

    yield _wrapper


@pytest.fixture
def fetch_tags_from_inventory(test_config):
    def _wrapper(host_id, params=None):
        hostname = test_config.get("console", "host")
        response = sh.curl(f'''https://{hostname}/api/inventory/v1/hosts/{host_id}/tags
                           --cert /etc/pki/consumer/cert.pem
                           --key /etc/pki/consumer/key.pem
                           -k'''.split())

        # logger.info(f"Fetching host tags from inventory. Url: {url} - params: {params}")
        data = json.loads(response)
        return data

    return _wrapper


@pytest.fixture
def subscription_manager():
    def _wrapper(*args):
        output = sh.subscription_manager(*args)
        return output

    yield _wrapper


@pytest.fixture
def set_rhc_tags():
    config_path = "/etc/rhc/tags.toml"
    backup_path = f'{config_path}.orig'
    the_config_file_exists = False

    def _wrapper(tags: dict):
        # save the original file before
        if os.path.isfile(config_path):
            logging.info(f'{config_path} exists. saved to a file {backup_path}')
            the_config_file_exists = True
            shutil.move(config_path, backup_path)
        with open("/etc/rhc/tags.toml", "w") as f:
            toml.dump(tags, f)

    yield _wrapper

    # return the original file back if the one exists
    if the_config_file_exists:
        if os.path.isfile(backup_path):
            shutil.move(backup_path, config_path)
    else:
        if os.path.isfile(config_path):
            os.remove(config_path)
