import json
import requests

basic_url = "https://synapse-wireless.hipchat.com/v2/room?"
token_snippet = "auth_token={api_token}".format(api_token="6He1vooYEwgOV1CT8Sh7kacRjWOeU901tI504msI")
rooms = requests.get(basic_url+token_snippet).json()
rooms_json = json.dumps(rooms["items"])
room_dict = {}
if rooms["items"]:
    for name in rooms["items"]:
        room_dict[name["name"].encode('unicode-escape')] = name["id"]
