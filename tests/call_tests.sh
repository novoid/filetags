#!/bin/sh
cd $(dirname $0)/..
PYTHONPATH=".:" tests/test_unit_tests.py --verbose

#end
