#!/usr/bin/bash
coverage run -m unittest discover tests &&
  echo "*** Creating HTML report" &&
  coverage html
