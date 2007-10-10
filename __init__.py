#!/usr/bin/env python

VERSION = '0.1-pre'
PORT = 8888

def main(mapper, reducer):
    """Run a MapReduce program.

    Ideally, your Mrs MapReduce program looks something like this:

    def mapper(key, value):
        yield newkey, newvalue

    def reducer(key, value):
        yield newvalue

    if __name__ == '__main__':
        import mrs
        mrs.main(mapper, reducer)
    """
    from optparse import OptionParser
    import sys

    usage = 'usage: %prog master-type [args] input1 [input2 ...] output\n' \
            '       %prog slave [args] server_url'
    version = 'Mrs %s' % VERSION

    parser = OptionParser(usage=usage)
    parser.add_option('--shared', dest='shared',
            help='Shared storage area (posix only)')
    parser.add_option('-M', '--map-tasks', dest='map_tasks', type='int',
            help='Number of map tasks (parallel only)')
    parser.add_option('-R', '--reduce-tasks', dest='reduce_tasks', type='int',
            help='Number of reduce tasks (parallel only)')
    parser.set_defaults(map_tasks=0, reduce_tasks=0)
    # TODO: other options:
    # input format
    # output format

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error("Requires an subcommand.")
    subcommand = args[0]

    if subcommand in ('posix', 'serial'):
        if len(args) < 3:
            parser.error("Requires inputs and an output.")
        inputs = args[1:-1]
        output = args[-1]
        if subcommand == 'posix':
            retcode = posix(mapper, reducer, inputs, output, options)
        elif subcommand == 'serial':
            retcode = serial(mapper, reducer, inputs, output, options)
    elif subcommand == 'slave':
        if len(args) != 2:
            parser.error("Requires a server address and port.")
        url = args[1]
        retcode = slave(master, reducer, url)
    else:
        parser.error("No such subcommand exists.")

    return retcode


def posix(mapper, reducer, inputs, output, options):
    map_tasks = options.map_tasks
    if map_tasks == 0:
        map_tasks = len(inputs)
    if reduce_tasks == 0:
        reduce_tasks = 1

    if options.map_tasks != len(inputs):
        raise NotImplementedError("For now, the number of map tasks "
                "must equal the number of input files.")

    from mrs.mapreduce import Operation, POSIXJob
    op = Operation(mapper, reducer, map_tasks=map_tasks,
            reduce_tasks=options.reduce_tasks)
    mrsjob = POSIXJob(inputs, output, options.shared)
    mrsjob.operations = [op]
    mrsjob.run()
    return 0


def serial(mapper, reducer, inputs, output, options):
    from mrs.mapreduce import Operation, SerialJob
    op = Operation(mapper, reducer)
    mrsjob = SerialJob(inputs, output)
    mrsjob.operations = [op]
    mrsjob.run()
    return 0

def slave(mapper, reducer, url):
    import slave, rpc
    try:
        server = rpc.rpc_server(slave.SlaveRPC, PORT)
        # TODO: start a worker thread
        # TODO: sign in with the master
        while True:
            server.handle_request()
    except KeyboardInterrupt:
        return -1

# vim: et sw=4 sts=4