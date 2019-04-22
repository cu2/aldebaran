#!/usr/bin/env bash
set -eu
set -o pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd "${ROOT_DIR}"

if [ ! -d "virtualenv" ]; then
  echo 'Please install first by running ./scripts/setup.sh'
  exit 1
fi

. "virtualenv/bin/activate"

exec python -m utils.generate_docs "$@"
