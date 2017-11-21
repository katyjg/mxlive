#!/bin/bash

sudo docker build --rm -t opi2051-002:5000/mxlive:mxlive-refresh . ; sudo docker push opi2051-002:5000/mxlive:mxlive-refresh
