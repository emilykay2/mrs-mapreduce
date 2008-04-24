# Mrs
# Copyright 2008 Andrew McNabb <amcnabb-mrs@mcnabbs.org>
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

from twisted.internet import reactor, interfaces
from zope.interface import implements
import twisttest


class LineConsumer(object):
    """Consume data (from a Producer) into a Bucket.

    In this basic consumer, the key-value pair is composed of a line number
    and line contents.  Note that the most valuable method to override in this
    class is __iter__.


    Create a consumer and producer.
    >>> data = "First Line.\\nSecond Line.\\nText without newline."
    >>> bucket = twisttest.TestBucket()
    >>> consumer = LineConsumer(bucket)
    >>> producer = twisttest.TestProducer(data, consumer)
    >>>

    >>> producer.push()
    >>> len(bucket.data)
    2
    >>> bucket.data[0]
    (0, 'First Line.\\n')
    >>> bucket.data[1]
    (1, 'Second Line.\\n')
    >>>
    """

    implements(interfaces.IConsumer)

    def __init__(self, bucket):
        self.bucket = bucket

        self._buffer = ''
        self.producer = None
        self.streaming = False

    def registerProducer(self, producer, streaming):
        """Called by the producer when it's ready.

        The streaming parameter indicates whether it's a "push producer"
        as opposed to a "pull producer."
        """
        self.producer = producer
        self.streaming = streaming

    def unregisterProducer(self):
        """Called by the producer when it's exhausted."""
        self.producer = None

    def __iter__(self):
        """Iterate over key-value pairs.
        
        Inheriting classes will almost certainly override this method.
        """
        for index, line in enumerate(self.lines()):
            yield index, line

    def lines(self):
        """Iterate over complete lines in the buffer.

        Note that the lines are removed.  If the last line is a partial line
        (i.e., it doesn't have a trailing newline), it is left in the buffer.
        Also note that the buffer must be left alone while we do this.
        """
        from cStringIO import StringIO
        stringio = StringIO(self._buffer)
        self._buffer = ''
        for line in stringio:
            if line[-1] == '\n':
                yield line
            else:
                # premature end; save partial line back to buffer
                self._buffer = line

    def write(self, data):
        """Called by a Producer when data are available."""
        self._buffer += data
        self.bucket.collect(self)

        if not self.streaming:
            self.producer.resumeProducing()


def test():
    import doctest
    #twisttest.start_reactor()
    doctest.testmod()
    #twisttest.cleanup_reactor()

if __name__ == "__main__":
    test()

# vim: et sw=4 sts=4
