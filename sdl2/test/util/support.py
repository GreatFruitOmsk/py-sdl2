# #
# # This file is placed under the public domain.
# #
"""Utility functions for the tests."""
import os

class StreamOutput(object):
    def __init__(self, stream):
        self.stream = stream
        try:
            self.startoffset = self.stream.tell()
        except IOError:
            self.startoffset = 0
        self.curoffset = 0

    def writeline(self, data=None):
        if data:
            self.stream.write(data)
        self.stream.write(os.linesep)
        if data:
            self.curoffset = len(data)
        else:
            self.curoffset = 0
        self.stream.flush()

    def write(self, data):
        self.stream.write(data)
        self.curoffset = len(data)
        self.stream.flush()

    def writesame(self, data):
        overhang = self.curoffset - len(data)
        if overhang > 0:
            self.stream.write("%s %s\r" % (data, " " * overhang))
        else:
            self.stream.write("%s\r" % data)
        self.curoffset = len(data)
        self.stream.flush()
