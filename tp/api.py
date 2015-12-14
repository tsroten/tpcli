# -*- coding: utf-8 -*-
"""Interfaces with the Tp API.

Classes:
    * ResponseContent: The response content of an API request.
    * TpEntity: A generic Tp API entity class.
    * User: A Tp User entity.
    * General: A Tp General entity.
    * Assignable: A Tp Assignable entity.
    * GeneralFollower: A Tp GeneralFollower entity.
    * ApiError: Exception class for Tp API errors.
    * TpApi: A class to interface with the Tp Api.

Functions:
    * fetch: Fetch an entity from the API.

"""

import json
import logging
import re

import requests
import xmltodict

try:
    basestring
except NameError:
    basestring = str


def fetch(api, entity, raw=False, **data):
    """Fetch *entity* from *api* using options *data*.

    Typical options include:
    * orderBy
    * where
    * include or exclude
    * take
    * skip

    See the 'Response Format' page on the Tp Developers Portal for more
    information: http://dev.targetprocess.com/rest/response_format.

    :param TpApi api: The API to use.
    :param TpEntity entity: The Tp entity to fetch.
    :param bool raw: Whether or not to return the raw response.
    :param dict data: The data to send with the request.

    :returns: The response.
    :rtype: list or dict depending on *raw*
    """

    try:
        if 'exclude' in data and not isinstance(data['exclude'], basestring):
            data['exclude'] = '[{0}]'.format(','.join(data['exclude']))
        if 'include' in data and not isinstance(data['include'], basestring):
            data['include'] = '[{0}]'.format(','.join(data['include']))
    except TypeError:
        raise TypeError('include/exclude must be a string or container that '
                        'supports joining on a string.')

    response = api.request_and_raise_error('get', entity.uri, data=data)

    if raw is True:
        return response
    content = api.decode_content(response)
    return [entity(item, api=api) for item in content['Items']]


class ResponseContent(dict):
    """The response content of an API request."""

    def get_nested(self, keys, default=None):
        """Get the value or return *default*.

        :param keys: An iterable of nested keys/indices to lookup. Or, a string
            for a single key.
        :param default: A default value to return.
        """

        if isinstance(keys, basestring):
            keys = (keys, )

        content = self
        try:
            for key in keys:
                content = content[key]
            return content
        except (KeyError, IndexError, TypeError):
            return default


class TpEntity(dict):
    """A generic Tp API entity class."""

    #: The relative URI for this entity.
    #: It should include a trailing slash.
    uri = None

    def __init__(self, *args, **kwargs):
        """Store the API object if specified."""
        self._logger = logging.getLogger(__name__)

        self.api = kwargs.pop('api', None)
        return super(TpEntity, self).__init__(*args, **kwargs)

    def fetch(self, api=None):
        """Fetch this entity's data using the Tp API.

        This entity must have an ID before calling this method.

        :param TpApi api: The API to use. If not present uses object's *uri*
            attribute.

        :raises ApiError: if the entity doesn't have an ID.
        """

        if self['Id'] is None:
            raise ApiError('MissingID', 'An entity ID is required.')

        api = self.api if api is None else api
        uri = '{0}{1}'.format(self.uri, self['Id'])

        r = api.request_and_raise_error('get', uri, data=self)
        content = api.decode_content(r)
        self.update(content)

    def save(self, api=None):
        """Save this entity using the Tp API.

        This can be used to create or update an entity. The reponse is used to
        update this object's information.

        :param TpApi api: The API to use. If not present uses object's *uri*
            attribute.
        """

        api = self.api if api is None else api
        r = api.request_and_raise_error('post', self.uri, data=self)
        content = api.decode_content(r)
        self.update(content)

    def delete(self, api=None):
        """Delete this entity using the Tp API.

        :param TpApi api: The API to use. If not present uses object's *uri*
            attribute.

        :raises ApiError: if the entity doesn't have an ID.
        """

        api = self.api if api is None else api
        if self['Id'] is None:
            raise ApiError('MissingID', 'An entity ID is required.')
        uri = '{0}{1}'.format(self.uri, self['Id'])
        api.request_and_raise_error('delete', uri, data=self)
        del self['Id']


class User(TpEntity):
    """A Tp User entity."""

    uri = 'Users/'


class General(TpEntity):
    """A Tp General entity."""

    uri = 'Generals/'
    url = 'https://{subdomain}.tpondemand.com/entity/{id}'

    def get_url(self):
        """Get the entity's URL."""
        if self.api is None:
            raise TypeError("Entity's API must be a TpApi object.")
        if self['Id'] is None:
            raise ApiError('MissingID', 'An entity ID is required.')

        url = self.url.format(subdomain=self.api.subdomain, id=self['Id'])
        return url

    def follow(self, user_id=None):
        """Follow this entity.

        :param user_id: The user's ID who wants to follow this entity.
        """

        user_id = user_id or self.api.get_user_id()

        follower = GeneralFollower(api=self.api)
        follower['General'] = {'Id': self['Id']}
        follower['User'] = {'Id': user_id}
        follower.save()

    def unfollow(self, user_id=None):
        """Unfollow a TargetProcess entity.

        :param user_id: The user's ID who wants to unfollow this entity.

        :raises ApiError: if there was no record of the user following this
            entity.
        """

        user_id = user_id or self.api.get_user_id()

        where = 'General.Id eq {0} and User.Id eq {1}'.format(self['Id'],
                                                              user_id)
        include = ('Id', 'General[Id]', 'User[Id]')
        data = {'where': where, 'include': include}
        general_followers = fetch(self.api, GeneralFollower, **data)

        gf = general_followers[0]
        if gf['General']['Id'] != self['Id'] or gf['User']['Id'] != user_id:
            raise ApiError('NotFound',
                           'Matching GeneralFollower entity not found.')

        gf.delete()


