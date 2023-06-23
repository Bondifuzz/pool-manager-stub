#!/bin/sh

autoflake -r ./pool_manager --remove-all-unused-imports -i
isort -q ./pool_manager
black -q ./pool_manager
