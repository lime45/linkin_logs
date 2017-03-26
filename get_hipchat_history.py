#!/usr/bin/env python

import argparse
from collections import deque
import datetime
import dateutil.parser
import json
from dateutil import tz
from tzlocal import get_localzone 
import logging
from os.path import getmtime
import re
import time
import requests

from time import gmtime, strftime

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# get local timezone    
LOCAL_TZ = get_localzone() 

previous_time = datetime.datetime.strptime("01/01/1970 00:00:00", "%m/%d/%Y %H:%M:%S")
MAX_RESULTS=1000
DESIRED_REQUEST_RATE=0.2
MAX_LEN = 4
circular_queue = deque([DESIRED_REQUEST_RATE]*MAX_LEN, maxlen=MAX_LEN)
remaining_requests = 1
def make_pretty_messages(message_date, message_from, message_text):
    return "[" + message_date + "] <" + message_from + "> " + message_text

def convert_time_to_local(time_object):
    from_zone = tz.tzutc()
    to_zone = LOCAL_TZ
    utc = time_object.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)

def convert_time_to_utc(time_object):
    to_zone = tz.tzutc()
    from_zone = LOCAL_TZ
    utc = time_object.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)

def my_requestsget(url):
    global reset_time, remaining_requests
    this_request = requests.get(url)
    logger.debug("url = {url}".format(url=url))
    logger.debug("request headers = {headers}".format(headers=this_request.headers))
    if "X-Ratelimit-Remaining" in this_request.headers:
        remaining_requests = int(this_request.headers["X-Ratelimit-Remaining"])
        logger.info("remaining_requests = {remaining_requests}".format(remaining_requests=remaining_requests))
        reset_time = float(this_request.headers['X-Ratelimit-Reset'])
        logger.info("reset_time = {reset_time}".format(reset_time=reset_time))
        if remaining_requests == 0:
            wait_time = reset_time - time.time()
            logger.debug("sleeping for {sleep_time} seconds".format(sleep_time=wait_time))
            time.sleep(wait_time)
    return this_request

def print_hipchat_log(api_url, api_token, room_number, begin_date, end_date, num_messages):
    messages_remaining = True
    begin_date = convert_time_to_utc(begin_date)
    message_date = datetime.datetime.strftime(end_date.astimezone(tz.tzutc()), "%m-%d-%y %H:%M:%S")
    while messages_remaining:
        this_page_messages = min(num_messages, 1000)
        room_url = api_url + "/room/{room_number}/history?date={message_date}&max-results={this_page_messages}&reverse=false&auth_token={api_token}".format(
                 room_number=room_number, message_date=message_date, this_page_messages=this_page_messages, api_token=api_token)
        num_messages -= this_page_messages
        this_page_of_logs = my_requestsget(room_url)
        this_page_of_logs_json = this_page_of_logs.json()
        if "items" not in this_page_of_logs_json:
            return
        for message in this_page_of_logs_json["items"]:
            # print "inner_counter_tracker = {inner_counter_tracker}".format(inner_counter_tracker=inner_counter_tracker)
            message_date = json.dumps(message["date"])
            message_date = message_date[1:-1]
            message_date = dateutil.parser.parse(message_date)
            message_date = convert_time_to_local(message_date)
            if message_date - begin_date < datetime.timedelta(seconds=1):
                return
            message_date_sortable = datetime.datetime.strftime(message_date, "%y-%m-%d %H:%M:%S")
            message_from = json.dumps(message["from"])
            if "name" in message_from:
                message_from = json.dumps(message["from"]["name"])
            message_text = json.dumps(message["message"])
            print make_pretty_messages(message_date_sortable, message_from, message_text)
        if this_page_of_logs_json["items"] == []:
            messages_remaining = False

CACHE_FILE = 'c:/Users/christopher.browning/docs/hipchat_logs/cache_file'
SECONDS_TO_DIRTY_CACHE_FILE = 86400 # a day

def cache_file_valid():
    try:
        modtime = getmtime(CACHE_FILE)
        if time.time() - modtime < SECONDS_TO_DIRTY_CACHE_FILE:
            return True
    except:
        return False

def write_room_dict_to_cache_file(room_dict):
    with open(CACHE_FILE, 'w') as cf:
        cf.write(str(room_dict))

