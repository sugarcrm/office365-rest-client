# -*- coding: utf-8 -*-
import requests
from datetime import datetime

from .filters import BaseFilter
from .filters import AllMessagesFilter


class BaseService(object):

    def __init__(self, client):
        self.client = client
        self.headers = {
            'Authorization': 'Bearer {0}'.format(self.client.access_token)
        }


class BaseAPIService(BaseService):
    url = 'https://graph.microsoft.com/v1.0/me'
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
        next_url = self.get_complete_url(path=path or self.path,
                                         filter_backend=filter_backend)
        while next_url:
            response = self.execute_request(next_url, custom_headers)
            result.extend(response['value'])
            next_url = response.get('@odata.nextLink')

        return result

    def execute_request(self, url, headers):
        """
        Try API request; if access_token is expired, request a new one
        """
        headers = headers.update(self.headers) if headers else self.headers
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            is_successful = self.client.token.refresh()
            if is_successful:
                headers['Authorization'] = 'Bearer {0}'.format(self.client.access_token)
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            else:
                raise Exception('Error retrieving access token: %s' % response.content)
        return response.json()


class CalendarService(BaseAPIService):

    def get_events(self):
        """
        Return all events from the Office365 Calendar with given datetime range
        """
        filter_backend = BaseFilter()
        return self.get_list(filter_backend, path='/Events')

    def get_calendarview(self, start_date, end_date):
        """
        Return all events from the Office365 Calendar with given datetime range
        """
        custom_qs = {
            'startDateTime': start_date,
            'endDateTime': end_date
        }
        filter_backend = BaseFilter(custom_qs=custom_qs)
        return self.get_list(filter_backend, path='/CalendarView')


class OutlookService(BaseAPIService):
    path = '/MailFolders/AllItems/messages'

    def get_messages(self, start_date, end_date):
        """
        Return all messages from the mailbox starting from a datetime given
        """
        filter_backend = AllMessagesFilter(start_date, end_date)
        headers = {'Prefer': 'outlook.allow-unsafe-html'}
        return self.get_list(filter_backend, custom_headers=headers)


class TokenService(BaseService):
    refresh_url = 'https://login.microsoftonline.com/common/oauth2/token'

    def _get_refresh_data(self):
        """
        Get dynamic parameters for refreshing access token
        """
        return {
            'grant_type': 'refresh_token',
            'redirect_uri': self.client.redirect_uri,
            'client_id': self.client.client_id,
            'client_secret': self.client.client_secret,
            'resource': 'https://graph.microsoft.com/',
            'refresh_token': self.client.refresh_token
        }

    def refresh(self, retries=2):
        """
        Refresh access token with a given number of retries
        """
        while retries:
            response = requests.post(self.refresh_url, data=self._get_refresh_data())
            if response.status_code == 200:
                resp_json = response.json()
                expires_on = datetime.fromtimestamp(float(resp_json['expires_on']))
                self.client.save_credentials(access_token=resp_json['access_token'],
                                             refresh_token=resp_json['refresh_token'],
                                             expires_on=expires_on)
                return True
            retries -= 1
        return False
