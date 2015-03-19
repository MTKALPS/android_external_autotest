#!/usr/bin/python
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Mail the content of standard input.

Example usage:
  Use pipe:
     $ echo "Some content" |./gmail_lib.py -s "subject" abc@bb.com xyz@gmail.com

  Manually input:
     $ ./gmail_lib.py -s "subject" abc@bb.com xyz@gmail.com
     > Line 1
     > Line 2
     Ctrl-D to end standard input.
"""
import argparse
import base64
import httplib2
import logging
import sys
import os
from email.mime.text import MIMEText

import common
from autotest_lib.client.common_lib import global_config

try:
  from apiclient.discovery import build as apiclient_build
  from apiclient import errors as apiclient_errors
  from oauth2client import file as oauth_client_fileio
except ImportError as e:
  apiclient_build = None
  logging.debug("API client for gmail disabled. %s", e)


DEFAULT_GMAIL_CREDS_PATH = global_config.global_config.get_config_value(
        'NOTIFICATIONS', 'gmail_api_credentials', default='')

class GmailApiException(Exception):
    """Exception raised in accessing Gmail API."""


class Message():
    """An email message."""

    def __init__(self, to, subject, message_text):
        """Initialize a message.

        @param to: The recievers saperated by comma.
                   e.g. 'abc@gmail.com,xyz@gmail.com'
        @param subject: String, subject of the message
        @param message_text: String, content of the message.
        """
        self.to = to
        self.subject = subject
        self.message_text = message_text


    def get_payload(self):
        """Get the payload that can be sent to the Gmail API.

        @return: A dictionary representing the message.
        """
        message = MIMEText(self.message_text)
        message['to'] = self.to
        message['subject'] = self.subject
        return {'raw': base64.urlsafe_b64encode(message.as_string())}


class GmailApiClient():
    """Client that talks to Gmail API."""

    def __init__(self, oauth_credentials):
        """Init Gmail API client

        @param oauth_credentials: Path to the oauth credential token.
        """
        if not apiclient_build:
            raise GmailApiException('Cannot get apiclient library.')

        storage = oauth_client_fileio.Storage(oauth_credentials)
        credentials = storage.get()
        if not credentials or credentials.invalid:
            raise GmailApiException('Invalid credentials for Gmail API, '
                                    'could not send email.')
        http = credentials.authorize(httplib2.Http())
        self._service = apiclient_build('gmail', 'v1', http=http)


    def send_message(self, message):
      """Send an email message.

      @param message: Message to be sent.
      """
      try:
        # 'me' represents the default authorized user.
        message = self._service.users().messages().send(
                userId='me', body=message.get_payload()).execute()
        logging.debug('Email sent: %s' , message['id'])
      except apiclient_errors.HttpError as error:
        logging.error('Failed to send email: %s', error)


def get_default_creds_abspath():
    """Returns the abspath of the gmail api credentials file.

    @return: A path to the oauth2 credentials file.
    """
    auth_creds = DEFAULT_GMAIL_CREDS_PATH
    return (auth_creds if os.path.isabs(auth_creds) else
            os.path.join(common.autotest_dir, auth_creds))


def send_email(to, subject, message_text):
    """Send email.

    @param to: The recipients, separated by comma.
    @param subject: Subject of the email.
    @param message_text: Text to send.
    """
    auth_creds = get_default_creds_abspath()
    if not os.path.isfile(auth_creds):
        logging.error('Failed to send email to %s: Credential file does not'
                      'exist: %s. If this is a prod server, puppet should'
                      'install it. If you need to be able to send email, '
                      'find the credential file from chromeos-admin repo and '
                      'copy it to %s', to, auth_creds, auth_creds)
        return
    client = GmailApiClient(oauth_credentials=auth_creds)
    m = Message(to, subject, message_text)
    client.send_message(message=m)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(
            description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-s', '--subject', type=str, dest='subject',
                        required=True, help='Subject of the mail')
    parser.add_argument('recipients', nargs='*',
                        help='Email addresses separated by space.')
    args = parser.parse_args()
    if not args.recipients or not args.subject:
        print 'Requires both recipients and subject.'
        sys.exit(1)

    message_text = sys.stdin.read()
    send_email(','.join(args.recipients), args.subject , message_text)