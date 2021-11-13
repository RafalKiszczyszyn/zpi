## Installation
#### Docker Image
To create a docker image, run the command:
```
docker build -t feedreader .
```
Then, start the new container with the command:
```
docker run -d --hostname feedreader --name FeedReader --network host feedreader:latest
```

## Settings
#### General Settings
required keys:
```
heartbeat (int) - time in seconds between successive feed updates. 
                  If set to nonpositive number, feed wiil be fetched once.
```

#### GUID Generator
All guid generator related keys must be placed under the `guid_generator` key.

Optional keys:
```
prefix  (str) - prefix of the id.
postfix (str) - postfix of the id.
```

#### Database
All database related keys must be placed under the `database` key.

Required keys:
```
connection string (str) - the connection string.
database          (str) - name of the database. 
collection        (str) - name of the collection.
ttl               (str) - seconds after published article is removed from the collection.
```

#### Event Queue
All event queue related keys must be placed under the `event_queue` key.

Required keys:
```
url (str) - the url of the event queue.
```
Optional keys:
```               
ssl.cafile      (str)   - path to the CA's file.
ssl.certfile    (str)   - path to the feedreader's certificate file.
ssl.keyfile     (str)   - path to the feedreader's private key.
```

#### Email Notifications
Email notifications are optional and disabled by default. 
To enable this feature add required keys in the setting file under the `email_notifications` key.

Required keys:
```
host                    (str)       - the domain name or ip address of the SMTP server.
port                    (int)       - the port on which the SMTP server is listening.
credentials.username    (str)       - username. 
credentials.password    (str)       - password.
recipients              (list[str]) - the list of recipients' email addresses.
``` 
Optional keys:
```
template (str) - path to the template's file. Template is used to format email messages.
```