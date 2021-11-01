FROM python:3
WORKDIR /FeedReader/feedreader
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY ./feedreader .
ENV PYTHONPATH=$PYTHONPATH:/FeedReader
ENTRYPOINT ["python", "xd.py"]