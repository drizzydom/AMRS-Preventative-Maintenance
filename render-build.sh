#!/usr/bin/env bash
set -e

apt-get update
apt-get install -y libsqlcipher-dev

pip install --upgrade pip
pip install -r requirements.txt
