# SPDX-License-Identifier Apache-2.0

import argparse
import serial
from dataclasses import dataclass


@dataclass
class RfidMessage:
    version: int
    tag: str

    @staticmethod
    def from_bytes(data: bytes) -> "RfidMessage":
        if len(data) != 14:
            raise ValueError(f"Invalid message length {len(data)}")

        head = data[0]
        version = int(data[1:3].decode("ascii"), 16)
        tag = data[3:11].decode("ascii")
        checksum = int(data[11:13].decode("ascii"), 16)
        tail = data[13]
        if head != 0x02 or tail != 0x03:
            raise ValueError(
                f"Invalid message head or tail. Got head={head}, tail={tail}, expected 2 & 3"
            )

        def calculate_checksum() -> int:
            checksum = 0
            csum_data = data[1:11]
            for i in range(0, len(csum_data), 2):
                val = int(csum_data[i : i + 2], 16)
                checksum ^= val
            return checksum

        if calculate_checksum() != checksum:
            raise ValueError(
                f"Checksum mismatch. Got {calculate_checksum()}, expected {checksum}"
            )

        return RfidMessage(
            version=version,
            tag=tag,
        )

    @property
    def formatted_tag(self) -> str:
        return f"{int(self.tag, 16):010d}"


class RFIDReader:
    def __init__(self, device: str):
        self.ser = serial.Serial(device, 9600, timeout=1)

    def read(self) -> RfidMessage:
        while True:
            start_byte = self.ser.read(1)
            if start_byte == b"\x02":
                data = start_byte + self.ser.read(13)
                if len(data) == 14:
                    return RfidMessage.from_bytes(data)


def main(device: str):
    reader = RFIDReader(device)
    print("Ready!")

    while True:
        try:
            print(reader.read().formatted_tag)
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="RFID reader interfacing with the RDM6300 module"
    )
    parser.add_argument(
        "--device", required=True, help="Serial device (e.g., /dev/ttyUSB0)"
    )
    args = parser.parse_args()

    main(args.device)
