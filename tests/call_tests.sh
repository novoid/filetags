#!/bin/sh
cd $(dirname $0)/..
PYTHONPATH=".:" tests/unit_tests.py --verbose

#end
