# Opcode structure

The opcode of an instruction with its operands has the following structure:

- one byte encoding the instruction
- for each operand: one or more bytes

For example this line of assembly code:
```
ADD AX 0x0001 0x0002
```

can be assembled into this opcode:
```
00 A0 80 00 01 80 00
```

where:
- instruction: `00` = ADD
- operand 0: `A0` = word register AX
- operand 1: `80 00 01` = word literal 0x0001
- operand 2: `80 00 02` = word literal 0x0002



## Instruction opcode

Every instruction has a one byte opcode.

Based on the instruction the CPU knows, how many operands it has. E.g. MOV has 2 operands, HLT has 0, SETTMR has 5.



## Operand opbyte

Every operand starts with an opbyte:

- bit 7 (oplen): length of the operand's value
    0 = byte
    1 = word
- bits 4-6 (optype): operand type
    - 0 = value
    - 1 = address
    - 2 = register
    - 3 = absolute reference register
    - 4 = relative reference word
    - 5 = relative reference word + byte
    - 6 = relative reference word + register
    - 7 = extended
- bits 0-3 (opreg): if operand type is 2, 3 or 6, these 4 bits encode the register (otherwise it's 0)
    - 0-7: AX, BX, CX, DX, BP, SP, SI, DI (word)
    - 8-15: AL, AH, BL, BH, CL, CH, DL, DH (byte)

For some operand types, there are one or more bytes after the opbyte.



## Operand types

Most operand types that refer to memory addresses (either for control flow or memory access) use relative addresses. This is useful, because this way the binary code of a program can be loaded to any memory position without relocation (ie. recalculating label references).

The only drawback is that in some cases, when you want to access absolute addresses (e.g. system addresses, like the Device Status Table), you cannot access it directly, but you have to put the address in a register and use an absolute reference register operand.

For reference types the memory location refered to can be a byte or a word. This is encoded in bit 7 (oplen) of opbyte. In assembly if the operand ends with `]`, it refers to a word, if it ends with `]B`, it refers to a byte.


### Value

A byte or word literal: `0xdd`, `0xdddd`

Used for constants, interrupt and I/O numbers, system addresses.

Depending on oplen 1 or 2 bytes after the opbyte encode the value.

Examples:
- `0x12` is encoded as `00 12`
- `0x1234` is encoded as `80 12 34`


### Address

A relative address that must be "absolutized" (for jumps, calls): `^0xdddd`

When using a label reference (`label`), the assembler calculates the offset between the label and the reference and substitutes the result as an address.

In this example:
```
LOOP:
    INC CX 0x0001
    JMP LOOP
```
the `LOOP` operand of `JMP` will be substituted as `^0xFFFB` which means -5, because the `LOOP` label is at the same position as the beginning of `INC` which is 5 bytes before the beginning of `JMP`.

So the operand's opcode will be `90 FF FB`.

When the CPU evaluates it, it will add it the `IP`, so the result will be an absolute address. This is needed, because `JMP` (and all other jump instructions) use absolute addresses.


### Register

A byte or word register: `AL`, `AX`

Used for temporary variables.

In this case, the register is encoded in the second half of opbyte (opreg), so the operand has only one byte.

Examples:
- `AX` is encoded as `A0`
- `AL` is encoded as `28`


### Absolute reference register

An absolute address reference, where the address is either the value of a word register or the sum of the values of a word register and a signed byte literal: `[AX]`, `[AX+0xdd]`, `[AX-0xdd]`

Used for parameters (`[BP+...]`) and local variables (`[BP-...]`) in functions (with proper function perilogues). Can also be used for accessing absolute memory addresses (e.g. Device Status Table).

The byte literal offset is always encoded as an additional byte after the opbyte.

Examples:
- `[AX]` is encoded as `B0 00`
- `[BP+0x05]` is encoded as `B4 05`
- `[BP-0x01]` is encoded as `B4 FF`

Or if the refered value is byte, not word:

- `[AX]B` is encoded as `30 00`
- `[BP+0x05]B` is encoded as `34 05`
- `[BP-0x01]B` is encoded as `34 FF`


### Relative reference word

A relative address reference, where the address is signed word literal: `[0xdddd]`

When using a label reference (`[label]`), the assembler calculates the offset between the label and the reference and substitutes the result as a relative reference word.

Used for global variables.

For example in hello.ald:
```
        JLT CX [TEXT_LENGTH]B LOOP
...
TEXT_LENGTH:
        .DAT 0x0B
```

The assembler calculates the offset between `JLT` and `.DAT`, which is 20 (0x0014). So `[TEXT_LENGTH]B` will be encoded as `40 00 14`.


### Relative reference word + byte

A relative address reference, where the address is the sum of a signed word literal and an unsigned byte literal: `[0xdddd+0xdd]`

When using a label reference (`[label+0xdd]`), the assembler calculates the offset between the label and the reference and substitutes the result as a relative reference word + byte.

Used for global struct variables.

For example in pong.ald:
```
    MOV [OUTPUT_BUFFER] [BALL_X]
    MOV [OUTPUT_BUFFER+0x02] [BALL_Y]
...
    OUTPUT_BUFFER:
        .DATN 0xFF 0x00
```

The assembler calculates the offset between the `MOV`s and `.DATN`, substitutes it, so `[OUTPUT_BUFFER+0x02]` will be encoded as `D0 dd dd 02`.


### Relative reference word + register

A relative address reference, where the address is the sum of a signed word literal and a word register: `[0xdddd+AX]`, `[0xdddd+BX]`

When using a label reference (`[label+AX]`), the assembler calculates the offset between the label and the reference and substitutes the result as a relative reference word + register.

Used for global arrays.

For example in hello.ald:
```
        PRINTCHAR [TEXT+CX]B
...
TEXT:
        .DAT 'Hello world'
```

The assembler calculates the offset between `PRINTCHAR` and `.DAT`, which is 18 (0x0012). So `[TEXT+CX]B` will be encoded as `62 00 12`.


### Extended

Currently this is not implemented. If in the future there's need for more operand types, the extended type can be used, where the next byte specifies the subtype within extended.



## Overview of operand opcodes

- value:
    - byte: `00 dd`
    - word: `80 dd dd`
- address: `90 dd dd` (cannot be byte)
- register:
    - byte: `28-2F`
    - word: `A0-A7`
- absolute reference register:
    - byte: `30-37 dd`
    - word: `B0-B7 dd`
- relative reference word:
    - byte: `40 dd dd`
    - word: `C0 dd dd`
- relative reference word + byte:
    - byte: `50 dd dd dd`
    - word: `D0 dd dd dd`
- relative reference word + register:
    - byte: `60-67 dd dd`
    - word: `E0-E7 dd dd`
- extended:
    - byte: `70-7F xx ??`
    - word: `F0-FF xx ??`
