#!/bin/bash -e
set -o pipefail

PARENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

if [ ! -d "${PARENT_DIR}/virtualenv" ]; then
  echo 'Creating virtualenv...'
  python3 -m venv "${PARENT_DIR}/virtualenv"
  echo 'Created virtualenv.'
fi

. "${PARENT_DIR}/virtualenv/bin/activate"

echo 'Installing requirements...'
pip install -q --upgrade pip
pip install -q -r "${PARENT_DIR}/requirements.txt"
echo 'Installed requirements.'
