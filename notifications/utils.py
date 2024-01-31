from blessn.settings import FCM_SERVER_KEY

import requests
from requests.structures import CaseInsensitiveDict

url = "https://fcm.googleapis.com/fcm/send"

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"
headers["Authorization"] = "key={}".format(FCM_SERVER_KEY)
headers["Content-Type"] = "application/json"


def send_notification(user, title, content, notification_id):
    if user.registration_id and user.push_notification:
        payload = {
                'to': user.registration_id,
                'notification': {
                    "title": title,
                    "body": content
                },
                'data': {
                    "user_id": str(user.id),
                    "notification_id": str(notification_id)
                }
            }
        resp = requests.post(url, headers=headers, json=payload)
