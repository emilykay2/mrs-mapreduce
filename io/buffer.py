#!/usr/bin/env python

# Copyright 2008 Brigham Young University
#
# This file is part of Mrs.
#
# Mrs is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# Mrs is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# Mrs.  If not, see <http://www.gnu.org/licenses/>.
#
# Inquiries regarding any further use of the Materials contained on this site,
# please contact the Copyright Licensing Office, Brigham Young University,
# 3760 HBLL, Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail
# copyright@byu.edu.

class Buffer(object):
    """Read data from a filelike object without blocking

    """
    def __init__(self, filelike=None):
        self._data = ''
        self.filelike = filelike
        self.eof = False

    def _append(self, newdata):
        assert(self.eof is False)
        if newdata == '':
            self.eof = True
        else:
            self._data += newdata

    def doRead(self):
        """Called when data are available for reading

        To avoid blocking, read() will only be called once on the underlying
        filelike object.
        """
        assert(self.filelike is not None)
        newdata = self.filelike.read()

    def append(self, newdata):
        """Append additional data to the buffer
        """
        assert(self.filelike is None)
        self._append(newdata)

    def readline(self):
        """Read a complete line from the buffer

        Only complete lines are returned.  If no data are available, or if
        there is no newline character, None will be returned, and any
        remaining data will remain in the buffer.
        """
        data = self._data
        pos = data.find('\n')
        if pos is not -1:
            line = data[0:pos+1]
            self._data = data[pos+1:]
            return line
        else:
            return None

    def fileno(self):
        """Return the filenumber of the underlying filelike

        This will obviously fail if filelike is None or has no fileno.

        >>> b = Buffer(open('/etc/passwd'))
        >>> b.fileno() > 2
        True
        >>>
        """
        return self.filelike.fileno()


def test_buffer():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    test_buffer()

# vim: et sw=4 sts=4
