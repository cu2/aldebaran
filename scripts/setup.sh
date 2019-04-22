#!/usr/bin/env bash
set -eu
set -o pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

if [ ! -d "${ROOT_DIR}/virtualenv" ]; then
  echo 'Creating virtualenv...'
  python3 -m venv "${ROOT_DIR}/virtualenv"
  echo 'Created virtualenv.'
fi

. "${ROOT_DIR}/virtualenv/bin/activate"

echo 'Installing requirements...'
pip install -q --upgrade pip
pip install -q -r "${ROOT_DIR}/requirements.txt"
echo 'Installed requirements.'
