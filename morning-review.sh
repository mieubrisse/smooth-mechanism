#!/bin/bash
SCRIPT_DIR="$(cd $(dirname ${0}) && pwd)"
python ${SCRIPT_DIR}/morning-review.py ${SCRIPT_DIR}/config.json
