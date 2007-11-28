#!/usr/bin/env python

# TODO: right now we assume that input files are pre-split.

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

import threading


# maybe this should be ParallelDataSet:
class DataSet(object):
    """Manage input to or output from a map or reduce operation.
    
    The data are evaluated lazily.  A DataSet knows how to generate or
    regenerate its contents.  It can also decide whether to save the data to
    permanent storage or to leave them in memory on the slaves.
    """
    def __init__(self, input, outdir, registry, func_name, part_name,
            ntasks=1, nparts=1):
        self.input = input
        self.outdir = outdir
        self.registry = registry
        self.func_name = func_name
        self.part_name = part_name
        self.ntasks = ntasks
        self.nparts = nparts

        self.tasks_made = False
        self.tasks_todo = []
        self.tasks_done = []
        self.tasks_active = []

        # TODO: store a mapping from tasks to hosts and a map from hosts to
        # tasks.  This way you can know where to find data.  You also know
        # which hosts to restart in case of failure.

    def done(self):
        if self.tasks_made and (self.tasks_todo or self.tasks_active):
            return False
        else:
            return True

    def get_task(self):
        """Return the next available task"""
        if self.tasks_todo:
            task = self.tasks_todo.pop()
            return task
        else:
            return

    def print_status(self):
        active = len(self.tasks_active)
        todo = len(self.tasks_todo)
        done = len(self.tasks_done)
        total = active + todo + done
        print 'Completed: %s/%s, Active: %s' % (done, total, active)


class MapData(DataSet):
    def __init__(self, input, outdir, registry, map_name, part_name, ntasks,
            nparts):
        DataSet.__init__(self, input, outdir, registry, map_name, part_name,
                ntasks, nparts)

    def make_tasks(self):
        from mapreduce import MapTask
        # TODO: relax this assumption:
        assert self.ntasks == len(self.input)
        #for taskid in xrange(self.ntasks):
        for taskid, filename in enumerate(self.input):
            task = MapTask(taskid, self.registry, self.func_name,
                    self.part_name, self.outdir, self.nparts)
            task.inputs = [filename]
            task.dataset = self
            self.tasks_todo.append(task)
        self.tasks_made = True


class ReduceData(DataSet):
    def __init__(self, input, outdir, registry, reduce_name, part_name,
            ntasks, nparts):
        DataSet.__init__(self, input, outdir, registry, reduce_name,
                part_name, ntasks, nparts)

    def make_tasks(self):
        from mapreduce import ReduceTask
        # TODO: relax this assumption:
        assert self.ntasks == len(self.input)
        #for taskid in xrange(self.ntasks):
        for taskid, filename in enumerate(self.input):
            task = ReduceTask(taskid, self.registry, self.func_name,
                    self.outdir)
            task.inputs = [filename]
            task.dataset = self
            self.tasks_todo.append(task)
        self.tasks_made = True


# vim: et sw=4 sts=4
