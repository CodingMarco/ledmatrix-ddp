import logging
import struct
import socket

import numpy as np

_LOGGER = logging.getLogger(__name__)


class DDPDevice:
    """DDP device support"""

    # PORT = 4048
    HEADER_LEN = 0x0A
    # DDP_ID_VIRTUAL     = 1
    # DDP_ID_CONFIG      = 250
    # DDP_ID_STATUS      = 251

    MAX_PIXELS = 480
    MAX_DATALEN = MAX_PIXELS * 3  # fits nicely in an ethernet packet

    VER = 0xC0  # version mask
    VER1 = 0x40  # version=1
    PUSH = 0x01
    QUERY = 0x02
    REPLY = 0x04
    STORAGE = 0x08
    TIME = 0x10
    DATATYPE = 0x01
    SOURCE = 0x01
    TIMEOUT = 1

    def __init__(self, dest, port=4048):
        self.frame_count = 0
        self.connection_warning = False
        self._destination = dest
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def flush(self, data):
        self.frame_count += 1
        try:
            DDPDevice.send_out(
                self._sock,
                self._destination,
                self._port,
                data,
                self.frame_count,
            )
            if self.connection_warning:
                # If we have reconnected, log it, come back online, and fire an event to the frontend
                _LOGGER.info(f"DDP connection reestablished to {self.name}")
                self.connection_warning = False
                self._online = True
        except OSError as e:
            # print warning only once until it clears

            if not self.connection_warning:
                # If we have lost connection, log it, go offline, and fire an event to the frontend
                _LOGGER.warning(f"Error in DDP connection to {self.name}: {e}")
                self.connection_warning = True
                self._online = False

    @staticmethod
    def send_out(sock, dest, port, data, frame_count):
        sequence = frame_count % 15 + 1
        byteData = data.astype(np.uint8).flatten().tobytes()
        packets, remainder = divmod(len(byteData), DDPDevice.MAX_DATALEN)
        if remainder == 0:
            packets -= 1  # divmod returns 1 when len(byteData) fits evenly in DDPDevice.MAX_DATALEN

        for i in range(packets + 1):
            data_start = i * DDPDevice.MAX_DATALEN
            data_end = data_start + DDPDevice.MAX_DATALEN
            DDPDevice.send_packet(
                sock, dest, port, sequence, i, byteData[data_start:data_end]
            )

    @staticmethod
    def send_packet(sock, dest, port, sequence, packet_count, data):
        bytes_length = len(data)
        udpData = bytearray()
        header = struct.pack(
            "!BBBBLH",
            DDPDevice.VER1
            | (
                DDPDevice.VER1
                if (bytes_length == DDPDevice.MAX_DATALEN)
                else DDPDevice.PUSH
            ),
            sequence,
            DDPDevice.DATATYPE,
            DDPDevice.SOURCE,
            packet_count * DDPDevice.MAX_DATALEN,
            bytes_length,
        )

        udpData.extend(header)
        udpData.extend(data)

        sock.sendto(
            bytes(udpData),
            (dest, port),
        )
