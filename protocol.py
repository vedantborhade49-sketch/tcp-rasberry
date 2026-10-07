import struct
import time

class AerosarProtocol:
    """
    Implements the AEROSAR Frame Protocol.
    
    16-byte header:
    - Bytes 0-3:   frame_id (uint32, big-endian)
    - Bytes 4-11:  timestamp_ms (uint64, big-endian)
    - Bytes 12-15: payload_size (uint32, big-endian)
    
    Format string: ">IQI"
    """
    
    HEADER_FORMAT = ">IQI"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    def pack_frame(self, frame_id, jpeg_payload):
        """
        Packs a JPEG payload into an AEROSAR frame with the 16-byte header.
        Frame ID is passed externally to ensure it only increments when transmitted.
        """
        payload_size = len(jpeg_payload)
        timestamp_ms = int(time.time() * 1000)
        
        # Pack header
        header = struct.pack(
            self.HEADER_FORMAT,
            frame_id,
            timestamp_ms,
            payload_size
        )
        
        # Return concatenated packet
        return header + jpeg_payload
