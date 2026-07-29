#!/bin/sh
set -e

cd /opt/tempo
git fetch origin
git checkout main
git merge --ff-only origin/main
docker compose build web
docker compose up -d web
