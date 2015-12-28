FROM maprox/python3

RUN git clone https://github.com/maprox/Pipe.git /pipe

WORKDIR /pipe

ENV PIPE_ENVIRONMENT="production" \
    PIPE_HOSTNAME="trx.maprox.net" \
    PIPE_HOSTIP="212.100.159.142" \
    PIPE_HANDLER="" \
    PIPE_PORT="20000" \
    PIPE_LOGSPATH="/pipe/logs" \
    REDIS_PORT="6379" \
    REDIS_HOST="127.0.0.1" \
    REDIS_PASSWORD="" \
    AMQP_CONNECTION="amqp://guest:guest@127.0.0.1//"

ENTRYPOINT ["main.py"]

CMD ["-l", "stdout"]