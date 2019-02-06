FROM python:3

ENV GCSFUSE_REPO gcsfuse-jessie

RUN apt-get update && apt-get install --yes --no-install-recommends \
    ca-certificates \
    curl \
  && echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" \
    | tee /etc/apt/sources.list.d/gcsfuse.list \
  && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
  && apt-get update \
  && apt-get install --yes gcsfuse \
  && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /mnt/rgligor-travelsanta

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app .

ENV PYTHONPATH "${PYTHONPATH}:/usr/src"

CMD [ "python", "run.py" ]