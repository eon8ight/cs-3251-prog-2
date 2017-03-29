import socket
from packet import PacketIterator, Packet, ACK, SYNACK, CLOSEACK, CLOSE, _deconstruct_packet, _construct_packet
import datetime
from time import sleep

class Reldat( object ):
    def __init__( self, max_window_size ):
        self.src_ip_address      = socket.gethostbyname( socket.gethostname() )
        self.src_max_window_size = max_window_size

        self.dst_ip_address      = None
        self.dst_max_window_size = None

        self.port       = None
        self.in_socket  = None
        self.out_socket = None
        self.timeout = 3 #seconds

        # Need to ACK
        self.seqs_recd = []

        # Waiting for ACK
        self.seqs_sent = []
        self.timers    = {}

        self.pkt_buffer = [None for _ in range(self.src_max_window_size)]

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
        ack_pkt =  ACK(packet.seq_num, packet.payload.upper())
        self.out_socket.sendto(ack_pkt, self.dst_ip_address)

        pass

    def get_seq_num(self):
        self.seqs_sent.append(self.on_seq)
        self.on_seq += 1
        # TODO add timer and events
        return self.seqs_sent[-1]

    def open_socket(self, port):
        self.port       = port
        self.in_socket  = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.out_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

        self.in_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.in_socket.bind( ( self.src_ip_address, self.port ) )

        print "Listening on port " + str( self.port ) + "."

    def listen( self ):
        data, address = self.in_socket.recvfrom( 1024 )
        packet        = Packet( data )

        if packet.is_open() and not self.has_connection():
            self.establish_connection( address, packet )
        elif packet.is_close() and self.has_connection():
            self.disconnect( packet )
        elif packet.is_data():
            self.conversation( packet )

    def establish_connection( self, dst_ip_address, syn ):
        print "Attempting to establish connection with " + str( dst_ip_address[0] ) + ":" + str( self.port ) + "."

        self.dst_ip_address      = ( dst_ip_address[0], self.port + 1 ) # XXX DEBUG TODO REMOVE
        self.dst_max_window_size = int( syn.payload )

        print "Received SYN (packet 1/3)."

        synack = SYNACK( str( self.src_max_window_size ) )
        self.out_socket.sendto( synack, self.dst_ip_address )

        print "Sent SYNACK (packet 2/3)."

        data, address = self.in_socket.recvfrom( 1024 )
        packet        = Packet( data )

        if packet.is_ack():
            print "Received ACK (packet 3/3)."
            print packet.payload

        print "Connection established."

    def conversation(self, pkt):
        ind_start = pkt.seq_num
        all_data  = ""
        temp = ""

        while (not pkt.is_eod()):
            try:
                print pkt.payload
                print "seq: " + str(pkt.seq_num)
                print "ack: " + str(pkt.ack_num)
                print "flag: " + str(pkt.flag)

                print str(pkt.seq_num) + "/" + str(ind_start)
                index = pkt.seq_num - ind_start
                if (not pkt.is_retransmit() and pkt not in self.pkt_buffer):
                    self.pkt_buffer[index] = pkt
                    print self.pkt_buffer
                sleep(1.4)
                self.send_ack(pkt)

                received_packet, kappa = self.in_socket.recvfrom(1024)
                pkt = Packet(received_packet)

                if (self.buffer_full() and not pkt.is_retransmit()):
                    all_data += self.flush_buffer()
                    ind_start = pkt.seq_num

            except socket.error:
                continue

        print "Received EOD"
        self.send_ack(pkt)

        all_data += self.flush_buffer()
        print "Total data: " + all_data

    def buffer_full(self):
        for data in self.pkt_buffer:
            if (data is None):
                return False
        return True

    def flush_buffer(self):
        buffered_data = ""

        for pkt in self.pkt_buffer:
            if (pkt is not None):
                buffered_data += pkt.payload

        self.pkt_buffer = [None for _ in range(self.src_max_window_size)]
        return buffered_data

    def send( self, data ):
        packetizer = PacketIterator( data, self.dst_max_window_size, self.get_seq_num )

        for packet in packetizer:
            self.out_socket.sendto(packet, self.dst_ip_address)
            sent = _deconstruct_packet(packet)
            self.timers[sent[1]] = datetime.datetime.now()

    def recv( self ):
        while True:
            data, address = self.in_socket.recvfrom(1024)
            if address == self.dst_ip_address:
                packet = Packet(data)
                if packet.is_ack():
                    self.ack_recd(packet)
                else:
                    self.send_ack(packet)
                    return packet

    def disconnect( self, close ):
        print "Attempting to disconnect from " + str( self.dst_ip_address ) + ":" + str( self.port ) + "."
        print "Received CLOSE (packet 1/4)."

        closeack = CLOSEACK()
        self.out_socket.sendto( closeack, self.dst_ip_address )

        print "Sent CLOSEACK (packet 2/4)."

        close = CLOSE()
        self.out_socket.sendto( close, self.dst_ip_address )

        print "Sent server-side CLOSE (packet 3/4)."

        data, address = self.in_socket.recvfrom( 1024 )
        packet        = Packet( data )

        if packet.is_ack():
            print "Received CLOSEACK (packet 4/4)."

        print "Connection terminated."

        self.dst_ip_address      = None
        self.dst_max_window_size = None

    def has_connection(self):
        return self.dst_ip_address is not None
