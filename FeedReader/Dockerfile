FROM python:3
WORKDIR /FeedReader

SHELL ["/bin/bash", "-c"]

# Copy local python lib installer
COPY ./Tools/PythonLibs /var/lib/python/installer

# Copy local python libs
COPY ./Libs/Python/Common /var/lib/python/common

# Copy requirements
COPY ./FeedReader/requirements.txt requirements.txt

# Install requirements
RUN python /var/lib/python/installer/build.py /var/lib/python/common /var/lib/python \
    && pip3 install -r requirements.txt --find-links /var/lib/python

# Copy source code
COPY ./FeedReader/feedreader feedreader

# Copy SSL context
COPY ./FeedReader/ssl feedreader/AppData/ssl

# Add FeedReader to python path
ENV PYTHONPATH=$PYTHONPATH:/FeedReader

EXPOSE 5000

CMD ["python", "-u", "./feedreader/app.py"]