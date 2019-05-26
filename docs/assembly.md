# Assembly language

An assembly file (typically, but not necessarily with an `.ald` extension) consists of lines (separated by a `\n`).

Each line can have the following parts in this order:

- zero or more label definitions (e.g. `label:`)
- zero or one piece of "actual code":
    - either an instruction with zero or more operands (e.g. `mov ax 0x1234`)
    - or a macro with zero or more parameters (e.g. `.dat 'Hello world'`)
- zero or one comment (e.g. `# comment`)

The parts are separated by spaces and/or tabs (at least one). And the whole line can start and end with zero or more spaces and/or tabs.

Identifiers (label names) are case sensitive, instructions, macros, registers, hex literals are not. So `MOV AX 0xABCD` and `mov ax 0xabcd` are the same, but `JMP label` and `JMP LABEL` are not.


## Basic grammar

- label names start with a letter or underscore and can continue with letter, underscore or digit
- a label definition is a label name followed immediately by a colon (`:`)
- instruction names consist of letters
- macro names start with a dot (`.`) and continue with letters
- variable names start with a dollar (`$`) and continue with letters, digits, underscores and brackets `[]`
- system variable names start with two dollars (`$$`) and continue with letters, digits, underscores and brackets `[]`
- byte literals start with `0x` and continue with 2 hexadecimal digits (`0-9A-F`)
- word literals start with `0x` and continue with 4 hexadecimal digits (`0-9A-F`)
- string literals (used with macros) start with a single or double quote, continue with anything but quote and end with a quote matching the opening quote. Currently you cannot escape quotes, so if you need a string like `I can't dance`, use double quotes: `"I can't dance"`.
- comments start with a `#` and continue with anything. So it's impossible to have more comments in a line, because in `# something # other` the second `#` is part of the first (and single) comment.
- register names are predefined two-letter names ('AX', 'BX', 'CX', 'DX', 'BP', 'SP', 'SI', 'DI', 'AL', 'AH', 'BL', 'BH', 'CL', 'CH', 'DL', 'DH')
- operands can be hex (byte/word) literals, register names, addresses or references
- an address is a `^` followed by a word literal or label. When you use a label directly, the assembler interprets it as an address. So `jmp label` and `jmp ^label` are the same.
- a reference is a `[` followed by a bunch of characters (see operands below) followed by a `]` and optionally a `b` or `B`


## Labels

A label refers to a memory address. It can point to code or data. The label definition specifies where the label points to.

Here:

```
loop:
    inc ax 0x0001
    jmp loop
```

the label `loop` points to the `inc` instruction.

Here:

```
var:
    .dat 'Hello world'
```

the label `var` points to the 'H' character (`.dat` is a macro for creating "inline" data).

If the assembler finds a label definition that is never refered to, it doesn't care about it. If it finds a label reference with no label definition, it throws an error ("Unknown label reference").

The order of label definion and reference doesn't matter. You can refer to "past" and "future" labels.

When the assembler substitutes a label reference with its address, it calculates a relative address, i.e. the offset between the reference and the definition. This means that the binary code can be loaded into any memory position, label references will work the same.

In the above `loop` example, the reference in the `jmp` instruction will be substituted as `-5`, because the `inc` instructions is 5 bytes before the `jmp` instruction. So if `inc` instruction is loaded at `0x1234`, the `jmp` instruction will be at `0x1239` and it will jump 5 bytes *back* to `0x1234` (the `inc` instruction).

How the substituted address is evaluated, depends on the reference type. For more details, see operands below.


## Comments

Comments are comments. They are completely ignored.


## Variables

A variable refers to a "value". You can define variables with macros, e.g. `.CONST`:

```
.const $var 0x1234
```

After this line `$var` refers to `0x1234`, so every time the assembler sees `$var`, it substitutes it with `0x1234`. So

```
mov ax $var
```

will become:

```
mov ax 0x1234
```


## Instructions

See [Instruction set](instruction-set.md).


## Operands

The following operand types are available. For even more details, read [Opcode structure](opcode-structure.md).

### Value

A byte or word literal. It means itself. E.g. `mov ax 0x1234` will set the `AX` register's value to `0x1234`.

### Address

