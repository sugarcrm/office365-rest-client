# -*- coding: utf-8 -*-
import json
import logging
import urllib

import oauth2client.transport

from .exceptions import Office365ClientError, Office365ServerError

logger = logging.getLogger(__name__)

DEFAULT_MAX_ENTRIES=50


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
        """Simply execute the request for next_link."""
        # remove the prefix, as we only need the relative path
        full_prefix = '%s/%s/%s' % (self.base_url, self.graph_api_version, self.prefix)
        _, _, path = next_link.partition(full_prefix)
        resp = self.execute_request('get', path)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def execute_request(self, method, path, query_params=None, headers=None, body=None,
                        parse_json_result=True):
        """
        Run the http request and returns the json data upon success.

        path: the path of the api endpoint with leading slash (excluding the
        api version and user id prefix) query_params: dict to be urlencoded and
        appended to the final url headers: dict body: bytestring to be used as
        request body
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
    """Wrap a collection of services in a context."""

    def __init__(self, client, prefix):
        self.client = client
        self.prefix = prefix

        self.calendar = CalendarService(self.client, self.prefix)
        self.calendarview = CalendarViewService(self.client, self.prefix)
        self.event = EventService(self.client, self.prefix)
        self.message = MessageService(self.client, self.prefix)
        self.attachment = AttachmentService(self.client, self.prefix)
        self.contactfolder = ContactFolderService(self.client, self.prefix)
        self.contact = ContactService(self.client, self.prefix)
        self.mailfolder = MailFolderService(self.client, self.prefix)

        self.user = UserService(self.client, self.prefix)


class BaseFactory(object):
    def __init__(self, client):
        self.client = client


class SubscriptionFactory(BaseFactory):
    def __call__(self):
        return SubscriptionService(self.client, '')


class BatchService(BaseService):
    def __init__(self, client, batch_uri=None):
        self.client = client

        if not batch_uri:
            self.batch_uri = 'https://graph.microsoft.com/beta/$batch'

        self._callbacks = {}

        # A map from id to request.
        self._requests = {}

        # A map from id to callback.
        self._callbacks = {}

        # List of request ids, in the order in which they were added.
        self._order = []

        # The last auto generated id.
        self._last_auto_id = 0

        # A map from request id to (httplib2.Response, content) response pairs
        self._responses = {}

    def _new_id(self):
        """
        Create a new id.

        Auto incrementing number that avoids conflicts with ids already used.
        Returns:
           string, a new unique id.

        """
        self._last_auto_id += 1
        while str(self._last_auto_id) in self._requests:
            self._last_auto_id += 1

        return str(self._last_auto_id)

    def add(self, request, callback=None):
        request_id = self._new_id()
        self._requests[request_id] = request
        self._callbacks[request_id] = callback
        self._order.append(request_id)

    def _execute(self, requests):
        method = 'POST'
        default_headers = {'Content-Type': 'application/json'}

        logger.info('{}: {} with {}x requests'.format(method, self.batch_uri, len(requests)))
        resp, content = oauth2client.transport.request(self.client.http,
                                                       self.batch_uri,
                                                       method=method,
                                                       body=json.dumps({'requests': requests}),
                                                       headers=default_headers)
        if resp.status < 300:
            if content:
                return json.loads(content)
        elif resp.status < 500:
            try:
                error_data = json.loads(content)
            except ValueError:
                error_data = {'error': {'message': content, 'code': 'unknown'}}
            raise Office365ClientError(resp.status, error_data)
        else:
            raise Office365ServerError(resp.status, content)

    def execute(self):
        requests = []
        for request_id in self._order:
            request = self._requests[request_id]
            request['id'] = request_id
            requests.append(request)

        responses = self._execute(requests)

        # Map the responses to the request_ids
        for resp in responses['responses']:
            self._responses[resp['id']] = resp

        # Process the callbacks
        for request_id in self._order:
            response = self._responses[request_id]
            request = self._requests[request_id]
            callback = self._callbacks[request_id]
            exception = None
            try:
                if response['status'] >= 300:
                    error_data = response['body']
                    raise Office365ClientError(response['status'], error_data)
            except Office365ClientError as e:
                exception = e

            if callback is not None:
                callback(request_id, response['body'], exception)


class SubscriptionService(BaseService):

    def create(self, body=None):
        """https://developer.microsoft.com/en-us/graph/docs/api-reference/v1.0/resources/webhooks ."""
        path = 'subscriptions'
        method = 'post'
        _body = json.dumps(body)
        return self.execute_request(method, path, body=_body)

    def update(self, subscription_id, body=None):
        """Extend the duration of the subscription."""
        method = 'patch'
        path = 'subscriptions/%s' % subscription_id
        _body = json.dumps(body)
        return self.execute_request(method, path, body=_body)

    def delete(self, subscription_id):
        """Unsubscribe to a webhook channel."""
        path = 'subscriptions/%s' % subscription_id
        method = 'delete'
        return self.execute_request(method, path)


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
    def list(self, max_entries=DEFAULT_MAX_ENTRIES):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_calendars."""
        # TODO: handle pagination
        path = '/calendars'
        method = 'get'
        query_params = {
            "$top": max_entries
        }
        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, calendar_id=None):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/calendar_get ."""
        if calendar_id:
            path = '/calendars/' + calendar_id
        else:
            path = '/calendar'
        method = 'get'
        return self.execute_request(method, path)

    def create(self, **kwargs):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_post_calendars ."""
        path = '/calendars'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def delete(self, calendar_id):
        path = '/calendars/' + calendar_id
        method = 'delete'
        return self.execute_request(method, path)

    def update(self, calendar_id, **kwargs):
        path = '/calendars/' + calendar_id
        method = 'patch'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class EventService(BaseService):
    def create(self, calendar_id=None, **kwargs):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/calendar_post_events ."""
        if calendar_id:
            # create in specific calendar
            path = '/calendars/' + calendar_id + '/events'
        else:
            # create in default calendar
            path = '/calendar/events'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def list(self, calendar_id=None, _filter='', max_entries=DEFAULT_MAX_ENTRIES):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/calendar_list_events ."""
        if calendar_id:
            # create in specific calendar
            path = '/calendars/' + calendar_id + '/events'
        else:
            # create in default calendar
            path = '/calendar/events'
        method = 'get'
        query_params = {
            "$top": max_entries
        }
        if _filter:
            query_params['$filter'] =_filter

        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, event_id, params=None, path=None):
        if not path:
            path = '/calendar/events/'
        path += event_id

        method = 'get'
        return self.execute_request(method, path, query_params=params)

    def update(self, event_id, path=None, **kwargs):
        if not path:
            path = '/calendar/events/'
        path += event_id

        method = 'patch'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def delete(self, event_id, path=None):
        if not path:
            path = '/calendar/events/'
        path += event_id

        method = 'delete'
        return self.execute_request(method, path)


class CalendarViewService(BaseService):
    def list(self, start_datetime, end_datetime, max_entries=DEFAULT_MAX_ENTRIES):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_calendarview."""
        path = '/calendarView'
        method = 'get'
        query_params = {
            'startDateTime': start_datetime,
            'endDateTime': end_datetime,
            '$top': max_entries
        }
        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def delta_list(self, start_datetime=None, end_datetime=None, delta_token=None, calendar_id=None):
        """
        Support tracking of changes in the calendarview.

        https://developer.microsoft.com/en-us/graph/docs/concepts/delta_query_overview
        """
        path = ''
        if calendar_id:
            path = '/calendars/%s' % calendar_id
        path += '/calendarView/delta'

        method = 'get'
        if not delta_token:
            query_params = {
                'startDateTime': start_datetime,
                'endDateTime': end_datetime,
            }
        else:
            query_params = {
                '$deltaToken': delta_token,
            }
        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link


