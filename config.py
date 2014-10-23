# Network config

aldebaran_host = 'localhost'
aldebaran_base_port = 35000
device_controller_port = 0

device_host = 'localhost'
device_base_port = 35016


# Virtual config

number_of_ioports = 4  # "physically"
number_of_devices = 16  # potentially
ram_size = 0x10000
number_of_interrupts = 256
IVT_size = number_of_interrupts * 2
device_registry_size = number_of_devices * 4
system_interrupts = {
    'device_registered': 30,
    'device_unregistered': 31,
    'ioport_in': [32 + ioport_number for ioport_number in xrange(number_of_ioports)],
    'ioport_out': [48 + ioport_number for ioport_number in xrange(number_of_ioports)],
}
system_addresses = {
    'entry_point': 0x0000,
    'SP': ram_size - IVT_size - device_registry_size - number_of_devices - 1 - 1,
    'default_interrupt_handler': ram_size - IVT_size - device_registry_size - number_of_devices - 1,
    'device_status_table': ram_size - IVT_size - device_registry_size - number_of_devices,
    'device_registry_address': ram_size - IVT_size - device_registry_size,
    'IVT': ram_size - IVT_size,
}
clock_freq = 200  # Hz
