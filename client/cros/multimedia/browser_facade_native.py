# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""An interface to access the local browser facade."""

import logging

class BrowserFacadeNativeError(Exception):
    """Error in BrowserFacadeNative."""
    pass


class BrowserFacadeNative(object):
    """Facade to access the browser-related functionality."""
    def __init__(self, resource):
        """Initializes the USB facade.

        @param resource: A FacadeResource object.

        """
        self._resource = resource
        self._tabs = dict()


    def new_tab(self, url):
        """Opens a new tab and loads URL.

        @param url: The URL to load.

        """
        logging.debug('Load URL %s', url)
        self._resource.load_url(url)
        self._tabs[url] = self._resource.get_tab()


    def close_tab(self, url):
        """Closes a previously opened tab.

        @param url: The URL loaded for this tab when it was created.

        """
        if url not in self._tabs:
            raise BrowserFacadeNativeError('There is no tab for url %s', url)
        self._resource.close_tab(self._tabs[url])
        logging.debug('Closed URL %s', url)