def get_room_dict_from_cache_file():
    if cache_file_valid():
        with open(CACHE_FILE, 'r') as cf:
            room_dict = eval(cf.read())
        return room_dict
    else:
        return {}

def get_room_dict_from_url(api_url, api_token):
    token_snippet = "auth_token={api_token}".format(api_token=api_token)
    full_url = api_url + "/room?" + token_snippet
    rooms = my_requestsget(full_url).json()
    room_dict = {}
    if "items" in rooms:
        for name in rooms["items"]:
            room_dict[name["name"].encode('ascii', 'ignore')] = repr(name["id"])
    write_room_dict_to_cache_file(room_dict)
    return room_dict


def get_available_rooms_dict(api_url, api_token):
    if cache_file_valid():
        return get_room_dict_from_cache_file()
    else:
        return get_room_dict_from_url(api_url, api_token)

def find_rooms_by_name_snippet(api_url, api_token, name_snippet):
    room_dict = get_available_rooms_dict(api_url, api_token)
    this_room_dict = {}
    for room_name, room_number in room_dict.iteritems():
        if name_snippet in room_name:
            this_room_dict[room_name] = room_number
    return this_room_dict

def get_room_name_by_number(api_url, api_token, desired_room_number):
    room_dict = get_available_rooms_dict(api_url, api_token)
    logger.debug("room_dict = {room_dict}".format(room_dict=room_dict))
    room_name = ""
    for room_name, room_number in room_dict.iteritems():
        if int(desired_room_number) == int(room_number):
            room_name = room_name
            logger.debug("found room: %r", room_name)
            return room_name
    return ""
            

def main():
    parser = argparse.ArgumentParser(prog='get_hipchat_logs')
    parser.add_argument('-c', '--hipchat-token', required=True,
                        help="your hipchat token")
    parser.add_argument('-e', '--earliest-date', required=False, 
            default="01/01/1970 00:00:00", help="Earliest date from which to start retrieving logs. Formatting:\"MM/DD/YYYY hh:mm:ss\"")
    parser.add_argument('-l', '--latest-date', required=False, 
            default="Now", help="Latest date from which to end log retrieval. Formatting:\"MM/DD/YYYY hh:mm:ss\"")
    parser.add_argument('-n', '--number-messages', required=False, 
        default=1000000000, help="Number of messages to retrieve, default is 1 billion (probably all of them)")
    parser.add_argument('-r', '--room-number', required=False, 
        default=0, help="room number you wish to retrieve, this will override the snippet argument")
    parser.add_argument('-s', '--roomname-snippet', required=False, 
        help="snippet of roomname from which to get the log")
    parser.add_argument('-u', '--hipchatapi_url', required=False, 
        default="https://synapse-wireless.hipchat.com/v2", help="hipchat api url (stop at 'v2', defaults to synapse hipchat") 

    args = parser.parse_args()
    if args.latest_date is "Now":
        args.latest_date = datetime.datetime.now(LOCAL_TZ)
    else:
        try:
            args.latest_date = datetime.datetime.strptime(args.latest_date, "%m/%d/%Y %H:%M:%S")
        except:
            print "date format is not recognizable"
            exit(1)
    try:
        args.earliest_date = datetime.datetime.strptime(args.earliest_date, "%m/%d/%Y %H:%M:%S")
    except:
        print "date format is not recognizable"
        exit(1)
    # if they provided a room number
    if int(args.room_number) > 0:
        interesting_rooms_dict = { 
                get_room_name_by_number(args.hipchatapi_url, args.hipchat_token, args.room_number) :
                args.room_number }
        logger.debug("interesting_rooms_dict = {interesting_rooms_dict}".format(interesting_rooms_dict=interesting_rooms_dict)) # if they provided a name snippet
    elif args.roomname_snippet == None:
        interesting_rooms_dict = get_available_rooms_dict(args.hipchatapi_url, args.hipchat_token)
    else:
        interesting_rooms_dict = find_rooms_by_name_snippet(args.hipchatapi_url, args.hipchat_token, args.roomname_snippet)
    if interesting_rooms_dict == None:
        print "No rooms found"
        exit(1)
    for room_name, room_number in interesting_rooms_dict.iteritems():
        print "room name: " + str(room_name) + ", room number: " + str(room_number)
        print_hipchat_log(args.hipchatapi_url, args.hipchat_token, int(room_number), args.earliest_date, args.latest_date, int(args.number_messages))

if __name__ == "__main__":
    main()

