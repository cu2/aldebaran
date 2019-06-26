# How does it work?


## Basics

- BootLoader loads an image into RAM: default interrupts handlers, device registry...
- BootLoader loads an executable into RAM: kernel or other program
- Clock sends the CPU a signal periodically
- CPU checks hardware interrupts, if there's any, it calls the interrupt handler routine
- CPU executes the instruction at `IP`:
    - it reads the byte at `IP` and decodes it into an instruction
    - it reads 16 bytes (`IP+1` - `IP+16`) into the operand buffer
    - it parses the operand buffer into operands (cf. [opcode structure](opcode-structure.md))
    - it executes the instruction with the operands
    - it sets `IP` to the next instruction
- Interrupt Controller collects hardware interrupts from internal devices and stores them in a FIFO (from where CPU can fetch one by one)
- Device Controller handles devices and communicates with them
- Timer sends hardware interrupts periodically based on its programming


## Source and binary

Programs can be written either directly in machine code or [assembly](assembly.md). For the latter, there's an external assembler. "External" means it doesn't run *on* Aldebaran, but on the host machine (where Aldebaran itself is running).

Typical source code looks like this:
```
add ax 0x0001 0x0002
print ax
shutdown
```

The assembler converts it into binary machine code and creates an executable file that Aldebaran can load and run.

The executable has a header:

- bytes 0-6: signature (`0A 4C DE BA 52 0A 4E` where `4C`, `52` and `4E` are ASCII 'L', 'R' and 'N', so the signature reads 'ALDEBARAN')
- byte 7: version of the executable format (currently only version 1 is supported: `01`)
- bytes 8-9: entry point (offset from beginning of file to opcode, for version 1 it's always 10: `00 0A`, because it has no extra header)
- optional extra header (version 1 has no extra header)

After the header comes the opcode (machine code) for the program. For the above source code it looks like this:
```
10 A0 80 00 01 80 00 02 04 A0 03
```

Which could be disassembled like this:

- `10`: instruction ADD
- `A0`: word register AX
- `80 00 01`: word literal 0x0001
- `80 00 02`: word literal 0x0002
- `04`: instruction PRINT
- `A0`: word register AX
- `03`: instruction SHUTDOWN


## Devices

### Input scenario

1. Device sends data to Device Controller
2. Device Controller puts it into the targeted IOPort's input queue and calls an `ioport_in` interrupt
3. CPU calls the specified interrupt handler routine
4. The routine uses the `IN` instruction to read an item from the input queue into RAM

### Output scenario

1. The `OUT` instruction sends a piece of RAM to an IOPort
2. IOPort asks Device Controller to send the data to the device
3. Device Controller sends the data to the device

### Registering/unregistering devices

1. Device sends register/unregister command to Device Controller
2. Device Controller registers/unregisters the device with the specified IOPort
3. Device Controller registers/unregisters the device into the Device Registry
4. Device Controller calls the `device_registered` or `device_unregistered` interrupt
5. CPU calls the specified interrupt handler routine
