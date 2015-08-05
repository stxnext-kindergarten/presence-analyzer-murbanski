# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
from lxml import etree
from json import dumps
from functools import wraps
from datetime import datetime

from flask import Response

from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()

                data.setdefault(user_id, {})[date] = {'start': start,
                                                      'end': end}
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

    return data


def get_user_data():
    """
    Extracts user data from XML file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            'avatar': '/api/images/users/user_id',
            'name': 'User Name',
        }
    }
    """
    data = {}
    with open(app.config['USERS_XML'], 'r') as xmlfile:
        users_xml = etree.parse(xmlfile)
        server_info = users_xml.getroot().find('server')
        avatar_prefix = None
        if server_info is not None:
            host = server_info.find('host')
            port = server_info.find('port')
            protocol = server_info.find('protocol')
            if None not in (host, port, protocol):
                avatar_prefix = "%s://%s:%s" % (protocol.text, host.text,
                                                port.text)

        for user in users_xml.getroot().iter('user'):
            user_id = int(user.get('id'))
            avatar = user.find('avatar')
            name = user.find('name')

            data[user_id] = {'name': name.text}
            if avatar_prefix and avatar is not None:
                data[user_id]['avatar'] = avatar_prefix + avatar.text

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def mean_start_end_by_weekday(items):
    """
    Calculate mean start-end times by weekday.
    """

    # [start, end, count] for every day in week
    week_stats = [[0, 0, 0] for _ in range(7)]
    for date, item in items.iteritems():
        day_stats = week_stats[date.weekday()]
        day_stats[0] += seconds_since_midnight(item['start'])
        day_stats[1] += seconds_since_midnight(item['end'])
        day_stats[2] += 1

    results = []
    for weekday, day_stats in enumerate(week_stats):
        count = day_stats[2]
        if count:
            start = day_stats[0]/count
            end = day_stats[1]/count
            results.append([weekday, start, end])

    return results


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
