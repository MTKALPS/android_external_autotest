#!/usr/bin/env python

"""
This script generates autotest control files for dEQP. It supports
1) Generate control files for tests with Passing expectations.
2) Generate control files to run tests that are not passing.
3) Decomposing a test into shards. Ideally shard_count is chosen such that
   each shard will run less than 1 minute. It mostly makes sense in
   combination with "hasty".
"""

from collections import namedtuple
# Use 'sudo pip install enum34' to install.
from enum import Enum

Test = namedtuple('Test', 'filter, suite, shards, time, hasty, notpass')

ATTRIBUTES_BVT_CQ = (
    'suite:graphics_per-day, suite:graphics_system, suite:bvt-cq')
ATTRIBUTES_BVT_PB = (
    'suite:graphics_per-day, suite:graphics_system, suite:bvt-perbuild')
ATTRIBUTES_DAILY = 'suite:graphics_per-day, suite:graphics_system'
SUITE_BVT_CQ = 'graphics_per-day, graphics_system, bvt-cq'
SUITE_BVT_PB = 'graphics_per-day, graphics_system, bvt-perbuild'
SUITE_DAILY = 'graphics_per-day, graphics_system'

class Suite(Enum):
    none = 1
    daily = 2
    bvtcq = 3
    bvtpb = 4

tests = [
    Test('dEQP-EGL.functional',    Suite.none,  shards=1,  hasty=False, notpass=True, time='LENGTHY'),
    Test('dEQP-EGL.info',          Suite.none,  shards=1,  hasty=False, notpass=True, time='SHORT'),
    Test('dEQP-EGL.performance',   Suite.none,  shards=1,  hasty=False, notpass=True, time='SHORT'),
    Test('dEQP-EGL.stress',        Suite.none,  shards=1,  hasty=False, notpass=True, time='LONG'),
    Test('dEQP-GLES2.accuracy',    Suite.bvtpb, shards=1,  hasty=False, notpass=True, time='FAST'),
    Test('dEQP-GLES2.capability',  Suite.bvtpb, shards=1,  hasty=False, notpass=True, time='FAST'),
    Test('dEQP-GLES2.functional',  Suite.daily, shards=1,  hasty=False, notpass=True, time='LENGTHY'),
    Test('dEQP-GLES2.functional',  Suite.daily, shards=1,  hasty=True,  notpass=False, time='LONG'),
    Test('dEQP-GLES2.functional',  Suite.bvtpb, shards=10, hasty=True,  notpass=False, time='FAST'),
    Test('dEQP-GLES2.info',        Suite.bvtpb, shards=1,  hasty=False, notpass=True, time='FAST'),
    Test('dEQP-GLES2.performance', Suite.daily, shards=1,  hasty=False, notpass=True, time='LONG'),
    Test('dEQP-GLES2.stress',      Suite.daily, shards=1,  hasty=False, notpass=True, time='LONG'),
    Test('dEQP-GLES3.accuracy',    Suite.bvtpb, shards=1,  hasty=False, notpass=True, time='FAST'),
    Test('dEQP-GLES3.functional',  Suite.daily, shards=1,  hasty=False, notpass=True, time='LENGTHY'),
    Test('dEQP-GLES3.functional',  Suite.daily, shards=1,  hasty=True,  notpass=False, time='LONG'),
    Test('dEQP-GLES3.functional',  Suite.daily, shards=10, hasty=True,  notpass=False, time='FAST'),
    Test('dEQP-GLES3.info',        Suite.bvtpb, shards=1,  hasty=False, notpass=True, time='FAST'),
    Test('dEQP-GLES3.performance', Suite.daily, shards=1,  hasty=False, notpass=True, time='LONG'),
    Test('dEQP-GLES3.stress',      Suite.daily, shards=1,  hasty=False, notpass=True, time='LONG'),
    Test('dEQP-GLES31.functional', Suite.none,  shards=1,  hasty=False, notpass=True, time='LENGTHY'),
    Test('dEQP-GLES31.info',       Suite.none,  shards=1,  hasty=False, notpass=True, time='FAST'),
    Test('dEQP-GLES31.stress',     Suite.none,  shards=1,  hasty=False, notpass=True, time='LONG'),
]

