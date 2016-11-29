# -*- coding: utf-8 -*-
import json
import urlparse

import oauth2client.transport

from .exceptions import Office365ClientError
from .exceptions import Office365ServerError
from .filters import BaseFilter
from .filters import AllMessagesFilter


class BaseService(object):

    def __init__(self, client):
        self.client = client


class BaseAPIService(BaseService):
    url = 'https://outlook.office.com/api/v2.0/me'
    path = None

    def get_complete_url(self, path='', filter_backend=None):
        """
        Get complete API url with custom path and query string
        """
        if not filter_backend:
            filter_backend = BaseFilter()
        fmt = '{api_url}{api_path}?{query_string}'
        return fmt.format(api_url=self.url,
                          api_path=path,
                          query_string=filter_backend.get_query_string())

    def get_list(self, filter_backend, path='', custom_headers={}):
        """
        Retrieve list
        """
        assert not self.path, 'A path must be provided'

        result = []
        delta_token = ''
        next_link = self.get_complete_url(path=path or self.path,
                                          filter_backend=filter_backend)
        while next_link:
            response = self.execute_request(next_link, headers=custom_headers)
            result.extend(response['value'])
            next_link = response.get('@odata.nextLink')
            delta_link = response.get('@odata.deltaLink', '')
            delta_link_qs = urlparse.parse_qs(urlparse.urlparse(delta_link).query)
            if not next_link and (delta_link_qs.get('$deltaToken') or delta_link_qs.get('$deltatoken')):
                delta_token_qs = delta_link_qs.get('$deltaToken') or delta_link_qs.get('$deltatoken')
                delta_token = delta_token_qs[0] if delta_token_qs else ''

        return result, delta_token

    def execute_request(self, url, method='get', body=None, headers=None):
        """
        Try API request; if access_token is expired, request a new one
        """
        resp, content = oauth2client.transport.request(self.client.http, url,
                                                       method=method.upper(),
                                                       body=body,
                                                       headers=headers)
        if resp.status == 200:
            return json.loads(content)
        else:
            try:
                error_data = json.loads(content)
            except ValueError:
                # server failed to returned valid json
                # probably a critical error on the server happened
                raise Office365ServerError(resp.status, content)
            else:
                raise Office365ClientError(resp.status, error_data)


class CalendarService(BaseAPIService):

    def get_calendarview(self, filter_backend=None, **kwargs):
        """
        Return all events from the Office365 Calendar with given datetime range
        """
        if kwargs.get('deltaToken'):
            kwargs['$deltaToken'] = kwargs.pop('deltaToken')
        filter_backend = filter_backend or BaseFilter(custom_qs=kwargs)
        headers = {'Prefer': 'odata.track-changes,odata.maxpagesize=100'}
        return self.get_list(filter_backend, path='/CalendarView', custom_headers=headers)


class OutlookService(BaseAPIService):
    path = '/MailFolders/AllItems/messages'

    def get_messages(self, start_date, end_date):
        """
        Return all messages from the mailbox starting from a datetime given
        """
        filter_backend = AllMessagesFilter(start_date, end_date)
        headers = {'Prefer': 'outlook.allow-unsafe-html'}
        return self.get_list(filter_backend, custom_headers=headers)
