#!/usr/bin/env bash

set -eEux

PR_REF="$(cat ./pr_data)"
RUN_CONTAINMENT_DIR="${RUN_CONTAINMENT_BASE}/${PR_REF}_${GITHUB_RUN_NUMBER}";
MASK="mask --maskfile ${RUN_CONTAINMENT_DIR}/testing/maskfile.md";

INSTANCE_ADDRESS="$(cat ./instance_address)"
SSH_CMD="ssh
         -i ./access_key_file
         -o StrictHostKeyChecking=no
         -o StrictHostKeyChecking=no
         -o User=fedora
         -o ConnectTimeout=60 ${INSTANCE_ADDRESS}"

${SSH_CMD} ${MASK} infra create network "${RUN_CONTAINMENT_DIR}";
${SSH_CMD} ${MASK} infra create machines "${RUN_CONTAINMENT_DIR}";
${SSH_CMD} ${MASK} infra provision machines;
${SSH_CMD} ${MASK} testing perform;
${SSH_CMD} ${MASK} infra cleanup network;
${SSH_CMD} ${MASK} infra cleanup machines;
