# linkin_logs
Get Hipchat logs with throttler to maximize allotted requests

```
usage: get_hipchat_logs [-h] -c HIPCHAT_TOKEN [-e EARLIEST_DATE]
                        [-l LATEST_DATE] [-n NUMBER_MESSAGES] [-r ROOM_NUMBER]
                        [-s ROOMNAME_SNIPPET] [-u HIPCHATAPI_URL]

optional arguments:
  -h, --help            show this help message and exit
  -c HIPCHAT_TOKEN, --hipchat-token HIPCHAT_TOKEN
                        your hipchat token
  -e EARLIEST_DATE, --earliest-date EARLIEST_DATE
                        Earliest date from which to start retrieving logs.
                        Formatting:"MM/DD/YYYY hh:mm:ss"
  -l LATEST_DATE, --latest-date LATEST_DATE
                        Latest date from which to end log retrieval.
                        Formatting:"MM/DD/YYYY hh:mm:ss"
  -n NUMBER_MESSAGES, --number-messages NUMBER_MESSAGES
                        Number of messages to retrieve, default is 1 billion
                        (probably all of them)
  -r ROOM_NUMBER, --room-number ROOM_NUMBER
                        room number you wish to retrieve, this will override
                        the snippet argument
  -s ROOMNAME_SNIPPET, --roomname-snippet ROOMNAME_SNIPPET
                        snippet of roomname from which to get the log
  -u HIPCHATAPI_URL, --hipchatapi_url HIPCHATAPI_URL
                        hipchat api url (stop at 'v2', defaults to synapse
                        hipchat
```
