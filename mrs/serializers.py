# Mrs
# Copyright 2008-2012 Brigham Young University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import division, print_function

from collections import namedtuple


Serializer = namedtuple('Serializer', ('dumps', 'loads'))

def output_serializers(**kwargs):
    """A decorator to specify key and value serializers for map or 
    reduce functions.

    The two allowable keyword arguments are `key` and
    `value`. These are serializers, which must be attributes of the program.
    A serializer implements both the `dumps` and loads` methods.

    Note that if None is given as a serializer, then pickle is used as the
    default serializer.
    """
    def wrapper(f):
        if 'key' in kwargs:
            f.key_serializer = kwargs['key']
            del kwargs['key']
        if 'value' in kwargs:
            f.value_serializer = kwargs['value']
            del kwargs['value']
        if kwargs:
            raise TypeError('Invalid keyword argument(s) for this function')
        return f

    return wrapper


class Serializers(object):
    """Keeps track of a pair of serializers and their names."""

    def __init__(self, key_s, key_s_name, value_s,
            value_s_name):
        self.key_s = key_s
        self.key_s_name = key_s_name
        self.value_s = value_s
        self.value_s_name = value_s_name

    @classmethod
    def from_names(cls, names, program):
        """Creates a Serializers from a pair of names and a MapReduce program.
        """

        if not names:
            return None
        key_s_name, value_s_name = names

        if key_s_name:
            try:
                key_s = getattr(program, key_s_name)
            except AttributeError:
                msg = 'Key serializer not an attribute of the program'
                raise RuntimeError(msg)
        else:
            key_s = None

        if value_s_name:
            try:
                value_s = getattr(program, value_s_name)
            except AttributeError:
                msg = 'Value serializer not an attribute of the program'
                raise RuntimeError(msg)
        else:
            value_s = None

        return cls(key_s, key_s_name, value_s, value_s_name)

    def __repr__(self):
        return 'Serializers(%r, %r, %r, %r)' % (self.key_s,
                self.key_s_name, self.value_s, self.value_s_name)


###############################################################################
# bytes <-> bytes (no-op)

raw_serializer = Serializer(None, None)

###############################################################################
# str <-> bytes

def str_loads(b):
    return b.decode('utf-8')

def str_dumps(s):
    return s.encode('utf-8')

str_serializer = Serializer(str_dumps, str_loads)

###############################################################################
# int <-> bytes

def int_loads(b):
    return int(b.decode('utf-8'))

def int_dumps(i):
    return str(i).encode('utf-8')

int_serializer = Serializer(int_dumps, int_loads)

# vim: et sw=4 sts=4