A `^` followed by a word literal or label name, or a label name in itself. It means the absolute address of a relative address. E.g. `jmp ^0xfffb` will jump 5 bytes back (`0xfffb` is `-5` in two's complement).

The trick here is the `jmp` uses absolute addresses. When the CPU evaluates `^0xfffb` it adds it to the current `IP`, so it gets an absolute address.

As mentioned above the assembler handles direct label references as address, so you can write `jmp label` instead of `jmp ^label`, they mean the same.

Used for targets of jump and call instructions.

### Register

A register name. It means the register (when setting) or its value (when getting). E.g. `mov ax bx` will set the `AX` register's value to the `BX` register's value.

Used for temporary variables.

### Absolute reference register

A word register name +/- a byte literal (offset) in brackets followed by an optional `B`. E.g. `[ax+0x12]` or `[dx-0x12]b`.

We take the value of the register, add or subtract the offset, treat the result as an absolute address and take the word or byte (depending on the optional `B` after the closing bracket) value of that memory position.

E.g. if `AX`'s value is `0x1234`, `[ax+0x12]` will be the word value at absolute memory position `0x1246`.

Used for parameters and local variables in functions (with the `BP` register).

### Relative reference word

A word literal or a label name in brackets followed by an optional `B`. E.g. `[0x1234]` or `[label]`.

We take the value of the word literal or the relative address (offset) of the label, treat the result as a relative address and take the word or byte value of that memory position.

E.g. if `label`'s offset is `+15` (because the label definition is 15 bytes after this instruction), `mov ch [label]b` will set `CH`'s value to the byte at the label definition (e.g. in the case of `label: .dat 0x12` it will set it to `0x12`).

Used for global variables.

### Relative reference word + byte

A word literal or a label name + a byte literal in brackets followed by an optional `B`. E.g. `[0x1234+0x56]` or `[label+0x56]`.

We take the value of the word literal or the relative address (offset) of the label, add the value of the byte literal, treat the result as a relative address and take the word or byte value of that memory position.

E.g. if `label`'s offset is `+15` (because the label definition is 15 bytes after this instruction), `mov ch [label+0x04]b` will set `CH`'s value to the byte at the label definition + 4 bytes (e.g. in the case of `label: .dat 'Hello world'` it will set it to `0x6F` which is ASCII for `o`, at the end of `Hello`).

Used for structs.

### Relative reference word + register

A word literal or a label name + a word register name in brackets followed by an optional `B`. E.g. `[0x1234+AX]` or `[label+AX]`.

We take the value of the word literal or the relative address (offset) of the label, add the value of the word register, treat the result as a relative address and take the word or byte value of that memory position.

E.g. if `label`'s offset is `+15` (because the label definition is 15 bytes after this instruction), `mov ch [label+ax]b` will set `CH`'s value to the byte at the label definition + `AX` bytes. E.g. in the case of `label: .dat 'Hello world'` it will set it to `0x48` (ASCII for `H`) if `AX` is 0, `0x65` (`e`) if `AX` is 1...

Used for arrays.


## Macros

Macros are special instructions for the assembler itself. They are preprocessed and the result is written into the opcode.

### .DAT `<param>+`

It has one or more parameters. Each can be a byte, word or string literal. The assembler simply inserts the byte value of that literal.

Examples:

`.dat 0x12 0x3456` will insert 3 bytes: `12 34 56`

`.dat 'Hello'` will insert 5 bytes: `48 65 6C 6C 6F`

String literals are encoded as UTF-8, so one character can insert more bytes.

Used for global constants or variables.

### .DATN `<repeat>` `<value>`

It has two parameters:

- repeat: a byte or word literal
- value: a byte, word or string literal

The assembler insert the byte value of `value` `repeat` times after each other.

Examples:

`.datn 0x03 'Hello'` will insert 15 bytes: `48 65 6C 6C 6F 48 65 6C 6C 6F 48 65 6C 6C 6F`

`.datn 0xff 0x00` will insert 255 `00` bytes

Used for global variables (e.g. string buffers).

### .CONST `<name>` `<value>`

It has two parameters:

- name: a variable name
- value: a byte, word or string literal

With `.CONST` you can define a variable. The assembler will substitute its value every time it finds it.

E.g. this line defines the variable `$var`:

```
.const $var 0x1234
```

After this line, every `$var` will be substituted as `0x1234`:

```
mov ax $var
.dat $var
.const $other_var $var
```

will become:

```
mov ax 0x1234
.dat 0x1234
.const $other_var 0x1234
```

Important: variables defined by `.CONST`, `.PARAM` and `.VAR` cannot be redefined, so this is invalid after the above line:

```
.const $var 0xABCD
```

### .PARAM `<name>`

Used for defining function parameters. It can only be used in a "scope": between an `ENTER` and an `LVRET` instruction. For more details, see [Calling convention](calling-convention.md).

Typical usage:

```
enter 0x04 0x00
.param $p1
.param $p2
# ...
# $p1 will be substituted with [BP+0x09]
# $p2 will be substituted with [BP+0x07]
# ...
lvret
```

For byte parameters, use `.PARAMB`:

```
enter 0x02 0x00
.paramb $p1
.paramb $p2
# ...
# $p1 will be substituted with [BP+0x08]
# $p2 will be substituted with [BP+0x07]
# ...
lvret
```

Important: variables defined by `.CONST`, `.PARAM` and `.VAR` cannot be redefined.

### .VAR `<name>` `[<default_value>]`

Used for defining local variables in functions. It can only be used in a "scope": between an `ENTER` and an `LVRET` instruction. For more details, see [Calling convention](calling-convention.md).

Typical usage:

```
enter 0x00 0x04
.var $v1
.var $v2
# ...
# $v1 will be substituted with [BP-0x01]
# $v2 will be substituted with [BP-0x03]
# ...
lvret
```

For byte variables, use `.VARB`:

```
enter 0x00 0x02
.varb $v1
.varb $v2
# ...
# $v1 will be substituted with [BP]
# $v2 will be substituted with [BP-0x01]
# ...
lvret
```

Important: variables defined by `.CONST`, `.PARAM` and `.VAR` cannot be redefined.

If `<default_value>` is given, a `MOV` instruction will be inserted:

```
enter 0x00 0x04
.var $v1 0x1234
.var $v2
# ...
lvret
```

will become:

```
enter 0x00 0x04
mov $v1 0x1234
# ...
lvret
```
