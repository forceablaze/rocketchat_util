#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

import sys
import getpass
import json
import datetime
import csv

from optparse import OptionParser
from rocketchat.api import API

from asciimatics.widgets import Frame
from asciimatics.widgets import ListBox
from asciimatics.widgets import Layout
from asciimatics.widgets import Button
from asciimatics.widgets import Widget
from asciimatics.widgets import Text
from asciimatics.widgets import TextBox

from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
from time import sleep

from Models import ChannelModel
from Models import MessageModel

from csvstream.UnicodeWriter import UnicodeWriter

RC = None
config = None

class MessageView(Frame):
    def __init__(self, screen, model):
        super(MessageView, self).__init__(screen,
                screen.height * 2 // 3,
                screen.width * 2 // 3,
                on_load=self._load,
                hover_focus=True,
                can_scroll=False,
                title="Message",
                reduce_cpu=True)

        self._model = model

        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Text("Time:", "timestamp"))
        layout.add_widget(Text("From:", "author"))
        layout.add_widget(TextBox(Widget.FILL_FRAME,
            None, "text", as_string = True, line_wrap = True ))

        layout.add_widget(Button("Back", self._back))

        self.fix()

    def _load(self):
        self.data = self._model.getCurrentMessage()
        if 'text' in self.data:
            self.data['text'] = self.data['text'].replace('\n', '\n\r')

    def _back(self):
        raise NextScene("Main")

class View(Frame):
    def __init__(self, screen, channelModel, messageModel):
        super(View, self).__init__(screen,
                screen.height, screen.width,
                on_load=self._retrieve,
                title="Channel List")
        self._channelModel = channelModel
        self._messageModel = messageModel
        self._initialized = False

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
            on_select=self._on_message_select,
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

    def _on_message_select(self):
        messageId = self._messageListView.value
        self._messageModel.setCurrentMessageId(messageId)
        raise NextScene('Message')

    def _on_pick(self):
        pass

    def _retrieve(self):
        if self._initialized is False:
            self._channelModel._retrieve()
            self._initialized = True
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


def retrieveMessageAndExportToCSV():

    channels._retrieve()
    msgs = messages.getMessaegOrderbyTime()

    with open('output.csv' , 'w') as csvfile:
        writer = UnicodeWriter(csvfile)
        writer.writerow(['Time', 'Channel', 'From', 'Message'])

        for msg in msgs:
            writer.writerow([msg['timestamp'], 'Channel', msg['author'], msg['text']])

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
                message['msg'])

def doLogin():
    user = raw_input('Please input username:')
    password = getpass.getpass("Please input password:")
    data = RC.login(user, password)

config = loadJSONConfig()
RC = API(config['rocketchat'])
messages = MessageModel(RC, config)
channels = ChannelModel(messages, RC)

def frame(screen):
    scenes = [
        Scene([View(screen,
                    channelModel = channels,
                    messageModel = messages)], -1, name = 'Main'),
        Scene([MessageView(screen, model = messages)], -1, name = 'Message')
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

    parser.add_option("-e", "--export", default=False,
        action="store_true", dest = "export",
        help = "export to file")

    (options, args) = parser.parse_args()

    doLogin()
    if options.interactive is True:
        interactiveMode()
    elif options.export is True:
        retrieveMessageAndExportToCSV()
    else:
        getJoinedChannelsMentions()
