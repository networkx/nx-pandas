#!/usr/bin/env bash
set -e
NETWORKX_TEST_BACKEND=pandas \
NETWORKX_FALLBACK_TO_NX=True \
    pytest \
    --pyargs networkx \
    --config-file=$(dirname $0)/pyproject.toml \
    --cov-config=$(dirname $0)/pyproject.toml \
    --cov=nx_pandas \
    --cov-report= \
    "$@"
