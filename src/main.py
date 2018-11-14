#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

import getpass
import json
import datetime
from rocketchat.api import API

RC = None
config = None

def loadJSONConfig(path = './config.json'):
    global config;

    f = open(path, 'r')
    try:
        config = json.load(f)
    except ValueError:
        print 'JSON file format error'

    f.close()
    return config

def retrieveMentionsMessages(channelId, userId = None):
    messages = []

    now = datetime.datetime.now()
    oldtime = now + datetime.timedelta(days=int(config['period']))
    nowStr = '{}Z'.format(now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])
    oldTimeStr = '{}Z'.format(oldtime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])

    data = RC.channels_history(channelId, nowStr, oldTimeStr, 100)

    for message in data['messages']:
        if 'mentions' in message:
            for mention in message['mentions']:

                if userId is None:
                    messages.append(message)
                elif mention['_id'] == userId:
                    messages.append(message)
    return messages


def getJoinedChannelsMentions():
    data = RC.channels_list_joined()
    user_info = RC.users_info()

    userId = user_info['user']['_id']

    mentions = {}

    for channel in data['channels']:
        print 'channelName:{:30}roomId:{}'.format(
            channel['name'], channel['_id'])

        messages = retrieveMentionsMessages(channel['_id'], userId)
        mentions[channel['name']] = messages

    print ''
    for channel in mentions:
        print channel
        for message in mentions[channel]:
            print u'\tmessage from {}\t{}\n\t{}\n'.format(
                message['u']['name'], message['ts'],
                message['msg']).encode(config['encode'])

def doLogin():
    user = raw_input('Please input username:')
    password = getpass.getpass("Please input password：")
    data = RC.login(user, password)

if __name__ == '__main__':
    config = loadJSONConfig()
    RC = API(config['rocketchat'])
    print 'Rocket.Chat:', RC.info()['info']['version']
    doLogin()
    getJoinedChannelsMentions()
