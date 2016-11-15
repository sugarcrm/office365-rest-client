# -*- coding: utf-8 -*-
class BaseFilter(object):

    def __init__(self, order_by=[], filter_by=[], select=[], custom_qs=''):
        self.order_by = order_by
        self.filter_by = filter_by
        self.select = select
        self.custom_qs = custom_qs

    def get_query_string(self):
        qs_list = [
            '$orderby={}'.format(','.join(self.order_by)) if self.order_by else '',
            '$filter={}'.format(' AND '.join(self.filter_by)) if self.filter_by else '',
            '$select={}'.format(','.join(self.select)) if self.select else ''
        ]
        qs_list.extend([(k + '=' + str(self.custom_qs[k])) for k in self.custom_qs])
        return '&'.join([qs for qs in qs_list if qs])


class AllMessagesFilter(BaseFilter):

    def __init__(self, start_date, end_date):
        self.order_by = ['createdDateTime asc']
        self.filter_by = [
            'isDraft eq false',
            'createdDateTime ge {}'.format(start_date.strftime('%Y-%m-%d')),
            'createdDateTime le {}'.format(end_date.strftime('%Y-%m-%d'))
        ]
        self.select = [
            'subject', 'from', 'toRecipients', 'ccRecipients',
            'body', 'sentDateTime', 'receivedDateTime', 'createdDateTime'
        ]
