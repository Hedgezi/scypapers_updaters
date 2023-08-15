#!/bin/bash

aws s3 sync s3://pmc-oa-opendata ./pmc-test/ --exclude "*" --include "/oa_comm/xml/all/"