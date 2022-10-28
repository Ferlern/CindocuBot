FROM python:3.10

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH "$PATH:/root/.local/bin"

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false
RUN poetry install

COPY . ./
ONBUILD RUN /usr/local/bin/python-build setup.py
CMD ["python3.10", "-O", "run.py"]