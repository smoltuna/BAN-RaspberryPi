from bluepy.btle import Scanner, DefaultDelegate


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, is_new_dev, is_new_data):
        pass
        # if is_new_dev:
        #     print(f'Discovered device {dev.addr}')
        # elif is_new_data:
        #     print(f'Received new data from {dev.addr}')
