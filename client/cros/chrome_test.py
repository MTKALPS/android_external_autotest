# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import pwd
import re
import shutil
import stat
import subprocess
import tempfile

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import constants, cros_ui, cros_ui_test, ownership


class ChromeTestBase(cros_ui_test.UITest):
    """Base class for running tests obtained from the chrome tree.

    Sets up chrome_test subtree, test binaries, logs in and
    provides utility functions to run chrome binary tests.
    """

    # TODO(nirnimesh): Split this class into two, a base class and another
    #                  for binary tests.

    home_dir = None
    chrome_restart_disabled = False
    CHROME_TEST_DEP = 'chrome_test'
    _MINIDUMPS_FILE = '/mnt/stateful_partition/etc/enable_chromium_minidumps'


    def setup(self):
        cros_ui_test.UITest.setup(self)
        self.job.setup_dep([self.CHROME_TEST_DEP])
        # create an empty srcdir to prevent the error that checks .version file
        if not os.path.exists(self.srcdir):
            os.mkdir(self.srcdir)


    def nuke_chrome(self):
        try:
            open(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE, 'w').close()
            self.chrome_restart_disabled = True
        except IOError as e:
            logging.debug(e)
            raise error.TestError('Failed to disable browser restarting.')
        utils.nuke_process_by_name(name=constants.BROWSER, with_prejudice=True)


    def start_authserver(self):
        # Do not fake login
        pass


    def initialize(self, nuke_browser_norestart=True, skip_deps=False):
        # Make sure Chrome minidumps are written locally.
        # Requires UI restart to take effect. It'll be done by parent's
        # initialize().
        if not os.path.exists(self._MINIDUMPS_FILE):
            open(self._MINIDUMPS_FILE, 'w').close()
        assert os.path.exists(self._MINIDUMPS_FILE)

        cros_ui_test.UITest.initialize(self, creds='$default')

        self.home_dir = tempfile.mkdtemp()
        os.chmod(self.home_dir, stat.S_IROTH | stat.S_IWOTH |stat.S_IXOTH)
        chrome_test_dep_dir = os.path.join(
                self.autodir, 'deps', self.CHROME_TEST_DEP)
        if not skip_deps:
            self.job.install_pkg(self.CHROME_TEST_DEP, 'dep',
                                 chrome_test_dep_dir)
        self.cr_source_dir = '%s/test_src' % chrome_test_dep_dir
        self.test_binary_dir = '%s/out/Release' % self.cr_source_dir
        if nuke_browser_norestart:
            self.nuke_chrome()
        self._setup_for_chrome_test()


    def _setup_for_chrome_test(self):
        try:
            setup_cmd = ('/bin/bash %s/setup_test_links.sh'
                         % self.test_binary_dir)
            utils.system(setup_cmd)  # this might raise an exception
        except error.CmdError as e:
            raise error.TestError(e)

        deps_dir = os.path.join(self.autodir, 'deps')
        utils.system('chown -R chronos ' + self.cr_source_dir)

        # chronos should own the current dir.
        chronos_id = pwd.getpwnam('chronos')
        os.chown(os.getcwd(), chronos_id.pw_uid, chronos_id.pw_gid)

        # Disallow further browser restart by its babysitter.
        if not os.path.exists(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE):
            open(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE, 'w').close()
        assert os.path.exists(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE)


    def filter_bad_tests(self, tests, blacklist=None):
        matcher = re.compile(".+\.(FLAKY|FAILS|DISABLED).+")
        if blacklist:
          return filter(lambda(x): not matcher.match(x) and x not in blacklist,
                        tests)
        else:
          return filter(lambda(x): not matcher.match(x), tests)


    def list_chrome_tests(self, test_binary):
        all_tests = []
        try:
            cmd = '%s/%s --gtest_list_tests' % (self.test_binary_dir,
                                                test_binary)
            cmd = 'HOME=%s CR_SOURCE_ROOT=%s %s' % (self.home_dir,
                                                    self.cr_source_dir,
                                                    cros_ui.xcommand(cmd))
            logging.debug("Running %s" % cmd)
            test_proc = subprocess.Popen(cmd,
                                         shell=True,
                                         stdout=subprocess.PIPE)
            last_suite = None
            skipper = re.compile('YOU HAVE')
            for line in test_proc.stdout:
                stripped = line.lstrip()
                if stripped == '' or skipper.match(stripped):
                    continue
                elif (stripped == line):
                    last_suite = stripped.rstrip()
                else:
                  all_tests.append(last_suite+stripped.rstrip())
        except OSError as e:
            logging.debug(e)
            raise error.TestFail('Failed to list tests in %s!' % test_binary)
        return all_tests


    def run_chrome_test(self, test_to_run, extra_params='', prefix=''):
        """Run chrome binary test."""
        try:
            os.chdir(self.home_dir)
            cmd = '%s/%s %s' % (self.test_binary_dir, test_to_run, extra_params)
            cmd = 'HOME=%s CR_SOURCE_ROOT=%s %s' % (self.home_dir,
                                                    self.cr_source_dir,
                                                    prefix + cmd)
            cros_ui.xsystem_as(cmd)
        except error.CmdError as e:
            logging.debug(e)
            raise error.TestFail('%s failed!' % test_to_run)


    def generate_test_list(self, binary, group, total_groups):
        all_tests = self.list_chrome_tests(self.binary_to_run)
        group_size = len(all_tests)/total_groups + 1  # to be safe
        return all_tests[group*group_size:group*group_size+group_size]


    def cleanup(self):
        if os.path.exists(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE):
            # Allow chrome to be restarted again.
            os.unlink(constants.DISABLE_BROWSER_RESTART_MAGIC_FILE)
        if self.home_dir:
            shutil.rmtree(self.home_dir, ignore_errors=True)
        cros_ui_test.UITest.cleanup(self)


class PyAutoFunctionalTest(ChromeTestBase):
    """Run chrome pyauto functional tests."""

    def initialize(self, auto_login=True):
        # Control whether we want to auto login
        # (auto_login is defined in cros_ui_test.py)
        self.auto_login = auto_login
        ChromeTestBase.initialize(self)


    def run_pyauto_functional(self, suite=None, tests=[], as_chronos=False):
        """Run pyauto functional tests.

        Either suite or tests need to be specified, not both.

        Args:
            suite: the pyauto suite name for the tests to run
            tests: the list of pyauto tests to run
            as_chronos: specify whether tests should be run as chronos
                        (Default: run as root)
        """
        if not (suite or tests):
            raise error.TestError('Should specify suite or tests')
        if suite and tests:
            raise error.TestError('Should specify either suite or tests, '
                                  'not both')

        # Run tests.
        functional_cmd = 'python %s/deps/%s/test_src/' \
            'chrome/test/functional/pyauto_functional.py -v ' % (
            self.autodir, self.CHROME_TEST_DEP)
        if suite:
            functional_cmd += ' --suite=%s' % suite
        elif tests:
            functional_cmd += ' '.join(tests)

        xcommand_func = cros_ui.xcommand_as if as_chronos else cros_ui.xcommand
        launch_cmd = xcommand_func(functional_cmd)
        logging.info('Test launch cmd: %s', launch_cmd)
        utils.system(launch_cmd)
