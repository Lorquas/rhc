import sh
import logging


def rhcd_service_status():
    return sh.systemctl("status rhcd".split())


def system_is_connected_to_insights():
    return 'This host is registered' in sh.insights_client("--status")


def rhcd_service_is_active():
    try:
        stdout = sh.systemctl("is-active rhcd".split()).strip()
        return stdout == "active"
    except sh.ErrorReturnCode_3:
        return False
