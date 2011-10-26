# Copyright (c) 2011 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import dbus
import glob
import logging
import json
import os

from autotest_lib.client.bin import test
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros.cros_disks import CrosDisksTester
from autotest_lib.client.cros.cros_disks import ExceptionSuppressor
from autotest_lib.client.cros.cros_disks import VirtualFilesystemImage
from autotest_lib.client.cros.cros_disks import DefaultFilesystemTestContent


class CrosDisksFilesystemTester(CrosDisksTester):
    """A tester to verify filesystem support in CrosDisks.
    """
    def __init__(self, test, test_configs):
        super(CrosDisksFilesystemTester, self).__init__(test)
        self._test_configs = test_configs

    def _run_test_config(self, config):
        logging.info('Testing "%s"', config['description'])
        is_experimental = config.get('experimental_features_enabled', False)
        test_mount_filesystem_type = config.get('test_mount_filesystem_type')
        test_mount_options = config.get('test_mount_options')

        # Create a virtual filesystem image based on the specified parameters in
        # the test configuration and use it to verify that CrosDisks can
        # recognize and mount the filesystem properly.
        with VirtualFilesystemImage(
                block_size=config['block_size'],
                block_count=config['block_count'],
                filesystem_type=config['filesystem_type'],
                mount_filesystem_type=config.get('mount_filesystem_type'),
                mkfs_options=config.get('mkfs_options')) as image:
            image.format()
            image.mount(options=['sync'])
            test_content = DefaultFilesystemTestContent()
            if not test_content.create(image.mount_dir):
                raise error.TestFail("Failed to create filesystem test content")
            image.unmount()

            device_file = image.loop_device

            # If the filesystem type is an experimental feature, verify that
            # CrosDisks fails to mount the filesystem when the
            # ExperimentalFeaturesEnabled property is set to false, and succeeds
            # after ExperimentalFeaturesEnabled is set to true.
            self.cros_disks.experimental_features_enabled = False
            if is_experimental:
                self.cros_disks.mount(device_file, test_mount_filesystem_type,
                                      test_mount_options)
                expected_mount_completion = {
                    'source_path': device_file,
                }
                self.cros_disks.expect_mount_completion(
                        expected_mount_completion)
                # The mount path is reserved on failure, so the test needs to
                # unmount it before retrying with ExperimentalFeaturesEnabled
                # set to true.
                self.cros_disks.unmount(device_file, ['force'])
                self.cros_disks.experimental_features_enabled = True

            if self.cros_disks.experimental_features_enabled:
                logging.debug('Experimental features are enabled in cros-disks')

            self.cros_disks.mount(device_file, test_mount_filesystem_type,
                                  test_mount_options)
            expected_mount_completion = {
                'status': config['expected_mount_status'],
                'source_path': device_file,
            }
            if 'expected_mount_path' in config:
                expected_mount_completion['mount_path'] = \
                    config['expected_mount_path']
            result = self.cros_disks.expect_mount_completion(
                    expected_mount_completion)
            if not test_content.verify(result['mount_path']):
                raise error.TestFail("Failed to verify filesystem test content")
            self.cros_disks.unmount(device_file, ['force'])

    def test_using_virtual_filesystem_image(self):
        experimental = self.cros_disks.experimental_features_enabled
        try:
            for config in self._test_configs:
                self._run_test_config(config)
        finally:
            # Always restore the original value of the ExperimentalFeaturesEnabled
            # property, so cros-disks maintains in the same state of support
            # experimental features before and after tests.
            self.cros_disks.experimental_features_enabled = experimental

    def get_tests(self):
        return [self.test_using_virtual_filesystem_image]


class platform_CrosDisksFilesystem(test.test):
    version = 1

    def run_once(self, *args, **kwargs):
        test_configs = []
        config_file = '%s/%s' % (self.bindir, kwargs['config_file'])
        with open(config_file, 'rb') as f:
            test_configs.extend(json.load(f))

        tester = CrosDisksFilesystemTester(self, test_configs)
        tester.run(*args, **kwargs)
