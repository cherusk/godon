#!/bin/bash

set -eE

mask --maskfile "$(pwd)/testing/maskfile.md" util kcli inventory
