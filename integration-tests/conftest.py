import pytest
import logging
import sh
import json
import os
import toml
import shutil
from dynaconf import Dynaconf


@pytest.fixture
def settings():
    yield Dynaconf(
        envvar_prefix="CSI_CLIENT_TOOLS",
        settings_files=["settings.toml", ".secrets.yaml"],
        environments=True,
        load_dotenv=True,
    )


@pytest.fixture(scope="session")
def fetch_from_inventory(test_config):
    """
    curl https://cert.console.redhat.com/api/inventory/v1/hosts?insights_id=<insights-client/machine_id> \
      --cert /etc/pki/consumer/cert.pem \
      --key /etc/pki/consumer/key.pem \
      -k
    """
    def _wrapper(insights_id):
        hostname = test_config.get("console", "host")
        output = sh.curl(f'''https://{hostname}/api/inventory/v1/hosts?insights_id={insights_id}
                           --cert /etc/pki/consumer/cert.pem
                           --key /etc/pki/consumer/key.pem
                           -k'''.split())
        data = json.loads(output)
        return data

    yield _wrapper


@pytest.fixture(scope="session")
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

    yield _wrapper


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
        global the_config_file_exists
        if os.path.isfile(config_path):
            logging.info(
                f'{config_path} exists. saved to a file {backup_path}')
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


@pytest.fixture
def get_rhc_status():
    """
    (env) [root@jstavel-iqe-rhel93 csi-client-tools]# rhc status --format json
    {
        "hostname": "jstavel-iqe-rhel93",
        "rhsm_connected": true,
        "insights_connected": true,
        "rhcd_running": true
    }
    """
    def _wrapper():
        status = json.loads(sh.rhc("status", "--format", "json"))
        return status
    return _wrapper


@pytest.fixture
def not_registered_system(get_rhc_status):
    """
    If a system is registered it runs 'rhc disconnect' command.
    The fixture ensures that a system is not registered before a test is run.
    """
    rhc_status = get_rhc_status()
    if rhc_status.get("rhsm_connected"):
        sh.rhc("disconnect")
        return get_rhc_status()
    return rhc_status


@pytest.fixture
def registered_system(get_rhc_status, settings):
    rhc_status = get_rhc_status()
    if rhc_status.get("rhsm_connected"):
        return rhc_status
    sh.rhc("connect",
           "--username", settings.get("candlepin.username"),
           "--password", settings.get("candlepin.password"))
    return get_rhc_status()
