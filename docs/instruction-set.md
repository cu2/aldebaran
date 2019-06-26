# Instruction set

NOTE 1: this documentation is far from finished.

NOTE 2: the instruction set is even further.


## Misc

### NOP
No operation

### HLT
Halt CPU so it&#x27;s inactive until a hardware interrupt occurs

### SHUTDOWN
Shut down Aldebaran

### PRINT `<op0>`
Print &lt;op0&gt; as word to CPU log

### PRINTCHAR `<op0>`
Print &lt;op0&gt; as char to CPU log

### SETTMR `<op0>` `<op1>` `<op2>` `<op3>` `<op4>`
Set subtimer &lt;op0&gt; of Timer to mode=&lt;op1&gt;, speed=&lt;op2&gt;, phase=&lt;op3&gt;, interrupt_number=&lt;op4&gt;


## Arithmetic

### ADD `<op0>` `<op1>` `<op2>`
Add (unsigned): &lt;op0&gt; = &lt;op1&gt; + &lt;op2&gt;

### SUB `<op0>` `<op1>` `<op2>`
Substract (unsigned): &lt;op0&gt; = &lt;op1&gt; - &lt;op2&gt;

### MUL `<op0>` `<op1>` `<op2>`
Multiply (unsigned): &lt;op0&gt; = &lt;op1&gt; * &lt;op2&gt;

### DIV `<op0>` `<op1>` `<op2>`
Divide (unsigned): &lt;op0&gt; = &lt;op1&gt; / &lt;op2&gt;

### MOD `<op0>` `<op1>` `<op2>`
Modulo (unsigned): &lt;op0&gt; = &lt;op1&gt; % &lt;op2&gt;

### INC `<op0>` `<op1>`
Increase (unsigned): &lt;op0&gt; += &lt;op1&gt;

### DEC `<op0>` `<op1>`
Decrease (unsigned): &lt;op0&gt; -= &lt;op1&gt;

### IADD `<op0>` `<op1>` `<op2>`
Add (signed): &lt;op0&gt; = &lt;op1&gt; + &lt;op2&gt;

### ISUB `<op0>` `<op1>` `<op2>`
Substract (signed): &lt;op0&gt; = &lt;op1&gt; - &lt;op2&gt;

### IMUL `<op0>` `<op1>` `<op2>`
Multiply (signed): &lt;op0&gt; = &lt;op1&gt; * &lt;op2&gt;

### IDIV `<op0>` `<op1>` `<op2>`
Divide (signed): &lt;op0&gt; = &lt;op1&gt; / &lt;op2&gt;

### IMOD `<op0>` `<op1>` `<op2>`
Modulo (signed): &lt;op0&gt; = &lt;op1&gt; % &lt;op2&gt;

### IINC `<op0>` `<op1>`
Increase (signed): &lt;op0&gt; += &lt;op1&gt;

### IDEC `<op0>` `<op1>`
Decrease (signed): &lt;op0&gt; -= &lt;op1&gt;

### NEG `<op0>` `<op1>`
Negate: &lt;op0&gt; = -&lt;op1&gt;


## Data transfer

### MOV `<op0>` `<op1>`
Move data so that &lt;op0&gt; = &lt;op1&gt;

### PUSH `<op0>`
Push &lt;op0&gt; to stack

### POP `<op0>`
Pop &lt;op0&gt; from stack

### PUSHF
Push FLAGS to stack

### POPF
Pop FLAGS from stack

### IN `<op0>` `<op1>`
Transfer input data from IOPort &lt;op0&gt;B into memory at address &lt;op1&gt;W and set CX to its length

### OUT `<op0>` `<op1>`
Transfer output data (CX bytes) from memory at address &lt;op1&gt;W to IOPort &lt;op0&gt;B


## Control flow

### CALL `<op0>`
Call subroutine at address &lt;op0&gt;

### RET
Return from subroutine

### ENTER `<op0>` `<op1>`

Enter subroutine: set frame pointer and allocate &lt;op1&gt; bytes on stack for local variables

- &lt;op0&gt; = byte count of parameters (allocated by PUSH instructions in caller)
- &lt;op1&gt; = byte count of local variables (allocated by ENTER instruction in callee)


### LVRET
Leave subroutine and return from it: free stack allocated for local variables and parameters

### INT `<op0>`
Call interrupt &lt;op0&gt;

### IRET
Return from interrupt

### SETINT `<op0>` `<op1>`
Set IVT[&lt;op0&gt;] to &lt;op1&gt;

### STI
Enable interrupts

### CLI
Disable interrupts


## Jump

### JMP `<op0>`
Jump to &lt;op0&gt;

### JE `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; = &lt;op1&gt;

### JNE `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; != &lt;op1&gt;

### JG `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt; &lt;op1&gt; (signed)

### JGE `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt;= &lt;op1&gt; (signed)

### JL `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt; &lt;op1&gt; (signed)

### JLE `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt;= &lt;op1&gt; (signed)

### JA `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt; &lt;op1&gt; (unsigned)

### JAE `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &gt;= &lt;op1&gt; (unsigned)

### JB `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt; &lt;op1&gt; (unsigned)

### JBE `<op0>` `<op1>` `<op2>`
Jump to &lt;op2&gt; if &lt;op0&gt; &lt;= &lt;op1&gt; (unsigned)
