import json
import urllib.parse
import random
import asyncio
import websockets
import requests

import mimetypes

mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

from flask import Flask, send_from_directory
import threading

with open('config.json', 'r', encoding='utf8') as f:
    config = json.load(f)
    guild_id = config['guild_id'] if 'guild_id' in config else None
    channel_id = config['channel_id'] if 'channel_id' in config else None
    client_id = config['client_id']
    access_token = config['access_token'] if 'access_token' in config else None

current_users = []
talking_users = []
user_change_subscriptions = {}
talking_subscriptions = {}
debug = False


def rand_id():
    return random.randint(1000000, 9999999)


def log(message):
    if debug:
        print(message)


async def hello(websocket):
    while True:
        await asyncio.sleep(0.1)
        await websocket.send(json.dumps({'current_users': current_users, 'talking_users': talking_users}))


async def send_recv(ws, payload, key, value=None, child_key=None):
    while True:
        await ws.send(payload)
        try:
            return await asyncio.wait_for(recv(ws, key, value, child_key), timeout=2)
        except asyncio.exceptions.TimeoutError:
            log('Timed out. Retrying...')
            continue


async def recv(ws, key, value=None, child_key=None):
    while True:
        data = json.loads(await ws.recv())
        log("Received %s" % data)
        if key in data:
            if value is not None:
                if data[key] == value:
                    return
                else:
                    continue
            if child_key is not None:
                if child_key in data[key]:
                    return data[key]
                else:
                    continue
            return data[key]


async def start_client():
    global current_users
    global talking_users
    global guild_id
    global channel_id
    async with websockets.connect('ws://127.0.0.1:5988/?url=' + urllib.parse.quote_plus(
            'https://streamkit.kaiheila.cn/overlay/voice/%s/%s' % (0, 0)),
                                  origin='https://streamkit.kaiheila.cn',
                                  subprotocols=['ws_streamkit']) as ws:

        ready = await ws.recv()
        authorize_code = (await send_recv(ws,
                                         payload=json.dumps(
                                             {"id": rand_id(),
                                              "args": {"client_id": client_id, "scopes": ["rpc", "get_guild_info"],
                                                       "prompt": "none"},
                                              "cmd": "authorize"}),
                                         key='data',
                                         child_key='code'))['code']

        if not access_token or access_token.strip() == '':
            r = requests.post('https://www.kaiheila.cn/api/oauth2/token', data={
                "code": authorize_code,
                "grant_type": "authorization_code",
                "client_id": client_id
            }, verify=False)
            auth_token = r.json()['access_token']
        else:
            auth_token = access_token

        await send_recv(ws,
                        payload=json.dumps(
                            {"id": rand_id(), "args": {"client_id": client_id, "token": auth_token},
                             "cmd": "authenticate"}),
                        key='cmd',
                        value='authenticate')

        if guild_id.strip() == '':
            guild_id = None
        if channel_id.strip() == '':
            channel_id = None

        if guild_id is None or channel_id is None:
            print('没有指定服务器 ID 和频道 ID，将自动侦测用户当前所在频道。')
            print('订阅频道中……')

            guild_list = (await send_recv(ws,
                                          payload=json.dumps(
                                              {"id": rand_id(), "cmd": "get_guild_list"}
                                          ),
                                          key='data',
                                          child_key='guild_list'))['guild_list']

            for guild in guild_list:
                channel_list = (await send_recv(ws,
                                                payload=json.dumps(
                                                    {"id": rand_id(), "args": {"guild_id": guild['id']},
                                                     "cmd": "get_channel_list"}),
                                                key='data',
                                                child_key='channel_list'))['channel_list']

                for channel in channel_list:
                    channel_subscription_id = rand_id()
                    talking_subscription_id = rand_id()

                    await send_recv(ws,
                                    payload=json.dumps(
                                        {"id": talking_subscription_id, "args": {"channel_id": channel['id']},
                                         "cmd": "subscribe",
                                         "evt": "audio_channel_user_talk"}),
                                    key='cmd',
                                    value='subscribe')
                    await send_recv(ws,
                                    payload=json.dumps(
                                        {"id": channel_subscription_id,
                                         "args": {"guild_id": guild['id'], "channel_id": channel['id']},
                                         "cmd": "subscribe",
                                         "evt": "audio_channel_user_change"}),
                                    key='cmd',
                                    value='subscribe')

                    user_change_subscriptions[channel_subscription_id] = channel['id']
                    talking_subscriptions[talking_subscription_id] = channel['id']

                    log("Subscribed to %s with id %s" % (channel['name'], channel_subscription_id))

                print('已订阅服务器「%s」的 %s 个频道。' % (guild['name'], len(channel_list)))

            log("Subscribed %s channels" % (len(user_change_subscriptions)))
        else:
            print('已指定服务器 ID：%s 和频道 ID：%s' % (guild_id, channel_id))

            guild = (await send_recv(ws,
                                     payload=json.dumps(
                                         {"id": rand_id(), "args": {"guild_id": guild_id},
                                          "cmd": "get_guild"}
                                     ),
                                     key='data',
                                     child_key='guild'))['guild']

            channel = (await send_recv(ws,
                                       payload=json.dumps(
                                           {"id": rand_id(), "args": {"channel_id": channel_id, "guild_id": guild_id},
                                            "cmd": "get_channel"}),
                                       key='data'))


            await send_recv(ws,
                            payload=json.dumps(
                                {"id": rand_id(), "args": {"channel_id": channel['id']},
                                 "cmd": "subscribe",
                                 "evt": "audio_channel_user_talk"}),
                            key='cmd',
                            value='subscribe')

            await send_recv(ws,
                            payload=json.dumps(
                                {"id": rand_id(),
                                 "args": {"guild_id": guild['id'], "channel_id": channel['id']},
                                 "cmd": "subscribe",
                                 "evt": "audio_channel_user_change"}),
                            key='cmd',
                            value='subscribe')

            print('已订阅服务器「%s」的「%s」频道。' % (guild['name'], channel['name']))

        print("""
        ================================================

            启动成功 (*^▽^*)
            用浏览器或者 OBS 浏览器源打开 http://localhost:5000 即可。

        ================================================     
        """)

        while True:
            message = await ws.recv()
            data = json.loads(message)
            log(data)

            if 'evt' in data:
                if data['evt'] == 'audio_channel_user_change':
                    current_users = data['data']

                    if len(current_users) > 0:
                        print("侦测到频道使用者变化。")
                        print("当前用户列表：")
                        for user in current_users:
                            print('- ' + user['nickname'])
                    else:
                        print("侦测到用户离开频道。")

                elif data['evt'] == 'audio_channel_user_talk':
                    talking_users = data['data']

                    for user in current_users:
                        user['talking'] = user['id'] in talking_users


# Flask server
app = Flask(__name__, static_url_path='/')


@app.route('/')
def serve_root():
    return send_from_directory('static', 'index.html')


if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)).start()

    loop = asyncio.get_event_loop()
    server = websockets.serve(hello, "localhost", 8899)
    loop.run_until_complete(server)
    loop.run_until_complete(start_client())
    loop.run_forever()
