# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


from autotest_lib.client.cros.video import video_player


class NativeHtml5Player(video_player.VideoPlayer):
    """
    Provides an interface to interact with native html5 player in chrome.

    """


    def inject_source_file(self):
        """
        Injects the path to the video file under test into the html doc.


        """
        self.tab.ExecuteJavaScript(
            'loadVideoSource("%s")' % self.video_src_path)


    def is_video_ready(self):
        """
        Determines if a native html5 video is ready by using javascript.

        returns: bool, True if video is ready, else False.

        """
        return self.tab.EvaluateJavaScript('canplay()')


    def play(self):
        """
        Plays the video.

        """
        self.tab.ExecuteJavaScript('play()')


    def seek_to(self, t):
        """
        Seeks a vimeo video to a time stamp.

        @param t: timedelta, time value to seek to.

        """
        cmd = "%s.currentTime=%.3f" % (self.video_id, t.total_seconds())
        self.tab.ExecuteJavaScript(cmd)


    def has_video_finished_seeking(self):
        """
        Determines if a vimeo video has finished seeking.

        """
        return self.tab.EvaluateJavaScript('finishedSeeking()')