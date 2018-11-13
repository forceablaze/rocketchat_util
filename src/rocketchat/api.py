#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

import requests
import json
import urllib

API_ENTRY = '/api'
VERSION = 'v1'

INFO = 'info'
LOGIN = 'login'
USERS_INFO = 'users.info'

CHANNELS_HISTORY = 'channels.history'
CHANNELS_MESSAGES = 'channels.messages'
CHANNELS_LIST = 'channels.list'
CHANNELS_LIST_JOINED = 'channels.list.joined'

API_DATA = {
  INFO: { 'method': 'GET' },
  LOGIN: { 'method': 'POST' },
  USERS_INFO: { 'method': 'GET' },
  CHANNELS_HISTORY: { 'method': 'GET' },
  CHANNELS_MESSAGES: { 'method': 'GET' },
  CHANNELS_LIST: { 'method': 'GET' },
  CHANNELS_LIST_JOINED: { 'method': 'GET' }
}

class RequestBuilder:
    def __init__(self, api, apiName, version = 'v1'):
        self.version = version
        self.api = api
        self.apiName = apiName

    def buildURL(self):
        return '{}/{}/{}'.format(
            self.api.API_URL,
            self.version,
            self.apiName)

    def build(self, data = None, params = None):
        url = self.buildURL()

        headers = {}

        if API_DATA[self.apiName]['method'] == 'POST':
            headers['Content-type'] = 'application/json'

        if self.api._authToken != None:
            headers['X-Auth-Token'] = self.api._authToken

        if self.api._userId != None:
            headers['X-User-Id'] = self.api._userId

        req = requests.Request(
            API_DATA[self.apiName]['method'],
            url,
            data=data,
            params= params,
            headers=headers)
        return req

class API:
    def __init__(self, url):
        self.API_URL = url + API_ENTRY
        self._session = requests.Session()
        self._authToken = None
        self._userId = None

    def handleResponse(self, response):
        if response.status_code != 200:
            raise Exception(
                    'Request Failed. code:{}'.format(response.status_code),
                    response.text.encode('utf8'))

        return {
            'status_code': response.status_code,
            'text': response.text.encode('utf8')
        }

    # send request
    def request(self, request):
        self._session.prepare_request(request)
        prepped = self._session.prepare_request(request)

        return self.handleResponse(
                self._session.send(prepped))

    # build API reuqest and send request
    def info(self):
        request = RequestBuilder(
                api = self,
                apiName = INFO).build()

        data = self.request(request)
        obj = json.loads(data['text'])
        return obj

    def login(self, user, password):
        data = { 'username': user, 'password': password }

        obj = json.dumps(data);
        request = RequestBuilder(
                api = self,
                apiName = LOGIN).build(data = obj)

        data = self.request(request)
        obj = json.loads(data['text'])
        self._authToken = obj['data']['authToken']
        self._userId = obj['data']['userId']

        return obj

    def users_info(self, userId = None):
        if userId == None:
            userId = self._userId

        request = RequestBuilder(
                api = self,
                apiName = USERS_INFO).build(params = { 'userId': userId })

        data = self.request(request)
        obj = json.loads(data['text'])
        return obj

    def channels_history(self, roomId, latest, oldest, count):
        request = RequestBuilder(
                api = self,
                apiName = CHANNELS_HISTORY).build(
                    params = {
                        'roomId': roomId,
                        'latest': latest,
                        'oldest': oldest,
                        'count': count
                    })

        data = self.request(request)
        obj = json.loads(data['text'])
        return obj


    def channels_messages(self, roomId):
        request = RequestBuilder(
                api = self,
                apiName = CHANNELS_MESSAGES).build(params = { 'roomId': roomId })

        data = self.request(request)
        obj = json.loads(data['text'])
        return obj

    def channels_list(self):
        request = RequestBuilder(
                api = self,
                apiName = CHANNELS_LIST).build()

        data = self.request(request)
        obj = json.loads(data['text'])
        return obj

    def channels_list_joined(self):
        request = RequestBuilder(
                api = self,
                apiName = CHANNELS_LIST_JOINED).build()

        data = self.request(request)
        obj = json.loads(data['text'])
        return obj
