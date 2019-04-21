# Instruction set


## Arithmetic

### `ADD <op0> <op1> <op2>`
Add: &lt;op0&gt; = &lt;op1&gt; + &lt;op2&gt;

### `DEC <op0> <op1>`
Decrease: &lt;op0&gt; -= &lt;op1&gt;

### `DIV <op0> <op1> <op2>`
Divide (unsigned): &lt;op0&gt; = &lt;op1&gt; / &lt;op2&gt;

### `IDIV <op0> <op1> <op2>`
Divide (signed): &lt;op0&gt; = &lt;op1&gt; / &lt;op2&gt;

### `IMOD <op0> <op1> <op2>`
Modulo (signed): &lt;op0&gt; = &lt;op1&gt; % &lt;op2&gt;

### `IMUL <op0> <op1> <op2>`
Multiply (signed): &lt;op0&gt; = &lt;op1&gt; * &lt;op2&gt;

### `INC <op0> <op1>`
Increase: &lt;op0&gt; += &lt;op1&gt;

### `MOD <op0> <op1> <op2>`
Modulo (unsigned): &lt;op0&gt; = &lt;op1&gt; % &lt;op2&gt;

### `MUL <op0> <op1> <op2>`
Multiply (unsigned): &lt;op0&gt; = &lt;op1&gt; * &lt;op2&gt;

### `NEG <op0> <op1>`
Negate: &lt;op0&gt; = -&lt;op1&gt;

### `SUB <op0> <op1> <op2>`
Substract: &lt;op0&gt; = &lt;op1&gt; - &lt;op2&gt;


## Control flow

### `CALL <op0>`
Call subroutine at address &lt;op0&gt;

### `CLI`
Disable interrupts

### `ENTER <op0>`
Enter subroutine: set frame pointer and allocate &lt;op0&gt; bytes on stack for local variables

### `INT <op0>`
Call interrupt &lt;op0&gt;

### `IRET`
Return from interrupt

### `JA <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt; &lt;op1&gt; (unsigned)

### `JAE <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt;= &lt;op1&gt; (unsigned)

### `JB <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt; &lt;op1&gt; (unsigned)

### `JBE <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt;= &lt;op1&gt; (unsigned)

### `JE <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; = &lt;op1&gt;

### `JGE <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt;= &lt;op1&gt; (signed)

### `JGT <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt; &lt;op1&gt; (signed)

### `JLE <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt;= &lt;op1&gt; (signed)

### `JLT <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt; &lt;op1&gt; (signed)

### `JMP <op0>`
Jump to &lt;op0&gt;

### `JNE <op0> <op1> <op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; != &lt;op1&gt;

### `JNZ <op0> <op1>`
Jump to &lt;op1&gt; if &lt;op0&gt; is non-zero

### `JZ <op0> <op1>`
Jump to &lt;op1&gt; if &lt;op0&gt; is zero

### `LEAVE`
Leave subroutine: free stack allocated for local variables

### `RET`
Return from subroutine

### `RETPOP <op0>`
Return from subroutine and pop &lt;op0&gt; bytes

### `SETINT <op0> <op1>`
Set IVT[&lt;op0&gt;] to &lt;op1&gt;

### `STI`
Enable interrupts


## Data transfer

### `IN <op0> <op1>`
Transfer input data from IOPort &lt;op0&gt;B into memory at address &lt;op1&gt;W, set CX to its length and send ACK

### `MOV <op0> <op1>`
Move data so that &lt;op0&gt; = &lt;op1&gt;

### `OUT <op0> <op1>`
Transfer output data (CX bytes) from memory at address &lt;op1&gt;W to IOPort &lt;op0&gt;B

### `POP <op0>`
Pop &lt;op0&gt; from stack

### `POPF`
Pop FLAGS from stack

### `PUSH <op0>`
Push &lt;op0&gt; to stack

### `PUSHF`
Push FLAGS to stack


## Misc

### `HLT`
Halt CPU so it's inactive until a hardware interrupt occurs

### `NOP`
No operation

### `PRINT <op0>`
Print &lt;op0&gt; as word to CPU log

### `PRINTCHAR <op0>`
Print &lt;op0&gt; as char to CPU log

### `SETTMR <op0> <op1> <op2> <op3> <op4>`
Set subtimer &lt;op0&gt; of Timer to mode=&lt;op1&gt;, speed=&lt;op2&gt;, phase=&lt;op3&gt;, interrupt_number=&lt;op4&gt;

### `SHUTDOWN`
Shut down Aldebaran
