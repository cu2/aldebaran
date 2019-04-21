# Aldebaran

Aldebaran is a 16-bit computer with 64kB RAM emulated in Python.

The specs are partly based on the IBM PC XT, but mostly follow my own design, based on ideas coming from various sources. In spite of the totally inefficient technology (namely Python) it reached the blazing speed of 10-15 kHz on a Macbook Air.

The project is under construction: the architecture, the instruction set and the assembly language are not final/ready yet. Not to mention the missing devices, operating system or high-level language.



## Architecture

![Architecture](docs/aldebaran_architecture.png)


### Clock

The clock sends the CPU a beat every `1/clock_freq` seconds. If it takes more time for the CPU to execute the instruction at hand, the clock will wait and send the next beat as soon as possible. So the effective clock frequency (printed after Aldebaran shuts down) is typically smaller than the theoretical. If `clock_freq` is zero ("TURBO" mode), the clock sends beats as fast as possible.


### RAM

A simple RAM module with 65536 bytes of storage. Capable of reading and writing bytes or words. The stack is stored in the RAM but it's implemented by the CPU.


### CPU

For every clock beat the CPU:

- checks if there's a hardware interrupt coming from the Interrupt Controller (only if the Interrupt Flag is set)
- if yes, it calls the specified interrupt handler routine (based on the Interrupt Vector Table)
- if no, it executes the instruction at the Instruction Pointer (`IP`) and sets the `IP` to the next instruction

The CPU has the following registers:

- 4 generic 16-bit registers: `AX`, `BX`, `CX`, `DX` (with separate lower and upper parts)
- `SP`: Stack Pointer for stack operations
- `BP`: Base Pointer for either using as a frame pointer in the call stack or for generic usage
- `SI`, `DI`: Source and Destination Index registers for either string operations or for generic usage
- `IP`: Instruction Pointer for control flow
- Interrupt Flag: to enable and disable hardware interrupts


### Interrupt Controller

The Interrupt Controller accepts hardware interrupts from internal devices (currently: Device Controller and Timer) and puts them into a FIFO queue. The CPU can take interrupts out of the queue and handle them.

Interrupt numbers (00-FF) are mapped to interrupt handler routines based on the Interrupt Vector Table (a 256 times 2 bytes part of the RAM). Interrupt numbers are the following:

- 00-3F: reserved for hardware interrupts
    - 00-1D: unused (so far)
    - 1E: device_registered (called when a device is registered)
    - 1F: device_unregistered (called when a device is unregistered)
    - 20-2F: ioport_in (called when a device sends data to an IOPort)
    - 30-3F: ioport_out (called after data is sent to a device and the device responds a status)
- 40-7F: reserved for OS and device driver (system) interrupts
- 80-FF: free (user) interrupts

Software interrupts are called by the CPU directly with the `INT` instruction.


### Device Controller and IOPorts

The Device Controller contains 16 IOPorts each capable of communicating with a separate device (via HTTP). The Device Controller handles the slow "physical" (i.e. network) connection to the devices. The IOPorts work fast: they respond to requests from the CPU (`IN` and `OUT` instructions) immediately.

When a new device is connected, first it's registered with an IOPort and into the so called Device Registry. The Device Registry is a part of the RAM. For each IOPort it has 4 bytes:

- 1 byte Device Type (00 if no device is registered)
- 3 bytes Device ID (000000 if no device is registered)

Another part of the RAM is the Device Status Table. For each IOPort it has 1 byte that is the status of the last `OUT` instruction. 0 if it was successful, 1 otherwise.

#### Input scenario

1. Device sends signal to Device Controller
2. Device Controller forwards it to the targeted IOPort
3. IOPort stores the data in its input buffer and calls an `ioport_in` interrupt
4. CPU calls the specified interrupt handler routine
5. The routine uses the `IN` instruction to read the content of the input buffer into RAM
6. IOPort asks Device Controller to send an `ACK` signal to the device
7. Device Controller sends an `ACK` signal to the device

#### Output scenario

1. The `OUT` instruction send a piece of RAM to an IOPort
2. IOPort asks Device Controller to send the data to the device
3. Device Controller sends the data to the device
4. Device Controller puts the status of the device into RAM and calls an `ioport_out` interrupt
5. CPU calls the specified interrupt handler routine
6. The routine checks the Device Status Table in RAM to see the device's status

#### Registering/unregistering devices

1. Device sends signal to Device Controller
2. Device Controller registers/unregisters the device with the specified IOPort
3. Device Controller registers/unregisters the device into the Device Registry in RAM
4. Device Controller calls the `device_registered` or `device_unregistered` interrupt
5. CPU calls the specified interrupt handler routine
6. Device Controller responds to the device


### Timer

Timer is an internal device (i.e. it's not controlled by the Device Controller but directly by the CPU). It runs on a preset frequency (`timer_freq`) independently from the clock and increases a step counter (`step_count`) at every beat. It has 8 subtimers that can be programmed separately with the `SETTMR` instruction.

A subtimer can be in 3 modes:

- `OFF` (`00`): the subtimer does nothing
- `ONESHOT` (`01`): the subtimer waits until `step_count % speed = phase`, then it calls a specified interrupt and switches to `OFF` mode
- `PERIODIC` (`02`): the subtimer waits until `step_count % speed = phase`, then it calls a specified interrupt and waits again

If `speed` is zero, a `ONESHOT` subtimer calls the interrupt at the next beat of the Timer, a `PERIODIC` calls at every beat. In this case `phase` has no meaning. Otherwise `phase` should be between `0` and `speed-1`.



## Programming

### Opcode structure

### Instruction set

[See here](./docs/instruction_set.md)

### Assembly language



## How to install

```
./scripts/setup.sh
```

Requirements: Python 3.x



## How to use

Assemble source code to executable:
```
./assembler.py software/hello.ald
```

Run executable:
```
./aldebaran.py software/hello
```

Run a device:
```
./run_device.py <device_name> <ioport_number> [<optional_arguments_for_device>]
```
