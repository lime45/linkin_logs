#!/usr/bin/env python

import argparse
from datetime import datetime
import dateutil.parser
from dateutil import tz
import pytz 
import json
import logging
import re
import time
import codecs, sys
import requests

from time import gmtime, strftime
requests_sent = 0

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
MAX_REQUESTS_PER_5_MINUTES = 500
logger = logging.getLogger(__name__)
MAX_RESULTS=1000

def make_pretty_messages(message_date, message_from, message_text):
    return "[" + message_date + "] <" + message_from + "> " + message_text

def convert_time_to_local(time_object):
    CT = pytz.timezone('America/Chicago')
    from_zone = tz.tzutc()
    # to_zone = tz.tzlocal() # isn't working on my machine for some reason
    to_zone = CT
    utc = time_object.replace(tzinfo=from_zone)
    return utc.astimezone(to_zone)

def my_requestsget(url):
    global requests_sent, time_variable
    current_time = strfime("%Y-%m-%d %H:%M:%S", gmtime())
    current_time = gg
    return requests.get(url)


# max num_messages = 1000
def print_hipchat_log(api_token, room_number, num_messages, 
        api_url="https://synapse-wireless.hipchat.com/v2"):
    this_page_messages = min(num_messages, 1000)
    room_url = api_url + "/room/{room_number}/history?max-results={this_page_messages}&reverse=false&auth_token={api_token}".format(
             room_number=room_number, this_page_messages=this_page_messages, api_token=api_token)
    this_page_of_logs = my_requestsget(room_url)
    message_date = None
    while "items" in this_page_of_logs.json():
        for message in this_page_of_logs.json()["items"]:
            message_date = json.dumps(message["date"])
            message_date = message_date[1:-1]
            message_date = dateutil.parser.parse(message_date)
            message_date = convert_time_to_local(message_date)
            message_date = datetime.strftime(message_date, "%m-%d-%y %H:%M:%S")
            message_from = json.dumps(message["from"])
            if "name" in message_from:
                message_from = json.dumps(message["from"]["name"])
            message_text = json.dumps(message["message"])
            print make_pretty_messages(message_date, message_from, message_text)
        # use latest date to get more results
        num_messages -= this_page_messages
        if num_messages <= 0:
            return
        this_page_messages = min(num_messages, 1000)
        if message_date != None:
            room_url = api_url + "/room/{room_number}/history?date={message_date}&max-results={this_page_messages}&reverse=false&auth_token={api_token}".format(
                     room_number=room_number, message_date=message_date, this_page_messages=this_page_messages, api_token=api_token)
        this_page_of_logs = my_requestsget(room_url)


def get_available_rooms_dict(api_url, api_token):
    token_snippet = "auth_token={api_token}".format(api_token="6He1vooYEwgOV1CT8Sh7kacRjWOeU901tI504msI")
    full_url = api_url + "/room?" + token_snippet
    rooms = my_requestsget(full_url).json()
    if "items" in json.dumps(rooms):
        rooms_json = json.dumps(rooms["items"])
    else:
        return None
    room_dict = {}
    if rooms["items"]:
        for name in rooms["items"]:
            room_dict[name["id"]] = name["name"].encode('unicode-escape')
    return room_dict 
def find_rooms(api_url, api_token, name_snippet):
    room_dict = get_available_rooms_dict(api_url, api_token)
    if room_dict == None:
        return None
    this_room_dict = {}
    for room_number, room_name in room_dict.iteritems():
        if name_snippet in room_name:
            this_room_dict[room_name] = room_number
    return this_room_dict

def get_room_name_by_number(api_url, api_token, desired_room_number):
    room_dict = get_available_rooms_dict(api_url, api_token)
    if room_dict == None:
        return None
    this_room_dict = {}
    for room_number, room_name in room_dict.iteritems():
        if int(desired_room_number) == int(room_number):
            return room_name
            

def main():
    parser = argparse.ArgumentParser(prog='merge_nag_bot')
    parser.add_argument('-c', '--hipchat-token', required=True,
                        help="your hipchat token")
    parser.add_argument('-n', '--number-messages', required=False, 
        default=1000000000, help="Number of messages to retrieve, default is 1 billion (probably all of them)")
    parser.add_argument('-r', '--room-number', required=False, 
        default=0, help="room number you wish to retrieve, this will override the snippet argument")
    parser.add_argument('-s', '--roomname-snippet', required=False, 
        help="snippet of roomname from which to get the log")
    parser.add_argument('-u', '--hipchatapi_url', required=False, 
        default="https://synapse-wireless.hipchat.com/v2", help="hipchat api url (stop at 'v2', defaults to synapse hipchat") 

    args = parser.parse_args()
    if int(args.room_number) > 0:
        interesting_rooms_dict = { 
                args.room_number :
                get_room_name_by_number(args.hipchatapi_url, args.hipchat_token, args.room_number) }
    elif args.roomname_snippet == None:
        interesting_rooms_dict = get_available_rooms_dict(args.hipchatapi_url, args.hipchat_token)
    else:
        interesting_rooms_dict = find_rooms(args.hipchatapi_url, args.hipchat_token, args.roomname_snippet)
    if interesting_rooms_dict == None:
        print "No rooms found"
        exit(1)
    for room_number, room_name in interesting_rooms_dict.iteritems():
        print "room name: " + str(room_name) + ", room number: " + str(room_number)
        print_hipchat_log(args.hipchat_token, int(room_number), int(args.number_messages))

if __name__ == "__main__":
    main()
