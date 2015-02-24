#!/usr/bin/env python

'''A tiny library for parsing, modifying, and composing SRT files.'''

import functools
import re
from datetime import timedelta
from itertools import groupby


SUBTITLE_PATTERN = r'(\d+)\n(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)\n(.+?)\n\n'
SUBTITLE_REGEX = re.compile(SUBTITLE_PATTERN, re.MULTILINE | re.DOTALL)


@functools.total_ordering  # pylint: disable=too-few-public-methods
class Subtitle(object):
    '''
    The metadata relating to a single subtitle.

    :param index: The SRT index for this subtitle
    :param start: A timedelta object representing the time that the subtitle
                  should start being shown
    :param end: A timedelta object representing the time that the subtitle
                should stop being shown
    :param content: The subtitle content
    '''

    def __init__(self, index, start, end, content):
        self.index = index
        self.start = start
        self.end = end
        self.content = content

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __lt__(self, other):
        return self.start < other.start

    def to_srt(self):
        '''
        Convert the current subtitle to an SRT block.

        :returns: A string with the metadata of the current Subtitle object as
                  an SRT formatted subtitle block
        '''
        return '%d\n%s --> %s\n%s\n\n' % (
            self.index, timedelta_to_srt_timestamp(self.start),
            timedelta_to_srt_timestamp(self.end), self.content,
        )


def timedelta_to_srt_timestamp(timedelta_timestamp):
    '''
    Convert a timedelta to an SRT timestamp.

    :param timedelta_timestamp: A timestamp represented as a datetime timedelta
    :returns: An SRT formatted (HH:MM:SS,mmm) string representing the same
              timestamp passed in
    '''
    hrs, remainder = divmod(timedelta_timestamp.seconds, 3600)
    mins, secs = divmod(remainder, 60)
    msecs = timedelta_timestamp.microseconds // 1000
    return '%02d:%02d:%02d,%03d' % (hrs, mins, secs, msecs)


def srt_timestamp_to_timedelta(srt_timestamp):
    '''
    Convert an SRT timestamp to a timedelta.

    :param srt_timestamp: A timestamp in SRT format (HH:MM:SS,mmm)
    :returns: A timedelta object representing the same timestamp passed in
    '''
    hrs, mins, secs, msecs = (int(x) for x in re.split('[,:]', srt_timestamp))
    return timedelta(hours=hrs, minutes=mins, seconds=secs, milliseconds=msecs)


def parse(srt):
    '''
    Convert an SRT formatted string to a generator of Subtitle objects.

    :param srt: A string containing SRT formatted data
    :returns: A generator of the subtitles contained in the SRT file as
              Subtitle objects
    '''
    for match in SUBTITLE_REGEX.finditer(srt):
        raw_index, raw_start, raw_end, content = match.groups()
        yield Subtitle(
            index=int(raw_index), start=srt_timestamp_to_timedelta(raw_start),
            end=srt_timestamp_to_timedelta(raw_end), content=content,
        )


def parse_file(srt):
    '''
    Parse an SRT formatted stream into Subtitle objects.

    :param srt: A stream containing SRT formatted data
    :returns: A generator of the subtitles contained in the SRT file as
              Subtitle objects
    '''
    srt_chomped = (line.rstrip('\n') for line in srt)
    srt_blocks = [
        '\n'.join(srt_lines) + '\n\n'
        for line_has_content, srt_lines in groupby(srt_chomped, bool)
        if line_has_content
    ]

    for srt_block in srt_blocks:
        subtitle, = parse(srt_block)
        yield subtitle


def compose(subtitles):
    '''
    Convert an iterator of Subtitle objects to a string of joined SRT blocks.

    This may be a convienient interface when converting back and forth between
    Python objects and SRT formatted blocks, but you may wish to consider using
    the provided stream interface, `compose_file`, instead, which is
    considerably more memory efficient when dealing with particularly large SRT
    data.

    :param subtitles: An iterator of Subtitle objects, in the order they should
                      be in the output
    :returns: A single SRT formatted string, with each input Subtitle
              represented as an SRT block
    '''
    return ''.join(subtitle.to_srt() for subtitle in subtitles)


def compose_file(subtitles, output):
    '''
    Stream a sequence of Subtitle objects into an SRT formatted stream.

    :param subtitles: An iterator of Subtitle objects, in the order they should
                      be written to the file
    :param output: A stream to write the resulting SRT blocks to

    Returns:
        The number of subtitles that were written to the stream.
    '''
    num_written = 0
    for num_written, subtitle in enumerate(subtitles, start=1):
        output.write(subtitle.to_srt())
    return num_written
