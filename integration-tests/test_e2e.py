import logging
import jmespath
import json
import re
from functools import partial

def test_rhc_fetch_from_inventory(fetch_from_inventory, subscription_manager, subtests):
    machine_id=open("/etc/insights-client/machine-id","rt").read().strip()    
    data = fetch_from_inventory(insights_id=machine_id)
    inventory_record = jmespath.search(f"results[?insights_id=='{machine_id}'] | [0]",data)

    with subtests.test(msg="Insights info in inventory"):
        assert machine_id == inventory_record.get('insights_id'),\
            "insights_id in the returned record should be the same as the one in /etc/insights-client/machine-id"
    
    """
    >> /usr/sbin/subscription-manager identity

    Fetching organizations ...
    system identity: b618cfee-db40-480a-a276-df9f1762df6a
    name: jstavel-iqe-rhel93
    org name: 16769664
    org ID: 16769664
    """
    output = subscription_manager("identity")
    def parse_output(output):
        data = dict([re.split(r': +',line) for line in output.splitlines() if re.search(r"[^:]+: +",line)])
        return data

    with subtests.test(msg="Subscription Management info in inventory"):
        identity = parse_output(output)
        assert inventory_record["subscription_manager_id"] == identity["system identity"],\
            "Id in an inventory record should be the same as 'subscription-manager identity' provides"
        assert inventory_record["org_id"] == identity["org ID"],\
            "Organization ID in an inventory record should be the same as 'subscription-manager identity' provides"
