import logging
import sh
from packaging import version
import pytest


def test_rhc_version(subtests):
    """
    # rhc --version
    rhc version 0.2.4

    The application should provide a version number of the application.
    The version number complies with https://packaging.python.org/en/latest/specifications/version-specifiers/
    """
    with subtests.test("RHC version"):
        out = sh.rhc("--version")
        assert "rhc version" in out

    with subtests.test("RHC version in the proper format"):
        version_string = out.strip()
        rhc_version = version.parse(version_string.split()[2])
        assert isinstance(rhc_version, version.Version) is True


def test_rhc_connect_disconnect(not_registered_system, get_rhc_status, settings, subtests):
    """
    An application allows use to connect/disconnect the actual system to/from the main service.

    # rhc connect
    ... it will connect a system to Red Hat services
    ... it will prompt for username and password
    ... it will inform a user about connection progress


    # rhc disconnect
    ... it will disconnect from all Red Hat services
    ... it will inform a user how it goes
    """
    with subtests.test(msg="RHC connect"):
        out = sh.rhc('connect',
                     '--username', settings.get("candlepin.username"),
                     '--password', settings.get("candlepin.password"),
                     )
        logging.info(f'result is {out}')
        assert "Successfully connected to Red Hat!" in out
        status = get_rhc_status()
        assert status.get('rhsm_connected'), \
            "'rhc status' should return the actual state of the system registration"

    with subtests.test(msg="RHC disconnect"):
        out = sh.rhc('disconnect')
        logging.info(f'result of disconnect task: {out}')
        assert not get_rhc_status().get('rhsm_connected')
        assert "Disconnected from Red Hat Subscription Management" in out, \
            "The application should inform a system is disconnected from Red Hat Subscription Management"
        assert "Disconnected from Red Hat Insights" in out, \
            "The application should inform a system is disconnected from Red Hat Insights"


def test_rhc_connect_with_wrong_credentials(not_registered_system, settings, subtests):
    """
    The application handles a case when a user provides wrong credentials.
    The application should help a user to solve this mistake.
    It prints a helpful message to do so.
    """
    with subtests.test(msg="Wrong password"):
        out = sh.rhc('connect',
                     '--username', settings.get("candlepin.username"),
                     '--password', "WRONG-PASSWORD",
                     _ok_code=(0, 1))

        logging.info(f'result is {out}')
        assert "error: Invalid username or password" in out, \
            "The application informs about wrong credentials"
        assert "To create a login, please visit https://www.redhat.com/wapps/ugc/register.html" in out, \
            "The application offers a way to fix it"
        assert "Traceback" not in out, \
            "No traceback appears in an application response"

    with subtests.test(msg="Wrong username"):
        out = sh.rhc('connect',
                     '--username', "WRONG-USERNAME",
                     '--password', settings.get('candlepin.password'),
                     _ok_code=(0, 1))

        logging.info(f'result is {out}')
        assert "error: Invalid username or password" in out, \
            "The application informs about wrong credentials"
        assert "To create a login, please visit https://www.redhat.com/wapps/ugc/register.html" in out, \
            "The application offers a way to fix it"
        assert "Traceback" not in out, \
            "No traceback appears in an application response"


def test_rhc_connect_when_connected(registered_system, settings, subtests):
    """
    The application handles a case when a system is already connected to Red Hat services.
    There is no error message or traceback in an application reponse.
    """
    out = sh.rhc('connect',
                 '--username', settings.get('candlepin.username'),
                 '--password', settings.get('candlepin.password')
                 )
    logging.info(f'result of the connect command: {out}')
    assert "This might take a few seconds." in out, \
        "Application should inform about an activation progress"
    assert "This system is already connected to Red Hat Subscription Management" in out, \
        "Application should inform about connecting to Red Hat Subscription Management"
    assert "Traceback" not in out, \
        "No traceback appears in an application response"


def test_rhc_status(not_registered_system):
    """
    The applications provides a status of connection to Red Hat services.
    """
    out = sh.rhc("status")
    logging.info(f'rhc status is: {out}')
    assert "Not connected to Red Hat Subscription Management" in out, \
        "Application should inform about status of connection to Red Hat Subscription Management"
    assert "Not connected to Red Hat Insights" in out, \
        "Application should inform about status of connection to Red Hat Insights"


@pytest.mark.env('stage')
def test_rhc_connect_with_activation_key(not_registered_system, settings):
    """
    User can connect a system to a service using activation key.
    It is necessary to specify organization in this case.
    """
    status = not_registered_system
    logging.info(f"status of registration: {status}")
    logging.info(f"activation key is: {settings.candlepin.activation_key}")
    out = sh.rhc("connect",
                 "--activation-key", settings.get('candlepin.activation_key'),
                 "--organization", settings.get('candlepin.org')
                 )
    logging.info(f'rhc connect response: {out}')
    assert "Successfully connected to Red Hat!" in out, \
        "Application should inform about connection to Red Hat Subscription Management"
    assert "Connected to Red Hat Insights" in out, \
        "Application should inform about connection to Red Hat Insights service"
    assert "Activated the Remote Host Configuration daemon" in out, \
        "Application should inform that RHCD service has been started"
