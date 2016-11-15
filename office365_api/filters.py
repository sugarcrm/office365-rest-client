# -*- coding: utf-8 -*-
class BaseFilter(object):

    def __init__(self, order_by=[], filter_by=[], select=[]):
        self.order_by = order_by
        self.filter_by = filter_by
        self.select = select

    def get_query_string(self):
        qs_list = [
            '$orderby={}'.format(','.join(self.order_by)) if self.order_by else '',
            '$filter={}'.format(' AND '.join(self.filter_by)) if self.filter_by else '',
            '$select={}'.format(','.join(self.select) if self.select else '')
        ]
        return '&'.join(qs_list)


class AllMessagesFilter(BaseFilter):

    def __init__(self, start_date):
        self.start_date = start_date
        super(AllMessagesFilter, self).__init__(
            order_by=['createdDateTime asc'],
            filter_by=[
                'isDraft eq false',
                'createdDateTime ge {}'.format(self.start_date.strftime('%Y-%m-%d'))
            ],
            select=[
                'subject', 'from', 'toRecipients', 'ccRecipients',
                'body', 'sentDateTime', 'receivedDateTime', 'createdDateTime'
            ]
        )
