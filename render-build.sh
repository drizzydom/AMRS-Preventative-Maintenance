#!/usr/bin/env bash
set -e

# Removed sqlcipher install - not needed for Render

pip install --upgrade pip
pip install -r requirements.txt
