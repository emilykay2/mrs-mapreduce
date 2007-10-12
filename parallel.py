#!/usr/bin/env python

PING_INTERVAL = 5.0

def run_master(inputs, output, options):
    """Mrs Master
    """
    map_tasks = options.map_tasks
    if map_tasks == 0:
        map_tasks = len(inputs)
    if reduce_tasks == 0:
        reduce_tasks = 1

    if options.map_tasks != len(inputs):
        raise NotImplementedError("For now, the number of map tasks "
                "must equal the number of input files.")

    from mrs.mapreduce import Operation
    op = Operation(mapper, reducer, partition, map_tasks=map_tasks,
            reduce_tasks=options.reduce_tasks)
    mrsjob = ParallelJob(inputs, output, options.shared)
    mrsjob.operations = [op]
    mrsjob.run()
    return 0

def run_slave(mapper, reducer, uri, options):
    """Mrs Slave

    The uri is of the form scheme://username:password@host/target with
    username and password possibly omitted.
    """
    import slave, rpc
    import select, xmlrpclib

    # Create an RPC proxy to the master's RPC Server
    master = xmlrpclib.ServerProxy(uri)

    # Start up a worker thread.  This thread will die when we do.
    worker = slave.Worker()
    worker.start()

    # Startup a slave RPC Server
    slave_rpc = slave.SlaveRPC(worker)
    server = rpc.new_server(slave_rpc, options.port)
    server_fd = server.fileno()
    host, port = server.server_address

    # Register with master.
    if not master.signin(slave_rpc.cookie, port):
        import sys
        print >>sys.stderr, "Master rejected signin."
        return -1

    while slave_rpc.alive:
        rlist, wlist, xlist = select.select([server_fd], [], [], PING_INTERVAL)
        if server_fd in rlist:
            server.handle_request()
        else:
            # try to ping master
            try:
                # TODO: consider setting socket.setdefaulttimeout()
                master_alive = master.ping()
            except:
                master_alive = False
            if not master_alive:
                print >>sys.stderr, "Master failed to respond to ping."
                return -1
    return 0


class ParallelJob(Job):
    """MapReduce execution in parallel, with a master and slaves.

    For right now, we require POSIX shared storage (e.g., NFS).
    """
    def __init__(self, inputs, output_dir, shared_dir, reduce_tasks=1, **kwds):
        Job.__init__(self, **kwds)
        self.inputs = inputs
        self.output_dir = output_dir
        self.shared_dir = shared_dir

    def run(self):
        ################################################################
        # TEMPORARY LIMITATIONS
        if len(self.operations) != 1:
            raise NotImplementedError("Requires exactly one operation.")
        operation = self.operations[0]

        map_tasks = operation.map_tasks
        if map_tasks != len(self.inputs):
            raise NotImplementedError("Requires exactly 1 map_task per input.")

        reduce_tasks = operation.reduce_tasks
        ################################################################

        import sys, os
        import formats, master, rpc
        from tempfile import mkstemp, mkdtemp

        # Start RPC master server thread
        master_rpc = master.MasterRPC()
        rpc_thread = rpc.RPCThread(master_rpc, options.port)
        rpc_thread.start()
        port = rpc_thread.server.server_address[1]
        print >>sys.stderr, "Listening on port %s" % port


        # PREP
        jobdir = mkdtemp(prefix='mrs.job_', dir=self.shared_dir)

        interm_path = os.path.join(jobdir, 'interm_')
        interm_dirs = [interm_path + str(i) for i in xrange(reduce_tasks)]
        for name in interm_dirs:
            os.mkdir(name)

        output_dir = os.path.join(jobdir, 'output')
        os.mkdir(output_dir)


        ### IN PROGRESS ###

        # MAP PHASE
        ## still serial
        for mapper_id, filename in enumerate(self.inputs):
            map_task = MapTask(operation.mapper, operation.partition,
                    input, reduce_tasks, interm_path)

            ######################

        for reducer_id in xrange(operation.reduce_tasks):
            # SORT PHASE
            interm_directory = interm_path + str(reducer_id)
            fd, sorted_name = mkstemp(prefix='mrs.sorted_')
            os.close(fd)
            interm_filenames = [os.path.join(interm_directory, s)
                    for s in os.listdir(interm_directory)]
            formats.hexfile_sort(interm_filenames, sorted_name)

            # REDUCE PHASE
            sorted_file = formats.HexFile(open(sorted_name))
            basename = 'reducer_%s' % reducer_id
            output_name = os.path.join(self.output_dir, basename)
            output_file = operation.output_format(open(output_name, 'w'))

            reduce(operation.reducer, sorted_file, output_file)

            sorted_file.close()
            output_file.close()


# vim: et sw=4 sts=4