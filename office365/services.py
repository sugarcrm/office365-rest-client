# -*- coding: utf-8 -*-
import requests
from datetime import datetime

from office365.exceptions import UnknownFilterException
from office365.filters import AllMessagesFilter


class BaseService(object):

    def __init__(self, client):
        self.client = client


class OutlookService(BaseService):
    url = 'https://graph.microsoft.com/v1.0/me'

    def get_complete_url(self, path='', filter_backend=None):
        """
        Get complete API url with custom path and query string
        """
        if not filter_backend:
            raise UnknownFilterException()
        fmt = '{api_url}{api_path}?{query_string}'
        return fmt.format(api_url=self.url, api_path=path,
                          query_string=filter_backend.get_query_string())

    def list_messages(self, start_date):
        """
        Return all messages from the mailbox starting from a datetime given
        """
        messages = []
        path = '/MailFolders/AllItems/messages'
        filter_backend = AllMessagesFilter(start_date)
        next_url = self.get_complete_url(path=path, filter_backend=filter_backend)

        while next_url:
            response = self.execute_request(next_url)
            messages.extend(response['value'])
            next_url = response.get('@odata.nextLink')

        return messages

    def execute_request(self, url):
        """
        Try API request; if access_token is expired, request a new one
        """
        headers = {
            'Prefer': 'outlook.allow-unsafe-html',
            'Authorization': 'Bearer {0}'.format(self.client.access_token)
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            is_successful = self.refresh_credentials()
            if is_successful:
                headers['Authorization'] = 'Bearer {0}'.format(self.client.access_token)
                response = requests.get(url, headers=headers)
                response.raise_for_status()
            else:
                raise Exception('Error retrieving access token: %s' % response.content)
        return response.json()


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
            'resource': 'http://graph.microsoft.com/',
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
                self.client.access_token = resp_json['access_token']
                self.client.refresh_token = resp_json['refresh_token']
                self.client.expires_on = datetime.fromtimestamp(resp_json['expires_on'])
                return True
            retries -= 1
        return False
