import sys
import time
import subprocess
from otii_tcp_client import otii_connection, otii as otii_application


MEASUREMENT_DURATION = 5.0


class OtiiTesterClient(object):

    def __init__(self, hostname, port, arc_name):
        self.hostname = hostname
        self.port = port
        self.arc_name = arc_name

        # initilization
        self.otii = self.connect_to_otii()
        self.arc = self.get_otii_arc()
        self.set_up_arc()  # with default values

    def connect_to_otii(self):
        connection = otii_connection.OtiiConnection(self.hostname, self.port)
        connect_response = connection.connect_to_server()
        if connect_response["type"] == "error":
            print("Exit! Error code: " + connect_response["errorcode"] + ", Description: " + connect_response["payload"]["message"])
            sys.exit()
        otii = otii_application.Otii(connection)

        return otii

    def get_otii_arc(self):
        devices = self.otii.get_devices()
        if len(devices) == 0:
            print("No Arc connected!")
            sys.exit()
        devices = [device for device in devices if device.name == self.arc_name]
        if len(devices) != 1:
            print("Expected to find exactly 1 device named {0}, found {1} devices".format(self.arc_name, len(devices)))
            sys.exit()
        arc = devices[0]

        return arc

    def set_up_arc(self, main_voltage=3.3, exp_voltage=3.3, max_current=0.5, uart_baudrate=115200, enable_uar=True, enable_exp=True, enable_5v=True):
        arc.set_main_voltage(3.3)
        arc.set_exp_voltage(3.3)
        arc.set_max_current(0.5)
        arc.set_uart_baudrate(115200)
        arc.enable_uart(True)
        arc.enable_exp_port(True)
        arc.enable_5v(True)  # The switch board is powerd by the Otii +5V pin

    def upload_firmware(self):
        self.arc.enable_5v(True)  # The switch board is powered by the Otii +5V pin.

        # Turn on the main power, and give the DUT time to startup.
        self.arc.set_main(True)
        time.sleep(1.0)

        # Enable the USB, and give the ST-lINK time to startup
        self.arc.set_gpo(1, True)
        time.sleep(3.0)

        # Upload new firmware
        result = subprocess.call("cd ../firmware; make; make upload", shell=True)  # TODO: generalise this
        if result != 0:
            print("Falied to upload new firmware")
            sys.exit()
        time.sleep(3.0)

        # Disable the USB, and turn off the main power
        arc.set_gpo(1, False)
        time.sleep(1.0)
        arc.set_main(False)

    def record_data(self, duration=MEASUREMENT_DURATION):
        self.project = self.otii.get_active_project()
        if not self.project:
            project = self.otii.create_project()

        self.arc.enable_channel("mc", True)
        self.arc.enable_channel("me", True)
        self.arc.enable_channel("i1", True)
        self.arc.enable_channel("rx", True)

        self.arc.set_main(True)
        self.project.start_recording()
        time.sleep(duration)
        self.project.stop_recording()

        self.arc.set_main(False)

    # TODO: add from to msg and make multiple methods -> some for 1st occuranve of messages, and 1 for avg, min, max across all occurances.
    def get_energy_consumed_rx(self, msg_begin, msg_end):
        recording = self.project.get_last_recording()
        index = 0
        count = recording.get_channel_data_count(arc.id, "rx")
        data = recording.get_channel_data(arc.id, "rx", index, count)
        values = data["values"]
        timestamps_begin = [value["timestamp"] for value in values if value["value"] == msg_begin]
        timestamps_end = [value["timestamp"] for value in values if value["value"] == msg_end]

        # TODO: loop over all timestamps and do max, min, avg, and count
        start = recording.get_channel_data_index(arc.id, "me", timestamps_begin[0])
        if start > 0:
            start = start - 1
        stop = recording.get_channel_data_index(arc.id, "me", timestamps_end[0])
        count = stop - start
        data = recording.get_channel_data(arc.id, "me", start, 1)
        start_energy = data["values"][0]
        data = recording.get_channel_data(arc.id, "me", stop - 1, 1)
        stop_energy = data["values"][0]
        consumed = (stop_energy - start_energy) / 3600

        return consumed

    def get_energy_consumed_gpi1(self, msg_begin, msg_end):
        pass  # TODO: copy from example and modify similar as above
