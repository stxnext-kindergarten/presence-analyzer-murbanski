# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect, abort
from flask import render_template
from flask import url_for

from presence_analyzer.main import app
from presence_analyzer.utils import jsonify, get_data, get_user_data
from presence_analyzer.utils import mean, group_by_weekday, \
    mean_start_end_by_weekday

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for('presence_weekday_renderer'))


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    users = get_user_data()
    return [
        {'user_id': i,
         'name': users[i]['name'] if i in users else 'User {0}'.format(str(i)),
         'avatar': users[i]['avatar'] if i in users else ''}
        for i in data.keys()
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    week_stats = mean_start_end_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], start, end)
        for weekday, start, end in week_stats
    ]

    return result


@app.route('/presence_weekday', methods=['GET'])
def presence_weekday_renderer():
    """
    Renders and returns template for presence time of users.
    """
    return render_template('presence_weekday.html')


@app.route('/presence_start_end', methods=['GET'])
def presence_start_end_renderer():
    """
    Renders and returns template for mean start-end time of users
    """
    return render_template('presence_start_end.html')


@app.route('/mean_time_weekday', methods=['GET'])
def mean_time_weekday_renderer():
    """
    Renders and returns template for mean presence times of users
    """
    return render_template('mean_time_weekday.html')