class MessageService(BaseService):
    def list(self, _filter=None, max_entries=DEFAULT_MAX_ENTRIES):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_messages ."""
        path = '/messages'
        method = 'get'
        query_params = {
            "$top": max_entries
        }
        if _filter:
            query_params['$filter'] =_filter

        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, message_id, _filter=None):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_list_messages ."""
        path = '/messages/{}'.format(message_id)
        method = 'get'
        return self.execute_request(method, path, query_params=_filter)

    def create(self, **kwargs):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/user_post_messages ."""
        path = '/messages'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def send(self, message_id, **kwargs):
        """https://developer.microsoft.com/en-us/graph/docs/api-reference/v1.0/api/message_send ."""
        path = '/messages/{}/send'.format(message_id)
        # this request fails if Content-Type header is set
        # to work around this, we don't use self.execute_request()
        resp, content = oauth2client.transport.request(self.client.http,
                                                       self.build_url(path),
                                                       method='POST',
                                                       headers={'Content-Length': 0})
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

    def update(self, message_id, **kwargs):
        path = '/messages/{}'.format(message_id)
        method = 'patch'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def move(self, message_id, destination_id):
        path = '/messages/{}/move'.format(message_id)
        method = 'post'
        body = json.dumps({'DestinationId': destination_id})
        return self.execute_request(method, path, body=body)



