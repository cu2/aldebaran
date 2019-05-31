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

debugger_host = 'localhost'
debugger_port = 8000


# Virtual config

memory_size = 0x10000  # 65536
ram_size = 0xF000  # 61440
input_buffer_size = 0x100  # 256

number_of_ioports = 16
number_of_interrupts = 256
number_of_subtimers = 16
operand_buffer_size = 16
timer_freq = 10  # Hz
cpu_halt_freq = 1000  # Hz

# physical ram:
IVT_size = number_of_interrupts * 2
IVT_address = ram_size - IVT_size
default_interrupt_handler_address = IVT_address - 1
bottom_of_stack = default_interrupt_handler_address - 1
entry_point = 0x0000

# virtual ram:
device_registry_address = 0xF000
device_registry_size = number_of_ioports * 4
device_status_table_address = device_registry_address + device_registry_size
device_status_table_size = number_of_ioports * 1

system_interrupts = {
    'device_registered': 0x1E,
    'device_unregistered': 0x1F,
    'ioport_in': [0x20 + ioport_number for ioport_number in range(number_of_ioports)],
    'device_status_changed': [0x30 + ioport_number for ioport_number in range(number_of_ioports)],
}
system_addresses = {
    # physical addresses:
    'entry_point': entry_point,
    'bottom_of_stack': bottom_of_stack,
    'default_interrupt_handler': default_interrupt_handler_address,
    'IVT': IVT_address,
    # virtual addresses:
    'device_registry_address': device_registry_address,
    'device_registry_size': device_registry_size,
    'device_status_table_address': device_status_table_address,
    'device_status_table_size': device_status_table_size,
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
