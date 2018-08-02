#!/bin/bash

sudo docker build --rm -t srv-cmcf-dp4:5000/mxlive:latest . && sudo docker push srv-cmcf-dp4:5000/mxlive:latest
