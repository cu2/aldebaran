'''
System config
'''

from . import boot


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
number_of_timers = 16
timer_freq = 10  # Hz

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

def create_boot_image():
    '''
    Create boot image
    '''
    boot_image = boot.BootImage(ram_size)
    # default interrupt handler
    from instructions.instruction_set import INSTRUCTION_SET
    instruction_mapping = {
        inst.__name__: (opcode, inst)
        for opcode, inst in INSTRUCTION_SET
    }
    boot_image.write_byte(
        system_addresses['default_interrupt_handler'],
        instruction_mapping['IRET'][0],
    )
    # IVT
    for int_num in range(number_of_interrupts):
        boot_image.write_word(
            system_addresses['IVT'] + int_num * 2,
            system_addresses['default_interrupt_handler'],
        )
    return boot_image
