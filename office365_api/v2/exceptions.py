# -* -coding: utf-8 -*-
import json


class Office365ClientError(Exception):

    def __init__(self, status_code, data):
        super(Office365ClientError, self).__init__('{}: {}: {}'.format(
            status_code, data['error']['code'], data['error']['message']))
        self.status_code = status_code
        self.error_code = data['error']['code']
        self.error_message = data['error']['message']

    @property
    def is_not_found(self):
        return self.status_code == 404

    @property
    def is_invalid_session(self):
        # Need to use refresh_token
        return self.status_code == 401

    @property
    def is_invalid_tokens(self):
        # The refresh_token has expired. Ask to re-login
        return self.status_code == 400

    @property
    def is_expired_sync_token(self):
        return (self.error_code or '').lower() == 'syncstatenotfound'

    def __repr__(self):
        return '<{0}>: {1} {2} ({3})'.format(
            'Office365ClientError', self.status_code, self.error_code, self.error_message)


class Office365ServerError(Exception):
    
    def __init__(self, status_code, body):
        super(Office365ServerError, self).__init__(
            '{}: {}'.format(status_code, body))
        self.status_code = status_code
        try:
            data = json.loads(body)
            self.error_code = data['error']['code']
        except:
            self.error_code = ''

        self.error_message = body

    @property
    def is_response_timeout(self):
        # request takes too long to complete
        return self.status_code in [503, 504] and self.error_code == 'UnknownError'
