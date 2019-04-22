from . import utils


# Network config

aldebaran_host = 'localhost'
aldebaran_base_port = 35000
device_controller_port = 0

device_host = 'localhost'
device_base_port = 35016


# Virtual config

number_of_ioports = 16
ram_size = 0x10000
number_of_interrupts = 256
IVT_size = number_of_interrupts * 2
device_registry_size = number_of_ioports * 4
system_interrupts = {
    'device_registered': 0x1E,
    'device_unregistered': 0x1F,
    'ioport_in': [0x20 + ioport_number for ioport_number in range(number_of_ioports)],
    'ioport_out': [0x30 + ioport_number for ioport_number in range(number_of_ioports)],
}
system_addresses = {
    'entry_point': 0x0000,
    'SP': ram_size - IVT_size - device_registry_size - number_of_ioports - 1 - 1,
    'default_interrupt_handler': ram_size - IVT_size - device_registry_size - number_of_ioports - 1,
    'device_status_table': ram_size - IVT_size - device_registry_size - number_of_ioports,
    'device_registry_address': ram_size - IVT_size - device_registry_size,
    'IVT': ram_size - IVT_size,
}
clock_freq = 10000  # Hz
timer_freq = 10  # Hz
number_of_timers = 16


# Logging

minimal_loggers = {
    'aldebaran': utils.Log(),
    'clock': None,
    'cpu': None,
    'user': utils.Log(),
    'ram': None,
    'interrupt_controller': None,
    'device_controller': None,
    'timer': None,
}
normal_loggers = {
    'aldebaran': utils.Log(),
    'clock': None,
    'cpu': utils.Log(),
    'user': utils.Log(),
    'ram': None,
    'interrupt_controller': utils.Log(),
    'device_controller': utils.Log(),
    'timer': None,
}
full_loggers = {
    'aldebaran': utils.Log(),
    'clock': utils.Log(),
    'cpu': utils.Log(),
    'user': utils.Log(),
    'ram': utils.Log(),
    'interrupt_controller': utils.Log(),
    'device_controller': utils.Log(),
    'timer': utils.Log(),
}

# choose verbosity:
loggers = minimal_loggers
# loggers = normal_loggers
