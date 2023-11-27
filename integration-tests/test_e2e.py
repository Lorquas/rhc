import jmespath
import re
import sh
import os
import funcy
import pytest

"""
Tests related to ingress service. The service provides information
about every system that is connected to the account.
"""


@pytest.mark.env('stage')
def test_rhc_fetch_from_inventory(not_registered_system,
                                  settings,
                                  get_rhc_status,
                                  fetch_from_inventory,
                                  subtests):
    """
    rhc client can download inventory file from ingress service.
    There are all important fields in the inventory file.
    """
    sh.rhc('connect',
           '--username', settings.get("candlepin.username"),
           '--password', settings.get("candlepin.password"),
           )
    assert get_rhc_status().get('rhsm_connected')

    machine_id = open("/etc/insights-client/machine-id", "rt").read().strip()
    data = fetch_from_inventory(insights_id=machine_id)
    inventory_record = jmespath.search(
        f"results[?insights_id=='{machine_id}'] | [0]", data)

    with subtests.test(msg="Insights info in inventory"):
        assert machine_id == inventory_record.get('insights_id'), \
            "insights_id in the returned record should be the same as the one in /etc/insights-client/machine-id"

    """
    >> /usr/sbin/subscription-manager identity

    Fetching organizations ...
    system identity: b618cfee-db40-480a-a276-df9f1762df6a
    name: jstavel-iqe-rhel93
    org name: 16769664
    org ID: 16769664
    """
    output = sh.subscription_manager("identity")

    def parse_output(output):
        data = dict([re.split(r': +', line)
                    for line in output.splitlines() if re.search(r"[^:]+: +", line)])
        return data

    with subtests.test(msg="Subscription Management info in inventory"):
        identity = parse_output(output)
        assert inventory_record["subscription_manager_id"] == identity["system identity"], \
            "Id in an inventory record should be the same as 'subscription-manager identity' provides"
        assert inventory_record["org_id"] == identity["org ID"], \
            "Organization ID in an inventory record should be the same as 'subscription-manager identity' provides"


@pytest.mark.env('stage')
def test_rhc_tags_in_inventory(not_registered_system,
                               settings,
                               fetch_from_inventory,
                               fetch_tags_from_inventory,
                               set_rhc_tags,
                               get_rhc_status,
                               subtests):
    """
    There is a file 'tags.toml' in /etc/rhc/.
    The file consist of tags that specify a connected system somehow.
    An inventory file fetched from ingress service should consist of each specified tag.
    """
    test_tags = {"uptime": "99.999",
                 "production": "true", "region": "us-east-1"}
    set_rhc_tags(test_tags)

    sh.rhc('connect',
           '--username', settings.get("candlepin.username"),
           '--password', settings.get("candlepin.password"),
           )
    assert get_rhc_status().get("rhsm_connected")
    assert 'This host is registered' in sh.insights_client("--status"), \
        "A system should be registered to Insights service after 'rhc connect'"

    assert os.path.isfile("/etc/insights-client/machine-id"), \
        "a file /etc/insights-client/machine-id should be presented after a system is connected"

    machine_id = open("/etc/insights-client/machine-id", "rt").read().strip()
    data = fetch_from_inventory(insights_id=machine_id)
    inventory_record = jmespath.search(
        f"results[?insights_id=='{machine_id}'] | [0]", data)
    assert "id" in inventory_record, \
        "a key 'id' is a mandatory in inventory record"
    host_id = inventory_record['id'].strip()
    response = fetch_tags_from_inventory(host_id)
    """
    {'total': 1, 'count': 1, 'page': 1, 'per_page': 50,
     'results': {'eb4f0dd6-60df-4e3c-82a6-d05bccc0a12e': [{'namespace': 'rhc_client', 'key': 'region', 'value': 'us-east-1'},
                                                          {'namespace': 'rhc_client', 'key': 'uptime', 'value': '99.999'},
                                                          {'namespace': 'rhc_client', 'key': 'production', 'value': 'true'}]}}
    """
    tags_in_inventory = funcy.get_in(response, ['results', host_id])
    tags = dict([(item['key'].strip(), item['value'].strip())
                for item in tags_in_inventory])
    assert test_tags == tags, "Tags returned from api should be the same as the ones in /etc/rhc/tags.toml"
