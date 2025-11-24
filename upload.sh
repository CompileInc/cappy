#!/usr/bin/env bash
set -euo pipefail

rm -rf dist
uvx hatch build
uvx hatch publish