CONTROLFILE_TEMPLATE = (
"""\
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Please do not edit this file! It has been created by generate_controlfiles.py.

NAME = '{0}'
AUTHOR = 'chromeos-gfx'
PURPOSE = 'Run the drawElements Quality Program test suite.'
CRITERIA = 'All of the individual tests must pass.'
ATTRIBUTES = '{1}'
SUITE = '{2}'
TIME = '{3}'
{4}TEST_CATEGORY = 'Functional'
TEST_CLASS = 'graphics'
TEST_TYPE = 'client'
DOC = \"\"\"
This test runs the drawElements Quality Program test suite.
\"\"\"

job.run_test('graphics_dEQP', opts = args + ['filter={5}',
                                             'subset_to_run={6}',
                                             'hasty={7}',
                                             'shard_number={8}',
                                             'shard_count={9}'])""")

#Unlike the normal version it batches many tests in a single run
#to reduce testing time. Unfortunately this is less robust and
#can lead to spurious failures.


def get_controlfilename(test, shard=0):
    return 'control.%s' % get_name(test, shard)

def get_dependencies(test):
    if test.notpass:
        return "DEPENDENCIES = 'cleanup-reboot'\n"
    return ''

def get_suite(test):
    if test.suite == Suite.bvtcq:
        return SUITE_BVT_CQ
    if test.suite == Suite.bvtpb:
        return SUITE_BVT_PB
    if test.suite == Suite.daily:
        return SUITE_DAILY
    return ''

def get_attributes(test):
    if test.suite == Suite.bvtcq:
        return ATTRIBUTES_BVT_CQ
    if test.suite == Suite.bvtpb:
        return ATTRIBUTES_BVT_PB
    if test.suite == Suite.daily:
        return ATTRIBUTES_DAILY
    return ''

def get_time(test):
    return test.time

def get_name(test, shard):
    name = test.filter.replace('dEQP-', '', 1).lower()
    if test.hasty:
        name = '%s.hasty' % name
    if test.shards > 1:
        name = '%s.%d' % (name, shard)
    if test.notpass:
        name = name + '.NotPass'
    return name

def get_testname(test, shard=0):
    return 'graphics_dEQP.%s' % get_name(test, shard)

def write_controlfile(filename, content):
    print 'Writing %s.' % filename
    with open(filename, 'w+') as f:
        f.write(content)

def write_controlfiles(test):
    attributes = get_attributes(test)
    suite = get_suite(test)
    time = get_time(test)
    dependencies = get_dependencies(test)
    if test.shards > 1:
        for shard in xrange(0, test.shards):
            subset = 'Pass'
            testname = get_testname(test, shard)
            filename = get_controlfilename(test, shard)
            content = CONTROLFILE_TEMPLATE.format(
                testname, attributes, suite, time, dependencies,
                test.filter, subset, test.hasty, shard, test.shards)
            write_controlfile(filename, content)
    else:
        if test.notpass:
            subset = 'NotPass'
            testname = get_testname(test)
            filename = get_controlfilename(test)
            content = CONTROLFILE_TEMPLATE.format(
                testname, attributes, suite, time, dependencies, test.filter,
                subset, test.hasty, 0, test.shards)
            write_controlfile(filename, content)
        test = Test(test.filter, test.suite, test.shards, test.time, test.hasty, notpass=False)
        dependencies = get_dependencies(test)
        subset = 'Pass'
        testname = get_testname(test)
        filename = get_controlfilename(test)
        content = CONTROLFILE_TEMPLATE.format(
            testname, attributes, suite, time, dependencies, test.filter,
            subset, test.hasty, 0, test.shards)
        write_controlfile(filename, content)


for test in tests:
    write_controlfiles(test)
