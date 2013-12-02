# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      CRC-16 calculate algorithm
@copyright 2012, Maprox LLC

Some links for smoking:
  http://www.modbus.org/docs/Modbus_over_serial_line_V1_02.pdf

Stolen from:
  http://www.digi.com/wiki/developer/index.php/Python_CRC16_Modbus_DF1

  >> Both the Modbus/RTU and DF1 protocols use the same CRC16 calculation,
     however you'll note one is 'forward' and one 'reverse' because
     Modbus starts with a CRC of 0xFFFF, which DF1 starts with 0x0000.
     The module below uses a 256-word look-up table of partially prepared
     answers to greatly reduce the system load.
'''

INITIAL_MODBUS = 0xFFFF
INITIAL_DF1 = 0x0000

class Crc16(object):
    """ Class for CRC-16 Modbus calculation """

    # ---------------------------------------------------------------
    # 256-word look-up table of partially prepared
    # answers to greatly reduce the system load
    __table = (
      0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
      0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
      0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
      0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
      0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
      0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
      0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
      0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
      0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
      0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
      0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
      0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
      0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
      0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
      0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
      0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
      0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
      0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
      0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
      0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
      0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
      0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
      0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
      0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
      0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
      0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
      0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
      0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
      0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
      0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
      0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
      0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040
    )

    @classmethod
    def calcByte(cls, ch, crc):
        """Given a new Byte and previous CRC, Calc a new CRC-16"""
        if type(ch) == type("c"):
            by = ord(ch)
        else:
            by = ch
        crc = (crc >> 8) ^ cls.__table[(crc ^ by) & 0xFF]
        return (crc & 0xFFFF)

    @classmethod
    def calcString(cls, st, crc):
        """Given a string and starting CRC, Calc a final CRC-16 """
        for ch in st:
            crc = (crc >> 8) ^ cls.__table[(crc ^ ord(ch)) & 0xFF]
        return crc

    @classmethod
    def calcBinaryString(cls, st, crc):
        """Given a binary string and starting CRC, Calc a final CRC-16 """
        for ch in st:
            crc = (crc >> 8) ^ cls.__table[(crc ^ ch) & 0xFF]
        return crc

    @classmethod
    def calcCCITT(cls, data):
        crc16htab = [
            0x00, 16, 32, 48, 64, 80, 96, 112, 129, 145, 161,
            177, 193, 209, 225, 241, 18, 2, 50, 34, 82, 66,
            114, 98, 147, 131, 179, 163, 211, 195, 243, 227,
            36, 52, 4, 20, 100, 116, 68, 84, 165, 181, 133,
            149, 229, 245, 197, 213, 54, 38, 22, 6, 118, 102,
            86, 70, 183, 167, 151, 135, 247, 231, 215, 199,
            72, 88, 104, 120, 8, 24, 40, 56, 201, 217, 233,
            249, 137, 153, 169, 185, 90, 74, 122, 106, 26,
            10, 58, 42, 219, 203, 251, 235, 155, 139, 187,
            171, 108, 124, 76, 92, 44, 60, 12, 28, 237, 253,
            205, 221, 173, 189, 141, 157, 126, 110, 94, 78,
            62, 46, 30, 14, 255, 239, 223, 207, 191, 175,
            159, 143, 145, 129, 177, 161, 209, 193, 241, 225,
            16, 0, 48, 32, 80, 64, 112, 96, 131, 147, 163,
            179, 195, 211, 227, 243, 2, 18, 34, 50, 66, 82,
            98, 114, 181, 165, 149, 133, 245, 229, 213, 197,
            52, 36, 20, 4, 116, 100, 84, 68, 167, 183, 135,
            151, 231, 247, 199, 215, 38, 54, 6, 22, 102,
            118, 70, 86, 217, 201, 249, 233, 153, 137, 185,
            169, 88, 72, 120, 104, 24, 8, 56, 40, 203, 219,
            235, 251, 139, 155, 171, 187, 74, 90, 106, 122,
            10, 26, 42, 58, 253, 237, 221, 205, 189, 173, 157,
            141, 124, 108, 92, 76, 60, 44, 28, 12, 239, 255,
            207, 223, 175, 191, 143, 159, 110, 126, 78, 94,
            46, 62, 14, 30
        ]

        crc16ltab = [
            0, 33, 66, 99, 132, 165, 198, 231, 8, 41, 74, 107,
            140, 173, 206, 239, 49, 16, 115, 82, 181, 148, 247,
            214, 57, 24, 123, 90, 189, 156, 255, 222, 98, 67,
            32, 1, 230, 199, 164, 133, 106, 75, 40, 9, 238, 207,
            172, 141, 83, 114, 17, 48, 215, 246, 149, 180, 91,
            122, 25, 56, 223, 254, 157, 188, 196, 229, 134, 167,
            64, 97, 2, 35, 204, 237, 142, 175, 72, 105, 10, 43,
            245, 212, 183, 150, 113, 80, 51, 18, 253, 220, 191,
            158, 121, 88, 59, 26, 166, 135, 228, 197, 34, 3, 96,
            65, 174, 143, 236, 205, 42, 11, 104, 73, 151, 182,
            213, 244, 19, 50, 81, 112, 159, 190, 221, 252, 27,
            58, 89, 120, 136, 169, 202, 235, 12, 45, 78, 111,
            128, 161, 194, 227, 4, 37, 70, 103, 185, 152, 251,
            218, 61, 28, 127, 94, 177, 144, 243, 210, 53, 20,
            119, 86, 234, 203, 168, 137, 110, 79, 44, 13, 226,
            195, 160, 129, 102, 71, 36, 5, 219, 250, 153, 184,
            95, 126, 29, 60, 211, 242, 145, 176, 87, 118, 21, 52,
            76, 109, 14, 47, 200, 233, 138, 171, 68, 101, 6, 39,
            192, 225, 130, 163, 125, 92, 63, 30, 249, 216, 187,
            154, 117, 84, 55, 22, 241, 208, 179, 146, 46, 15,
            108, 77, 170, 139, 232, 201, 38, 7, 100, 69, 162,
            131, 224, 193, 31, 62, 93, 124, 155, 186, 217, 248,
            23, 54, 85, 116, 147, 178, 209, 240
        ]

        crcHi = 0xff
        crcLo = 0xff

        for k in range(len(data)):
            ix = crcHi ^ int(data[k])
            crcHi = crcLo ^ crc16htab[ix]
            crcLo = crc16ltab[ix]

        return crcHi * 256 + crcLo

# ===========================================================================
# TESTS
# ===========================================================================

import unittest
class TestCase(unittest.TestCase):

    def setUp(self):
        pass

    def test_modbus1(self):
        crc = INITIAL_MODBUS
        st = "\xEA\x03\x00\x00\x00\x64"
        for ch in st:
            crc = Crc16.calcByte(ch, crc)
        self.assertEqual(crc, 0x3A53)

    def test_modbus2(self):
        st = "\x4b\x03\x00\x2c\x00\x37"
        crc = Crc16.calcString(st, INITIAL_MODBUS)
        self.assertEqual(crc, 0xbfcb)

    def test_modbus3(self):
        st = "\x0d\x01\x00\x62\x00\x33"
        crc = Crc16.calcString(st, INITIAL_MODBUS)
        self.assertEqual(crc, 0x0ddd)

    def test_df1(self):
        st = "\x07\x11\x41\x00\x53\xB9\x00\x00\x00" \
           + "\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        # DF1 uses same algorithm - just starts with CRC=0x0000
        # instead of 0xFFFF. Note: <DLE><STX> and the <DLE> of
        # the <DLE><ETX> pair NOT to be included
        crc = Crc16.calcString(st, INITIAL_DF1)
        crc = Crc16.calcByte("\x03", crc) # final ETX added
        self.assertEqual(crc, 0x4C6B)

    def test_CCITT(self):
        self.assertEqual(Crc16.calcCCITT(
            b'\x24\x24\x00\x11\x13\x61\x23\x45\x67\x8f\xff\x50\x00'
        ), 0x05D8)

if __name__ == '__main__':
    unittest.main()