#!/bin/sh

cd ..

#### PARAMETERS ####
VERTXT='kernel/version.txt'

git pull
rm $VERTXT
git rev-parse --short HEAD > $VERTXT