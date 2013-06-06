# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Galileo base class for other Galileo firmware
@copyright 2012, Maprox LLC
'''

import time, datetime
from struct import unpack, pack, calcsize

from kernel.logger import log
from lib.handler import AbstractHandler
import lib.handlers.galileo.packets as packets

# ---------------------------------------------------------------------------

class GalileoHandler(AbstractHandler):
    """
     Base handler for Galileo protocol
    """
    __commands = {}
    __commands_num_seq = 0
    __imageReceivingConfig = None
    __packNum = 0

    # private buffer for headPacket data
    __headPacketRawData = None
    
    def initialization(self):
        """
         Initialization of the handler
         @return:
        """
        self._packetsFactory = packets.PacketFactory()
        return super(GalileoHandler, self).initialization()

    def needCommandProcessing(self):
        """
         Returns false if we can not process commands
         @return: boolean
        """
        return self.uid and self.__imageReceivingConfig is None

    def processProtocolPacket(self, protocolPacket):
        """
         Process galileo packet.
         @param protocolPacket: Galileo protocol packet
        """
        #if (self.__packNum == 1) and (self.__imageReceivingConfig is None):
        #    self.__packNum += 1
        #    self.sendCommand("Makephoto 1")

        observerPackets = self.translate(protocolPacket)
        self.sendAcknowledgement(protocolPacket)
        if not self.__headPacketRawData:
            self.__headPacketRawData = b''

        if protocolPacket.header == 1:
            self.__headPacketRawData = protocolPacket.rawData

        if protocolPacket.hasTag(0xE1):
            log.info('Device answer is "' +
                protocolPacket.getTag(0xE1).getValue() + '".')

        if len(observerPackets) > 0:
            if 'uid' in observerPackets[0]:
                self.headpack = observerPackets[0]
                self.uid = self.headpack['uid']
                log.info('HeadPack is stored.')
                if 'time' not in self.headpack:
                    observerPackets.remove(self.headpack)

        if protocolPacket.header == 4:
            return self.receiveImage(protocolPacket)

        if len(observerPackets) == 0: return
        log.info('Location packet found. Sending...')

        # MainPack
        for packet in observerPackets:
            packet.update(self.headpack)

        log.info(observerPackets)
        self._buffer = self.__headPacketRawData + protocolPacket.rawData
        self.store(observerPackets)

    def sendCommand(self, command):
        """
         Sends command to the tracker
         @param command: Command string
        """
        log.info('Sending "' + command + '"...')
        packet = packets.Packet()
        packet.header = 1
        packet.addTag(0x03, self.headpack['uid'])
        packet.addTag(0x04, self.headpack['uid2'])
        packet.addTag(0xE0, self.__commands_num_seq)
        packet.addTag(0xE1, command)
        self.send(packet.rawData)
        # save sended command in local dict
        self.__commands[self.__commands_num_seq] = packet
        self.__commands_num_seq += 1 # increase command number sequence

    def receiveImage(self, packet):
        """
         Receives an image from tracker.
         Sends it to the observer server, when totally received.
        """
        if (packet == None) or (packet.body == None) or (len(packet.body) == 0):
            log.error('Empty image packet. Transfer aborted!')
            return

        config = self.__imageReceivingConfig
        partnum = packet.body[0]
        if self.__imageReceivingConfig is None:
            self.__imageReceivingConfig = {
              'imageParts': {}
            }
            config = self.__imageReceivingConfig
            log.info('Image transfer is started.')
        else:
            if len(packet.body) > 1:
                log.debug('Image transfer in progress...')
                log.debug('Size of chunk is %d bytes', len(packet.body) - 1)
            else:
                imageData = b''
                imageParts = self.__imageReceivingConfig['imageParts']
                for num in sorted(imageParts.keys()):
                    imageData += imageParts[num]
                self.sendImages([{
                  'mime': 'image/jpeg',
                  'content': imageData
                }])
                self.__imageReceivingConfig = None
                log.debug('Transfer complete.')
                return

        imageData = packet.body[1:]
        config['imageParts'][partnum] = imageData

    def translate(self, data):
        """
         Translate gps-tracker data to observer pipe format
         @param data: dict() data from gps-tracker
        """
        packets = []
        if (data == None): return packets
        if (data.tags == None): return packets

        packet = {}
        sensor = {}
        prevNum = 0
        for tag in data.tags:
            num = tag.getNumber()

            if (num < prevNum):
                self.setPacketSensors(packet, sensor)
                packets.append(packet)
                packet = {}
                sensor = {}

            prevNum = num
            value = tag.getValue()
            #print(num, value)
            if num == 3: # IMEI
                packet['uid'] = value
            elif num == 4: # CODE
                packet['uid2'] = value
            elif num == 32: # Timestamp
                packet['time'] = value.strftime('%Y-%m-%dT%H:%M:%S.%f')
            elif num == 48: # Satellites count, Correctness, Lat, Lon
                packet.update(value)
                sensor['sat_count'] = value['satellitescount']
            elif num == 51: # Speed, Azimuth
                packet.update(value)
            elif num == 52: # Altitude
                packet['altitude'] = value
            elif num == 53: # HDOP
                packet['hdop'] = value
            elif num == 64: # Status
                sensor.update(value)
            elif num == 65: # External voltage
                sensor['ext_battery_voltage'] = value
            elif num == 66: # Internal accumulator voltage
                sensor['int_battery_voltage'] = value
            elif num == 67: # Terminal temperature
                sensor['int_temperature'] = value
            elif num == 68: # Acceleration
                sensor['acceleration_x'] = value['X']
                sensor['acceleration_y'] = value['Y']
                sensor['acceleration_z'] = value['Z']
            elif num == 69: # Digital outputs 1-16
                sensor.update(value)
            elif num == 70: # Digital inputs 1-16
                sensor.update(value)
            elif num in range(80, 84): # Analog input 0 - 4
                sensor['ain%d' % (num - 80)] = value
            elif num in range(112, 120):
                sensor['ext_temperature_%d' % (num - 112)] = value
            elif num == 144:
                sensor['ibutton_1'] = value
            elif num == 192:
                sensor['fms_total_fuel_consumption'] = value
            elif num == 193:
                sensor.update(value)
            elif num == 194:
                sensor['fms_total_mileage'] = value
            elif num == 195:
                sensor['can_b1'] = value
            elif num in range(196, 211):
                sensor['can_8bit_r%d' % (num - 196)] = value
            elif num == 211:
                sensor['ibutton_2'] = value
            elif num == 212:
                sensor['total_mileage'] = value
            elif num == 213:
                sensor.update(value)
            elif num in range(214, 219):
                sensor['can_16bit_r%d' % (num - 214)] = value
            elif num in range(219, 224):
                sensor['can_32bit_r%d' % (num - 219)] = value
        self.setPacketSensors(packet, sensor)
        packets.append(packet)
        return packets

    def sendAcknowledgement(self, packet):
        """
         Sends acknowledgement to the socket
        """
        buf = self.getAckPacket(packet.crc)
        log.info("Send acknowledgement, crc = %d" % packet.crc)
        return self.send(buf)

    @classmethod
    def getAckPacket(cls, crc):
        """
          Returns acknowledgement buffer value
        """
        return pack('<BH', 2, crc)

    def processCommandExecute(self, task, data):
        """
         Execute command for the device
         @param task: id task
         @param data: data dict()
        """
        log.info('Observer is sending a command:')
        log.info(data)
        self.sendCommand(data['command'])

    def processCommandReadSettings(self, task, data):
        """
         Sending command to read all of device configuration
         @param task: id task
         @param data: data string
        """
        pass

    def processCommandSetOption(self, task, data):
        """
         Set device configuration
         @param task: id task
         @param data: data dict()
        """
        pass

    def getInitiationData(self, config):
        """
         Returns initialization data for SMS wich will be sent to device
         @param config: config dict
         @return: array of dict or dict
        """
        return [{
            "message": 'AddPhone 1234'
        }, {
            "message":
                'ServerIp ' + config['host'] + ',' + str(config['port'])
        }, {
            "message":
                'APN ' + config['gprs']['apn'] \
                 + ',' + config['gprs']['username'] \
                 + ',' + config['gprs']['password']
        }]


# ===========================================================================
# TESTS
# ===========================================================================

import unittest
#import time
class TestCase(unittest.TestCase):

    def setUp(self):
        import kernel.pipe as pipe
        self.handler = GalileoHandler(pipe.TestManager(), None)

    def test_packetData(self):
        data = b'\x01"\x00\x03868204000728070\x042\x00' \
             + b'\xe0\x00\x00\x00\x00\xe1\x08Photo ok\x137'
        protocolPackets = packets.Packet.getPacketsFromBuffer(data)
        for packet in protocolPackets:
            self.assertEqual(packet.header, 1)

    def test_packetNewTracker(self):
        data = b'\x01\xaa\x03\x03868204001578425\x042\x00\x10\xe7\x04 ' + \
               b'$\x17\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003\x00' + \
               b'\x00\x00\x004\x00\x005\x00@\xc0#A\x00\x00B[\x0fC\x1a' +\
               b'F\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x042\x00' +\
               b'\x10\xe6\x04 \xf1\x16\x11Q0\x10\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x003\x00\x00\x00\x004\x00\x005\x00@\xc0#A\x00\x00' +\
               b'Bh\x0fC\x1aF\x00\x00P\x00\x00Q\x00\x00\x03' +\
               b'868204001578425\x042\x00\x10\xe5\x04 \xac\x16\x11Q0\x10' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00\x004\x00' +\
               b'\x005\x00@\xc1#A\x00\x00Bb\x0fC\x1aF\x00\x00P\x00\x00Q' +\
               b'\x00\x00\x03868204001578425\x042\x00\x10\xe4\x04 4\x16' +\
               b'\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00' +\
               b'\x004\x00\x005\x00@\xc1#A\x00\x00Bo\x0fC\x1bF\x00\x00P' +\
               b'\x00\x00Q\x00\x00\x03868204001578425\x042\x00\x10\xe3' +\
               b'\x04 \xbb\x15\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003' +\
               b'\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00\x00Bq\x0fC\x1bF' +\
               b'\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x042\x00' +\
               b'\x10\xe2\x04 C\x15\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x003\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00\x00Bt\x0f' +\
               b'C\x1bF\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x042' +\
               b'\x00\x10\xe1\x04 \xcb\x14\x11Q0\x10\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00' +\
               b'\x00B\x82\x0fC\x1bF\x00\x00P\x00\x00Q\x00\x00\x03868204' +\
               b'001578425\x042\x00\x10\xe0\x04 R\x14\x11Q0\x10\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00' +\
               b'@\xc1\x03A\x00\x00B\x90\x0fC\x1cF\x00\x00P\x00\x00Q\x00' +\
               b'\x00\x03868204001578425\x042\x00\x10\xdf\x04 4\x14\x11' +\
               b'Q0\xf0\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00\x00' +\
               b'4\x00\x005\x00@\xc1\x01A\x00\x00B\x94\x0fC\x1cF\x00\x00' +\
               b'P\x00\x00Q\x00\x00\x03868204001578425\x042\x00\x10\xde' +\
               b'\x04 \xf9\x13\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'3\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00\x00B\x89\x0f' +\
               b'C\x1cF\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x04' +\
               b'2\x00\x10\xdd\x04 \x81\x13\x11Q0\x10\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00@\xc1' +\
               b'#A\x00\x00B\x9d\x0fC\x1cF\x00\x00P\x00\x00Q\x00\x00' +\
               b'\x03868204001578425\x042\x00\x10\xdc\x04 \x0c\x13\x11' +\
               b'Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00' +\
               b'\x004\x00\x005\x00@\x81#A\x00\x00B\x9d\x0fC\x1cF\x00' +\
               b'\x00P\x00\x00Q\x00\x00\x03868204001578425\x042\x00\x10' +\
               b'\xdb\x04 \t\x13\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x003\x00\x00\x00\x004\x00\x005\x00@\xc0#A\x00\x00B' +\
               b'\x9d\x0fC\x1cF\x00\x00P\x00\x00Q\x00\x00\x038682040015' +\
               b'78425\x042\x00\x10\xda\x04 \x05\x13\x11Q0\x10\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00' +\
               b'@\xc0#A\x00\x00B\x9d\x0fC\x1cF\x00\x00P\x00\x00Q' +\
               b'\x00\x00\xf4\xdf'
        protocolPackets = packets.Packet.getPacketsFromBuffer(data)
        self.assertEqual(len(protocolPackets), 1)
        observerPackets = self.handler.translate(protocolPackets[0])
        self.assertEqual(len(observerPackets), 14)
        packet = observerPackets[6]
        self.assertEqual(packet['speed'], 0)
        self.assertEqual(packet['uid'], '868204001578425')
    
    def test_processData(self):
        data = b'\x01\xaa\x03\x03868204001578425\x042\x00\x10\xe7\x04 ' + \
               b'$\x17\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003\x00' + \
               b'\x00\x00\x004\x00\x005\x00@\xc0#A\x00\x00B[\x0fC\x1a' +\
               b'F\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x042\x00' +\
               b'\x10\xe6\x04 \xf1\x16\x11Q0\x10\x00\x00\x00\x00\x00\x00' +\
               b'\x00\x003\x00\x00\x00\x004\x00\x005\x00@\xc0#A\x00\x00' +\
               b'Bh\x0fC\x1aF\x00\x00P\x00\x00Q\x00\x00\x03' +\
               b'868204001578425\x042\x00\x10\xe5\x04 \xac\x16\x11Q0\x10' +\
               b'\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00\x004\x00' +\
               b'\x005\x00@\xc1#A\x00\x00Bb\x0fC\x1aF\x00\x00P\x00\x00Q' +\
               b'\x00\x00\x03868204001578425\x042\x00\x10\xe4\x04 4\x16' +\
               b'\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00' +\
               b'\x004\x00\x005\x00@\xc1#A\x00\x00Bo\x0fC\x1bF\x00\x00P' +\
               b'\x00\x00Q\x00\x00\x03868204001578425\x042\x00\x10\xe3' +\
               b'\x04 \xbb\x15\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003' +\
               b'\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00\x00Bq\x0fC\x1bF' +\
               b'\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x042\x00' +\
               b'\x10\xe2\x04 C\x15\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x003\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00\x00Bt\x0f' +\
               b'C\x1bF\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x042' +\
               b'\x00\x10\xe1\x04 \xcb\x14\x11Q0\x10\x00\x00\x00\x00\x00' +\
               b'\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00' +\
               b'\x00B\x82\x0fC\x1bF\x00\x00P\x00\x00Q\x00\x00\x03868204' +\
               b'001578425\x042\x00\x10\xe0\x04 R\x14\x11Q0\x10\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00' +\
               b'@\xc1\x03A\x00\x00B\x90\x0fC\x1cF\x00\x00P\x00\x00Q\x00' +\
               b'\x00\x03868204001578425\x042\x00\x10\xdf\x04 4\x14\x11' +\
               b'Q0\xf0\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00\x00' +\
               b'4\x00\x005\x00@\xc1\x01A\x00\x00B\x94\x0fC\x1cF\x00\x00' +\
               b'P\x00\x00Q\x00\x00\x03868204001578425\x042\x00\x10\xde' +\
               b'\x04 \xf9\x13\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00\x00' +\
               b'3\x00\x00\x00\x004\x00\x005\x00@\xc1#A\x00\x00B\x89\x0f' +\
               b'C\x1cF\x00\x00P\x00\x00Q\x00\x00\x03868204001578425\x04' +\
               b'2\x00\x10\xdd\x04 \x81\x13\x11Q0\x10\x00\x00\x00\x00' +\
               b'\x00\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00@\xc1' +\
               b'#A\x00\x00B\x9d\x0fC\x1cF\x00\x00P\x00\x00Q\x00\x00' +\
               b'\x03868204001578425\x042\x00\x10\xdc\x04 \x0c\x13\x11' +\
               b'Q0\x10\x00\x00\x00\x00\x00\x00\x00\x003\x00\x00\x00' +\
               b'\x004\x00\x005\x00@\x81#A\x00\x00B\x9d\x0fC\x1cF\x00' +\
               b'\x00P\x00\x00Q\x00\x00\x03868204001578425\x042\x00\x10' +\
               b'\xdb\x04 \t\x13\x11Q0\x10\x00\x00\x00\x00\x00\x00\x00' +\
               b'\x003\x00\x00\x00\x004\x00\x005\x00@\xc0#A\x00\x00B' +\
               b'\x9d\x0fC\x1cF\x00\x00P\x00\x00Q\x00\x00\x038682040015' +\
               b'78425\x042\x00\x10\xda\x04 \x05\x13\x11Q0\x10\x00\x00' +\
               b'\x00\x00\x00\x00\x00\x003\x00\x00\x00\x004\x00\x005\x00' +\
               b'@\xc0#A\x00\x00B\x9d\x0fC\x1cF\x00\x00P\x00\x00Q' +\
               b'\x00\x00\xf4\xdf'
        
        h = self.handler
        h.processData(data)
        stored_packets = h.getStore().get_stored_packets()
        
        self.assertEqual(len(stored_packets), 14)
        packet = stored_packets[6]
        self.assertEqual(packet['speed'], 0)
        self.assertEqual(packet['uid'], '868204001578425')
        
