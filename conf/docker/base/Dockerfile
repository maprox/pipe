FROM debian:jessie
MAINTAINER Alexander Lyapko "sunsay@maprox.net"

RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip

ONBUILD RUN pip3 install -r requirements.txt --upgrade