#!/bin/bash
VERSION=unknown
eval $(fgrep VERSION config.py)
echo "${VERSION}"
