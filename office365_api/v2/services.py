# -*- coding: utf-8 -*-
import json
import logging
import urllib

import oauth2client.transport

from .exceptions import Office365ClientError
from .exceptions import Office365ServerError


logger = logging.getLogger(__name__)


class BaseService(object):
    base_url = 'https://graph.microsoft.com'
    graph_api_version = 'v1.0'

    def __init__(self, client, prefix):
        self.client = client
        self.prefix = prefix

    def build_url(self, path):
        if path.startswith('/'):
            path = path.lstrip('/')
        return '%s/%s/%s/%s' % (self.base_url, self.graph_api_version, self.prefix, path)

    def follow_next_link(self, next_link):
        """
        Simply execute the request for next_link.
        """
        # remove the prefix, as we only need the relative path
        full_prefix = '%s/%s/%s' % (self.base_url, self.graph_api_version, self.prefix)
        _, _, path = next_link.partition(full_prefix)
        resp = self.execute_request('get', path)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def execute_request(self, method, path, query_params=None, headers=None, body=None,
                        parse_json_result=True):
        """
        path: the path of the api endpoint with leading slash (excluding the api version and user id prefix)
        query_params: dict to be urlencoded and appended to the final url
        headers: dict
        body: bytestring to be used as request body

        Returns the parsed JSON data of the response content if the request was successful.
        """
        full_url = self.build_url(path)
        if query_params:
            querystring = urllib.urlencode(query_params)
            full_url += '?' + querystring

        default_headers = {
            'Content-Type': 'application/json'
        }
        if headers:
            default_headers.update(headers)

        logger.info('{}: {}'.format(method.upper(), full_url))
        resp, content = oauth2client.transport.request(self.client.http,
                                                       full_url,
                                                       method=method.upper(),
                                                       body=body,
                                                       headers=default_headers)
        if resp.status < 300:
            if content:
                return json.loads(content)
        elif resp.status < 500:
            try:
                error_data = json.loads(content)
            except ValueError:
                error_data = {'error': {'message': content, 'code': 'uknown'}}
            raise Office365ClientError(resp.status, error_data)
        else:
            raise Office365ServerError(resp.status, content)


class ServicesCollection(object):
    """
    Wrap a collection of services in a context.
    """
    def __init__(self, client, prefix):
        self.client = client
        self.prefix = prefix

        self.calendar = CalendarService(self.client, self.prefix)
        self.calendarview = CalendarViewService(self.client, self.prefix)
        self.event = EventService(self.client, self.prefix)
        self.message = MessageService(self.client, self.prefix)
        self.attachment = AttachmentService(self.client, self.prefix)

        self.user = UserService(self.client, self.prefix)


class BaseFactory(object):
    def __init__(self, client):
        self.client = client


class UserServicesFactory(BaseFactory):
    def __call__(self, user_id):
        self.user_id = user_id
        if user_id == 'me':
            # special case for 'me'
            return ServicesCollection(self.client, 'me')
        else:
            return ServicesCollection(self.client, 'users/' + user_id)


class UserService(BaseService):
    def get(self):
        path = ''
        method = 'get'
        resp = self.execute_request(method, path)
        return resp


class CalendarService(BaseService):
    def list(self):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_calendars """
        # TODO: handle pagination
        path = '/calendars'
        method = 'get'
        resp = self.execute_request(method, path)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, calendar_id=None):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/calendar_get """
        if calendar_id:
            path = '/calendars/' + calendar_id
        else:
            path = '/calendar'
        method = 'get'
        return self.execute_request(method, path)

    def create(self, **kwargs):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_post_calendars """
        path = '/calendars'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class EventService(BaseService):
    def create(self, calendar_id=None, **kwargs):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/calendar_post_events """
        if calendar_id:
            # create in specific calendar
            path = '/calendars/' + calendar_id + '/events'
        else:
            # create in default calendar
            path = '/calendar/events'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def list(self, calendar_id=None, _filter=''):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/calendar_list_events """
        if calendar_id:
            # create in specific calendar
            path = '/calendars/' + calendar_id + '/events'
        else:
            # create in default calendar
            path = '/calendar/events'
        method = 'get'
        query_params = None
        if _filter:
            query_params = {
                '$filter': _filter
            }
        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, event_id):
        path = '/calendar/events/' + event_id
        method = 'get'
        return self.execute_request(method, path)

    def update(self, event_id, **kwargs):
        path = '/calendar/events/' + event_id
        method = 'patch'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def delete(self, event_id):
        path = '/calendar/events/' + event_id
        method = 'delete'
        return self.execute_request(method, path)


class CalendarViewService(BaseService):
    def list(self, _filter=None):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_calendarview """
        path = '/calendarView'
        method = 'get'
        return self.execute_request(method, path, query_params=_filter)


class MessageService(BaseService):
    def list(self, _filter=None):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_messages """
        path = '/messages'
        method = 'get'
        return self.execute_request(method, path, query_params=_filter)

    def create(self, **kwargs):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_post_messages """
        path = '/messages'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class AttachmentService(BaseService):
    def list(self, message_id, _filter=None):
        path = '/messages/{}/attachments'.format(message_id)
        method = 'get'
        return self.execute_request(method, path, query_params=_filter)

    def get(self, message_id, attachment_id, _filter=None):
        path = '/messages/{}/attachments/{}'.format(message_id, attachment_id)
        method = 'get'
        return self.execute_request(method, path, query_params=_filter)

    def create(self, message_id, **kwargs):
        """ https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/message_post_attachments """
        path = '/messages/{}/attachments'.format(message_id)
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)
