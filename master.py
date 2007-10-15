#!/usr/bin/env python

# TODO: Switch to using "with" for locks when we stop supporting pre-2.5.
# from __future__ import with_statement

class MasterRPC(object):
    # Be careful how you name your methods.  Any method not beginning with an
    # underscore will be exposed to remote hosts.

    def __init__(self):
        import threading
        self.activity = threading.Event()
        self.slaves = Slaves()

    def _listMethods(self):
        import SimpleXMLRPCServer
        return SimpleXMLRPCServer.list_public_methods(self)

    def signin(self, cookie, slave_port, host=None, port=None):
        """Slave reporting for duty.
        """
        slave = Slave(host, slave_port, cookie)
        self.slaves.add_slave(slave)
        self.activity.set()
        return True

    def done(self, cookie, host=None, port=None):
        """Slave is done with whatever it was working on.
        """
        # MORE HERE
        self.activity.set()

    def ping(self, **kwds):
        """Slave checking if we're still here.
        """
        # TODO: return False if they're not signed in
        return True


class Slave(object):
    def __init__(self, host, port, cookie):
        self.host = host
        self.port = port
        self.cookie = cookie
        self.task = None
        import xmlrpclib
        uri = "http://%s:%s" % (host, port)
        self.slave_rpc = xmlrpclib.ServerProxy(uri)

    def __hash__(self):
        return hash(self.cookie)

    def assign_task(self, task):
        from mapreduce import MapTask, ReduceTask
        if isinstance(task, MapTask):
            self.slave_rpc.start_map(task.taskid, task.input, task.outprefix,
                    task.reduce_tasks, self.cookie)
        elif isinstance(task, ReduceTask):
            pass
        else:
            raise TypeError("Requires a MapTask or ReduceTask!")
        self.task = task


class Slaves(object):
    def __init__(self):
        self._slaves = {}
        self._idle_slaves = []

        import threading
        # TODO: consider reimplementing _lock and _idle_sem as a single
        # Condition variable.
        self._lock = threading.Lock()
        self._idle_sem = threading.Semaphore()

    def get_slave(cookie, host=None):
        """Find the slave associated with the given cookie.
        """

    def slave_list(self):
        """Get a snapshot of the current slaves.
        """
        self._lock.acquire()
        lst = self._slaves.values()
        self._lock.release()
        return lst

    def add_slave(self, slave):
        """Add a new idle slave.
        """
        self._lock.acquire()
        self._slaves[slave.cookie] = slave
        self._lock.release()

        self.push_idle(slave)

    def remove_slave(self, slave):
        """Remove a slave, whether it is busy or idle.

        Presumably, the slave has stopped responding.
        """
        self._lock.acquire()
        if slave in self._idle_slaves:
            # Note that we don't decrement the semaphore.  Tough luck for the
            # sap that thinks the list has more entries than it does.
            self._idle_slaves.remove(slave)
        del self._slaves[slave.cookie]
        self._lock.release()

    def push_idle(self, slave):
        """Set a slave as idle.
        """
        print "Calling push_idle."
        self._lock.acquire()
        if slave.cookie not in self._slaves:
            self._lock.release()
            raise RuntimeError("Slave does not exist!")
        if slave not in self._idle_slaves:
            self._idle_slaves.append(slave)
        self._idle_sem.release()
        self._lock.release()

    def pop_idle(self, blocking=False):
        """Request an idle slave, setting it as busy.

        Return None if all slaves are busy.  Block if requested with the
        blocking parameter.  If you set blocking, we will never return None.
        """
        idler = None
        while idler is None:
            if self._idle_sem.acquire(blocking):
                self._lock.acquire()
                try:
                    idler = self._idle_slaves.pop()
                except IndexError:
                    # This can happen if remove_slave was called.  So sad.
                    pass
                self._lock.release()
            if not blocking:
                break
        return idler


if __name__ == '__main__':
    # Testing standalone server.
    import rpc
    instance = MasterRPC()
    PORT = 8000
    #PORT = 0
    server = rpc.new_server(instance, host='127.0.0.1', port=PORT)
    server.serve_forever()


# vim: et sw=4 sts=4
