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
    
    def __init__(self):
        self.frame_id = 0
        
    def pack_frame(self, jpeg_payload):
        """
        Packs a JPEG payload into an AEROSAR frame with the 16-byte header.
        
        Args:
            jpeg_payload (bytes): The JPEG encoded image data.
            
        Returns:
            bytes: The complete packet (header + payload) ready for TCP transmission.
        """
        payload_size = len(jpeg_payload)
        timestamp_ms = int(time.time() * 1000)
        
        # Pack header
        header = struct.pack(
            self.HEADER_FORMAT,
            self.frame_id,
            timestamp_ms,
            payload_size
        )
        
        # Increment frame ID for the next frame
        self.frame_id += 1
        
        # Return concatenated packet
        return header + jpeg_payload
