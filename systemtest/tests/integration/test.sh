#!/bin/bash
set -eu
set -x

. /etc/os-release
VERSION_MAJOR=$(echo $VERSION_ID | cut -d. -f 1)
case "${ID}" in
  rhel)
    ;;
  *)
    curl --output-dir /etc/yum.repos.d/ -O \
      "https://ftp.redhat.com/redhat/client-tools/client-tools-for-rhel-${VERSION_MAJOR}.repo"
    curl -o /etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release \
      https://www.redhat.com/security/data/fd431d51.txt
    ;;
esac

# get to project root
cd ../../../

dnf --setopt install_weak_deps=False install -y \
  subscription-manager \
  insights-client \
  podman git-core python3-pip python3-pytest

python3 -m venv venv
# shellcheck disable=SC1091
. venv/bin/activate

pip install -r integration-tests/requirements.txt

pytest -v integration-tests
