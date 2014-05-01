# Copyright 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Module contains a simple client lib to the devices RPC."""

import json
import logging
import urllib2

import common
from fake_device_server.client_lib import common_client
from fake_device_server import devices as s_devices


class DevicesClient(common_client.CommonClient):
    """Client library for devices method."""

    def __init__(self, *args, **kwargs):
        common_client.CommonClient.__init__(
                self, s_devices.DEVICES_PATH, *args, **kwargs)


    def get_device(self, device_id):
        """Returns info about the given |device_id|.

        @param device_id: valid device_id.
        """
        url_h = urllib2.urlopen(self.get_url([device_id]))
        return json.loads(url_h.read())


    def list_devices(self):
        """Returns the list of the devices the server currently knows about."""
        url_h = urllib2.urlopen(self.get_url())
        return json.loads(url_h.read())


    def create_device(self, system_name, device_kind, channel, **kwargs):
        """Creates a device using the args.

        @param system_name: name to give the system.
        @param device_kind: type of device.
        @param channel: supported communication channel.
        @param kwargs: additional dictionary of args to put in config.
        """
        data = dict(systemName=system_name,
                    deviceKind=device_kind,
                    channel=channel,
                    **kwargs)
        request = urllib2.Request(self.get_url(), json.dumps(data),
                                  {'Content-Type': 'application/json'})
        url_h = urllib2.urlopen(request)
        return json.loads(url_h.read())