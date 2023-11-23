import logging
from sh import rhc
from functools import partial
from packaging import version


def test_version(rhc, subtests):
    """
    # rhc --version
    rhc version 0.2.4

    The application should provide a version number of the application.
    The version number complies with https://packaging.python.org/en/latest/specifications/version-specifiers/
    """
    with subtests.test("RHC version"):
        proc = rhc.run("--version")
        assert b"rhc version" in proc.stdout

    with subtests.test("RHC version in the proper format"):
        version_string = proc.stdout.decode().strip()
        rhc_version = version.parse(version_string.split()[2])
        assert isinstance(rhc_version, version.Version) is True


def test_rhc_connect_disconnect(external_candlepin, test_config, rhc, subtests):
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
    assert not rhc.is_registered
    candlepin_config = partial(test_config.get, "candlepin")
    with subtests.test(msg="RHC connect"):
        proc = rhc.connect(
            username=candlepin_config("username"),
            password=candlepin_config("password"),
        )
        logging.info(f'result is {proc.stdout}')
        assert "Successfully connected to Red Hat!" in proc.stdout.decode()
        assert rhc.is_registered

    with subtests.test(msg="RHC disconnect"):
        proc = rhc.disconnect()

        proc_stdout = proc.stdout.decode()
        logging.info(f'result of disconnect task: {proc.stdout}')
        assert not rhc.is_registered
        assert "Disconnected from Red Hat Subsription Management" in proc_stdout, \
            "The application should inform a system is disconnected from Red Hat Subscription Management"
        assert "Disconnected from Red Hat Insights" in proc_stdout, \
            "The application should inform a system is disconnected from Red Hat Insights"


def test_rhc_connect_with_wrong_credentials(any_candlepin, test_config, rhc, subtests):
    """
    The application handles a case when a user provides wrong credentials.
    The application should help a user to solve this mistake.
    It prints a helpful message to do so.
    """
    assert not rhc.is_registered
    candlepin_config = partial(test_config.get, "candlepin")
    with subtests.test(msg="Wrong password"):
        proc = rhc.connect(
            username=candlepin_config("username"),
            password="WRONG-PASSWORD",
        )
        logging.info(f'result is {proc.stdout}')
        proc_stdout = proc.stdout.decode()
        proc_stderr = proc.stderr.decode()
        assert "error: Invalid username or password" in proc_stdout, \
            "The application informs about wrong credentials"
        assert "To create a login, please visit https://www.redhat.com/wapps/ugc/register.html" in proc_stdout, \
            "The application offers a way to fix it"
        assert "Traceback" not in proc_stdout + proc_stderr, \
            "No traceback appears in an application response"

    with subtests.test(msg="Wrong username"):
        proc = rhc.connect(
            username="WRONG-USERNAME",
            password=candlepin_config("username"),
        )
        logging.info(f'result is {proc.stdout}')
        proc_stdout = proc.stdout.decode()
        proc_stderr = proc.stderr.decode()
        assert "error: Invalid username or password" in proc_stdout, \
            "The application informs about wrong credentials"
        assert "To create a login, please visit https://www.redhat.com/wapps/ugc/register.html" in proc_stdout, \
            "The application offers a way to fix it"
        assert "Traceback" not in proc_stdout + proc_stderr, \
            "No traceback appears in an application response"


def test_rhc_connect_when_connected(any_candlepin, test_config, rhc, subtests):
    """
    The application handles a case when a system is already connected to Red Hat services.
    There is no error message or traceback in an application reponse.
    """
    assert not rhc.is_registered
    candlepin_config = partial(test_config.get, "candlepin")
    rhc.connect(
        username=candlepin_config("username"),
        password=candlepin_config("password"),
    )
    proc_02 = rhc.connect(
        username=candlepin_config("username"),
        password=candlepin_config("password"),
    )
    logging.info(f'result of the second connect: {proc_02.stdout}')
    proc_02_stdout = proc_02.stdout.decode()
    proc_02_stderr = proc_02.stderr.decode()
    assert "This might take a few seconds." in proc_02_stdout, \
        "Application should inform about an activation progress"
    assert "This system is already connected to Red Hat Subscription Management" in proc_02_stdout, \
        "Application should inform about connecting to Red Hat Subscription Management"
    assert "Enabled console.redhat.com services" in proc_02_stdout, \
        "Application should inform about console.redhat.com service"
    assert "Traceback" not in proc_02_stdout + proc_02_stderr, \
        "No traceback appears in an application response"


def test_rhc_status(external_candlepin, rhc):
    """
    The applications provides a status of connection to Red Hat services.
    """
    assert not rhc.is_registered
    proc = rhc.run("status")
    logging.info(f'rhc status is: {proc.stdout}')
    decoded_stdout = proc.stdout.decode()
    assert "Not connected to Red Hat Subscription Management" in decoded_stdout, \
        "Application should inform about status of connection to Red Hat Subscription Management"
    assert "Not connected to Red Hat Insights" in decoded_stdout, \
        "Application should inform about status of connection to Red Hat Insights"


def test_rhc_connect_with_activation_key(not_registered_system, settings):
    """
    User can connect a system to a service using activation key.
    It is necessary to specify organization in this case.
    """
    status = not_registered_system
    logging.info(f"status of registration: {status}")
    logging.info(f"activation key is: {settings.candlepin.activation_key}")
    out = rhc("connect",
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
