import sh
import logging

def show_rhcd_service_status():
    sh.systemctl("status rhcd".split())

def rhcd_service_is_active():
    try:
        stdout = sh.systemctl("is-active rhcd".split()).strip()
        return stdout == "active"
    except sh.ErrorReturnCode_3:
        return False
