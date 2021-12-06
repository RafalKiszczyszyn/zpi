FROM python:3
WORKDIR /WordNet

SHELL ["/bin/bash", "-c"]

# Copy local python lib installer
COPY ./Tools/PythonLibs /var/lib/python/installer

# Copy local python libs
COPY ./Libs/Python/Common /var/lib/python/common

# Copy requirements
COPY ./WordNet/requirements.txt requirements.txt

# Install requirements
RUN python /var/lib/python/installer/build.py /var/lib/python/common /var/lib/python \
    && pip3 install -r requirements.txt --find-links /var/lib/python

# Copy source code
COPY ./WordNet/wordnet wordnet

# Copy SSL context
COPY ./WordNet/ssl wordnet/AppData/ssl

# Add WordNet to python path
ENV PYTHONPATH=$PYTHONPATH:/WordNet

CMD ["python", "-u", "./wordnet/app.py"]