class Assignable(General):
    """A Tp Assignable entity."""

    uri = 'Assignables/'


class GeneralFollower(TpEntity):
    """A Tp GeneralFollower entity."""

    uri = 'GeneralFollowers/'


class ApiError(Exception):
    """Exception class for Tp API errors."""

    def __init__(self, status, message, *args):
        """Store the *status* and *message* returned by Tp."""

        self.status = status
        self.message = message
        super(Exception, self).__init__(*args)


class TpApi(object):
    """An interface to the Tp Api."""

    uri = 'https://{subdomain}.tpondemand.com/api/v1/'
    response_format = 'json'

    def __init__(self, subdomain, token=None, username=None, password=None,
                 user_id=None):
        """Construct the base URI.

        :param str subdomain: The Targetprocess subdomain to use.
        :param str token: A Targetprocess security token.
        :param str username: A Targetprocess username (login).
        :param str password: A Targetprocess password.
        :param str user_id: A Targetprocess user's id.
        """

        self._logger = logging.getLogger(__name__)

        self.subdomain = subdomain
        self.base_uri = self.uri.format(subdomain=self.subdomain)

        if not any((token, username and password)):
            raise ValueError('Authentication details required. '
                             'Provide *token* or *username* and *password*.')

        self.token = token
        self.username = username
        self.password = password
        self.user_id = user_id

    def get_context(self):
        """Get the current context object.

        :returns: The current context object.
        :rtype: TpEntity
        """

        response = self.request_and_raise_error('get', 'Context')

        content = self.decode_content(response)
        context = TpEntity(content)
        return context

    def get_token(self, force=False):
        """Get the security token for the user."""
        if force is False and self.token is not None:
            return self.token

        response = self.request_and_raise_error('get', 'Authentication')

        content = self.decode_content(response)
        return content.get('Token')

    def get_current_user(self):
        """Get the current user."""

        context = self.get_context()
        return User(context['LoggedUser'], api=self)

    def get_user_id(self, force=False):
        """Get the current user's id.

        :returns: The user's id.
        :rtype: int
        """

        if force is False and self.user_id is not None:
            return self.user_id

        user = self.get_current_user()
        return user['Id']

    def request(self, method, resource, data=None):
        """Construct and send a request.

        :param str method: HTTP method to use, e.g. 'get' or 'post'.
        :param str resource: Relative resource URI for the request.
        :param dict data: The data to send with the request.

        :returns: The response.
        :rtype: requests.Response
        """

        method = method.lower()
        format_param = 'format' if method == 'get' else 'resultFormat'
        url = self.base_uri + resource
        request_kws = {}
        request_kws['params'] = {}
        request_kws['headers'] = {}
        request_kws['json'] = data
        request_kws['params'][format_param] = self.response_format

        if self.token is not None:
            request_kws['params']['token'] = self.token
        else:
            request_kws['auth'] = (self.username, self.password)

        if method == 'post':
            request_kws['headers']['Content-Type'] = 'application/{0}'.format(
                self.response_format)

        response = requests.request(method, url, **request_kws)
        return response

    def request_and_raise_error(self, *args, **kwargs):
        """Send a request and raise an ApiError if it fails."""

        try:
            response = self.request(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            self.log_exception(e)
            raise ApiError('ConnectionError',
                           'Failed to establish a new connection.')

        if response.status_code < 200 or response.status_code >= 300:
            self.raise_exception(response)

        return response

    def decode_content(self, response):
        """Decode the JSON content for *response*."""

        try:
            return ResponseContent(response.json())
        except (json.decoder.JSONDecodeError, ValueError) as e:
            self.log_exception(e)

    def log_exception(self, exception):
        """Log an exception."""

        # Hide the user's token from the logged message.
        message = re.sub('(?<=token=)[a-zA-Z0-9\%]+(?=[& ])', '*****',
                         str(exception))

        self._logger.warning('Exception raised: {0}'.format(message))

    def raise_exception(self, response):
        """Raise an ApiError with the proper status code and message."""

        content = self.decode_content(response)
        if content is None:
            # Tp likes to return XML when there is an error.
            content = ResponseContent(xmltodict.parse(response.text))

        raise ApiError(content.get_nested(('Error', 'Status')),
                       content.get_nested(('Error', 'Message')))