class AttachmentService(BaseService):
    def list(self, message_id, _filter=None, max_entries=DEFAULT_MAX_ENTRIES):
        path = '/messages/{}/attachments'.format(message_id)
        method = 'get'
        query_params = {
            "$top": max_entries
        }
        if _filter:
            query_params['$filter'] =_filter

        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def list_first_page(self, message_id, _filter=None):
        # backwards compatibility
        resp, _ = self.list(message_id, _filter)
        return resp

    def get(self, message_id, attachment_id):
        path = '/messages/{}/attachments/{}'.format(message_id, attachment_id)
        method = 'get'
        return self.execute_request(method, path)

    def create(self, message_id, **kwargs):
        """https://graph.microsoft.io/en-us/docs/api-reference/v1.0/api/message_post_attachments ."""
        path = '/messages/{}/attachments'.format(message_id)
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class ContactFolderService(BaseService):
    def list(self, max_entries=DEFAULT_MAX_ENTRIES):
        path = '/contactFolders'
        method = 'get'
        query_params = {
            '$top': max_entries
        }
        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, folder_id):
        path = '/contactFolders/' + folder_id
        method = 'get'
        return self.execute_request(method, path)

    def create(self, **kwargs):
        path = '/contactFolders'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class ContactService(BaseService):
    def create(self, contact_folder_id=None, **kwargs):
        if contact_folder_id:
            # create in specific folder
            path = '/contactFolders/' + contact_folder_id + '/contacts'
        else:
            # create in default calendar
            path = '/contacts'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def list(self, contact_folder_id=None, _filter='', max_entries=DEFAULT_MAX_ENTRIES):
        if contact_folder_id:
            # list in specific folder
            path = '/contactFolders/' + contact_folder_id + '/contacts'
        else:
            # create in default calendar
            path = '/contacts'
        method = 'get'
        query_params = {
            "$top": max_entries
        }
        if _filter:
            query_params['$filter'] =_filter

        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, contact_id):
        path = '/contacts/' + contact_id
        method = 'get'
        return self.execute_request(method, path)

    def delete(self, contact_id):
        path = '/contacts/' + contact_id
        method = 'delete'
        return self.execute_request(method, path)

    def update(self, contact_id, **kwargs):
        path = '/contacts/' + contact_id
        method = 'patch'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)


class MailFolderService(BaseService):
    def create(self, **kwargs):
        path = '/mailFolders'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)

    def list(self, max_entries=DEFAULT_MAX_ENTRIES):
        path = '/mailFolders'
        method = 'get'
        query_params = {'$top': max_entries}
        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def delta_list(self, folder_id, delta_token=None, _filter=None):
        """
        Support tracking of changes in the mailFolders.

        https://developer.microsoft.com/en-us/graph/docs/concepts/delta_query_overview
        """
        path = '/mailFolders/{}/messages/delta'.format(folder_id)

        method = 'get'
        query_params = {}
        if delta_token:
            query_params = {
                '$deltaToken': delta_token,
            }
        if _filter:
            query_params.update({'$filter':_filter})

        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def get(self, folder_id):
        path = '/mailFolders/' + folder_id
        method = 'get'
        return self.execute_request(method, path)

    def list_childfolders(self, folder_id, max_entries=DEFAULT_MAX_ENTRIES):
        path = '/mailFolders/' + folder_id + '/childFolders'
        method = 'get'
        query_params = {'$top': max_entries}
        resp = self.execute_request(method, path, query_params=query_params)
        next_link = resp.get('@odata.nextLink')
        return resp, next_link

    def create_childfolder(self, folder_id, **kwargs):
        path = '/mailFolders/' + folder_id + '/childFolders'
        method = 'post'
        body = json.dumps(kwargs)
        return self.execute_request(method, path, body=body)
