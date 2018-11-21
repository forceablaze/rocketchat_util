#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

import sys
import getpass
import json
import datetime

from optparse import OptionParser
from rocketchat.api import API

from asciimatics.widgets import Frame
from asciimatics.widgets import ListBox
from asciimatics.widgets import Layout
from asciimatics.widgets import Button
from asciimatics.widgets import Widget

from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from time import sleep

from Models import ChannelModel
from Models import MessageModel

RC = None
config = None

class View(Frame):
    def __init__(self, screen, channelModel, messageModel):
        super(View, self).__init__(screen,
                screen.height, screen.width,
                on_load=self._retrieve,
                title="Channel List")
        self._channelModel = channelModel
        self._messageModel = messageModel

        self._list_view = ListBox(
            Widget.FILL_FRAME,
            channelModel.get_summary(),
            name="channels",
            add_scroll_bar=True,
            on_change=self._on_channel_pick)

        self._messageListView = ListBox(
            Widget.FILL_FRAME,
            messageModel.get_summary(),
            name="messages",
            add_scroll_bar=True,
            on_change=self._on_pick)

        layout = Layout([1, 8, 1])
        self.add_layout(layout)
        layout.add_widget(self._list_view, 0)
        layout.add_widget(self._messageListView, 1)
        layout.add_widget(Button("Refresh", self._retrieve), 2)
        layout.add_widget(Button("Export to CSV", self._quit), 2)
        layout.add_widget(Button("Quit", self._quit), 2)
        self.fix()

    def _on_channel_pick(self):
        channelId = self._list_view.value
        self._messageListView.options = self._messageModel.get_summary(channelId)

    def _on_pick(self):
        pass

    def _retrieve(self):
        self._channelModel._retrieve()
        self._list_view.options = self._channelModel.get_summary()

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")

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

config = loadJSONConfig()
RC = API(config['rocketchat'])
messages = MessageModel(RC, config)
channels = ChannelModel(messages, RC)

def frame(screen):
    scenes = [
        Scene([View(screen,
                    channelModel = channels,
                    messageModel = messages)], -1, name = 'Main')
    ]
    screen.play(scenes)

def interactiveMode():
    while True:
        try:
            Screen.wrapper(frame)
            sys.exit(0)
        except ResizeScreenError:
            pass

if __name__ == "__main__":
    parser = OptionParser()

    # options settings
    parser.add_option("-I", "--interactive", default=False,
        action="store_true", dest = "interactive",
        help = "enable interactive mode")

    (options, args) = parser.parse_args()

    doLogin()
    if options.interactive is True:
        interactiveMode()
    else:
        getJoinedChannelsMentions()
