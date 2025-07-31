#!/bin/bash
source env/bin/activate
set -a
source .env
set +a
python3 -m cli.main
