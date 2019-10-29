#!/usr/bin/env bash

ln -s /tmp/ /app/static

flask run --host=0.0.0.0 --port=80