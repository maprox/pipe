FROM maprox/base

RUN git clone https://github.com/maprox/Pipe.git /pipe

WORKDIR /pipe

RUN pip3 install -r requirements.txt --upgrade

ENTRYPOINT ["python3", "main.py"]

CMD ["-l", "stdout"]