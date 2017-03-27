import socket
from packet import PacketIterator, Packet, SYNACK, _deconstruct_packet
import datetime
from time import sleep

class Reldat( object ):
    def __init__( self, max_window_size ):
        self.src_ip_address      = socket.gethostbyname( socket.gethostname() )
        self.src_max_window_size = max_window_size

        self.dst_ip_address      = None
        self.dst_max_window_size = None

        self.port    = None
        self.socket  = None
        self.timeout = 3 #seconds

        # Need to ACK
        self.seqs_recd = []

        # Waiting for ACK
        self.seqs_sent = []
        self.timers    = {}

        self.on_seq = 0;


    def update_timers(self):
        for seq in self.seqs_sent:
            elapsed = datetime.datetime.now() - self.timers[seq]
            z = divmod(elapsed.total_seconds(), 60)

            if (60 * z[0] + z[1] > self.timeout):
                retransmit_packet(seq)


    def retransmit_packet(self, seq):
        #TODO
        return False

    def ack_recd( self, packet ):
        if packet.is_ack() and packet.ack_num in self.seqs_sent:
            self.seqs_sent.remove( packet.ack_num )
            self.timers[packet.seq_num] = None
            return True

        return False

    def send_ack(self, packet):
        #     TODO
        pass

    def get_seq_num(self):
        self.seqs_sent.append(self.on_seq)
        self.on_seq += 1
        # TODO add timer and events
        return self.seqs_sent[-1]

    def listen( self, port ):
        self.port    = port
        self.socket  = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

        self.socket.bind( ( self.src_ip_address, self.port ) )

        print "Listening on port " + str( self.port ) + "."

        data, address = self.socket.recvfrom( 1024 )
        packet        = Packet( data )

        if packet.is_open():
            self.establish_connection( address, packet )

    def establish_connection( self, dst_ip_address, syn ):
        print "Attempting to establish connection with " + str( dst_ip_address ) + "."

        self.dst_ip_address      = dst_ip_address
        self.dst_max_window_size = int( syn.payload )

        print "Received SYN (packet 1/3)."

        synack = SYNACK( str( self.src_max_window_size ) )
        self.socket.sendto( synack, dst_ip_address )

        print "Sent SYNACK (packet 2/3)."

        while True:
            data, address = self.socket.recvfrom( 1024 )
            packet        = Packet( data )

            if packet.is_ack():
                print "Received ACK (packet 3/3)."
                self.conversation()

            if len( self.seqs_sent ) > 0:
                self.update_timers()

            # TODO add timer with break

        print "Connection established."

    def conversation(self):
        '''while True:
            print "sleeping for 4 secs"
            sleep(4)
            print "we back"
            self.send("TESTING SEND")'''

        print "waiting on packet"
        while True:
            receivedPacket, kappa = self.socket.recvfrom(1024)
            pkt = Packet(receivedPacket)
            print pkt.payload
            print "seq: " + str(pkt.seq_num)
            print "ack: " + str(pkt.ack_num)
            print "flag: " + str(pkt.flag)


    def conversate(self):
        while True:

            packet = self.recv()
            self.send(packet.payload.upper())

    def send( self, data ):
        packetizer = PacketIterator( data, self.dst_max_window_size, self.get_seq_num )

        for packet in packetizer:
            self.socket.sendto(packet, self.dst_ip_address)
            sent = _deconstruct_packet(packet)
            self.timers[sent[1]] = datetime.datetime.now()

    def recv( self ):
        while True:
            data, address = self.socket.recvfrom(1024)
            if address == self.dst_ip_address:
                packet = Packet(data)
                if packet.is_ack():
                    self.ack_recd(packet)
                else:
                    self.send_ack(packet)
                    return packet

    def disconnect( self ):
        # TODO
        pass
