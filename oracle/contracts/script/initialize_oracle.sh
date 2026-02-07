#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <PACKAGE_ID>"
    exit 1
fi

PACKAGE_ID=$1

sui client call \
  --package $PACKAGE_ID \
  --module score_oracle \
  --function initialize_registry \
  --gas-budget 10000000
