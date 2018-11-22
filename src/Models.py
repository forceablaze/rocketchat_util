#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

import datetime

# calc epoch time
import calendar

import sqlite3

class MessageModel(object):
    def __init__(self, RC, config):
        self._config = config
        self._RC = RC
        self._db = sqlite3.connect(':memory:')
        self._db.row_factory = sqlite3.Row

        self._currentMessageId = None

        # Create the basic contact table.
        self._db.cursor().execute('''
            CREATE TABLE messages(
                id INTEGER PRIMARY KEY,
                messageId TEXT unique,
                roomId TEXT,
                timestamp TEXT,
                epoch INT,
                author TEXT,
                text TEXT)
        ''')
        self._db.commit()

    def setCurrentMessageId(self, id):
        self._currentMessageId = id

    def getCurrentMessage(self):
        return self._db.cursor().execute(
            "SELECT timestamp, author, text, messageId from messages WHERE messageId=:id",
                {"id": self._currentMessageId}).fetchone()

    def parseTimestamp(self, timeStr):
        return datetime.datetime.strptime(
                                timeStr[:19], "%Y-%m-%dT%H:%M:%S")

    def add(self, message):
        try:
            self._db.cursor().execute('''
                INSERT INTO messages(messageId, roomId, timestamp, epoch, text, author)
                VALUES(:_id, :rid, :ts, :epoch, :msg, :author)''',
                { '_id': message['_id'],
                  'rid': message['rid'],
                  'ts': message['ts'],
                  # convert to epoch time
                  'epoch': calendar.timegm(self.parseTimestamp(message['ts']).timetuple()),
                  'msg': message['msg'],
                  'author': message['u']['name']})
            self._db.commit()
        except sqlite3.IntegrityError:
            pass

    def getMessaegOrderbyTime(self):
        return self._db.cursor().execute(
            "SELECT timestamp, author, text, messageId, roomId from messages ORDER BY epoch ASC").fetchall()

    def get_summary(self, channelId = None):
        if channelId is None:
            return [ ('None', 1)]

        items = self._db.cursor().execute(
            "SELECT timestamp, author, text, messageId from messages WHERE roomId=:id", {"id": channelId}).fetchall()

        if items != []:
            return list(map(lambda x:
                                    (u"{} from {}:{}".format(
                                        self.parseTimestamp(x[0]).
                                            strftime("%Y-%m-%d %H:%M:%S"),
                                        # from {}
                                        x[1],
                                        # summary text
                                        x[2].strip().replace('\n', ' ')[:50]),
                                    # message Id
                                    x[3]), items))
        return [("None", 0)]

    def _retrieve(self, channelId, userId = None, mention = False):
        messages = []

        now = datetime.datetime.now()
        oldtime = now + datetime.timedelta(days=int(self._config['period']))
        nowStr = '{}Z'.format(now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])
        oldTimeStr = '{}Z'.format(oldtime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3])

        data = self._RC.channels_history(channelId, nowStr, oldTimeStr, 100)

        if mention is False:
            return data['messages']

        for message in data['messages']:
            if 'mentions' in message:
                for mention in message['mentions']:

                    if userId is None:
                        self.add(message)
                    elif mention['_id'] == userId:
                        self.add(message)

class ChannelModel(object):
    def __init__(self, messageModel, RC):
        self._RC = RC
        self._messages = messageModel
        self._db = sqlite3.connect(':memory:')
        self._db.row_factory = sqlite3.Row

        # Create the basic contact table.
        self._db.cursor().execute('''
            CREATE TABLE channels(
                id INTEGER PRIMARY KEY,
                roomId TEXT,
                name TEXT,
                unique(roomId, name))
        ''')
        self._db.commit()

        # Current contact when editing.
        self.current_id = None

    def getChannel(self, channelId):
        return self._db.cursor().execute(
            "SELECT name, roomId from channels WHERE roomId=:id",
                {"id": channelId}).fetchone()

    def get_summary(self):
        return self._db.cursor().execute(
            "SELECT name, roomId from channels").fetchall()

    def add(self, channel):
        try:
            self._db.cursor().execute('''
                INSERT INTO channels(roomId, name)
                VALUES(:_id, :name)''',
                channel)
            self._db.commit()
        except sqlite3.IntegrityError:
            pass

    def _retrieve(self):
        data = self._RC.channels_list_joined()
        user_info = self._RC.users_info()

        userId = user_info['user']['_id']

        for channel in data['channels']:
            self.add(channel)
            self._messages._retrieve(channel['_id'], userId, mention = True)
