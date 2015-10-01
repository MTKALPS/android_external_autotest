#!/usr/bin/env python

"""
This file decomposes graphics_dEQP.gles2.functional.hasty into shards.
Ideally shard_count is chosen such that each shard will run less than 1 minute.
"""

CONTROLFILE_TEMPLATE = (
"""
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

NAME = 'graphics_dEQP.gles2.functional.hasty.{0}'
AUTHOR = 'chromeos-gfx'
PURPOSE = 'Run the drawElements Quality Program test suite in hasty mode.'
CRITERIA = 'All of the individual tests must pass.'
ATTRIBUTES = "suite:graphics_per-day, suite:graphics_system, suite:bvt-perbuild"
SUITE = 'graphics_per-day, graphics_system, bvt-perbuild'
TIME = 'MEDIUM'
TEST_CATEGORY = 'Functional'
TEST_CLASS = 'graphics'
TEST_TYPE = 'client'

DOC = \"\"\"
This test runs the drawElements Quality Program test suite. Unlike the
normal version it batches many tests in a single run to reduce testing
time. Unfortunately this is less robust and can lead to spurious
failures.
\"\"\"

job.run_test('graphics_dEQP', opts = args + ['filter=dEQP-GLES2.functional',
                                             'hasty=True',
                                             'shard_number={0}',
                                             'shard_count={1}'])""")


shard_count = 10
for shard_number in xrange(0, shard_count):
  filename = 'control.gles2.functional.hasty.%d' % shard_number
  with open(filename, 'w+') as f:
    content = CONTROLFILE_TEMPLATE.format(shard_number, shard_count)
    f.write(content)