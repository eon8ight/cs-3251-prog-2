#!/usr/bin/python

import re
import socket
import sys

import reldat

def teardown_connection( reldat_conn ):
    # TODO tear down connection
    pass

def transform( reldat_conn, f ):
    # TODO send file to server
    pass

def command_loop( reldat_conn ):
    disconnect = False

    while not disconnect:
        print '>',
        client_input  = raw_input()
        command_parts = re.match( '(\w+)\s*(.+)?', client_input )

        if command_parts is not None:
            command = command_parts.group( 1 )

            if command == 'disconnect':
                disconnect = True
            elif command == 'transform':
                file = command_parts.group( 2 )

                if file is None:
                    print '  Usage: transform <file>'
                else:
                    transform( reldat_conn, file )
            else:
                print '  Unrecognized command. Valid commands are:\n    disconnect\n    transform'

def usage():
    print 'Usage: ./reldata-client.py <host IP address>:<host port> <max receive window size in packets>'
    sys.exit( 0 )

def main( argv ):
    if len( argv ) != 2:
        usage()

    host_machine = re.match( '^(\d{1,3}[.]\d{1,3}[.]\d{1,3}[.]\d{1,3}):(\d{1,5})$', argv[0] )

    if host_machine is None:
        usage()

    ip_address              = host_machine.group( 1 )
    port                    = int( host_machine.group( 2 ) )
    max_receive_window_size = int( argv[1] )

    if port > 65535:
        usage()

    reldat_conn = reldat.Reldat( max_receive_window_size )
    reldat_conn.connect( ip_address, port )
    command_loop( reldat_conn )
    reldat_conn.disconnect()

if __name__ == "__main__":
    main( sys.argv[1:] )

sys.exit( 0 )