#!/bin/bash

aws s3 sync s3://pmc-oa-opendata "$(realpath "$1")" --exclude "*" --include "/oa_comm/xml/all/"
