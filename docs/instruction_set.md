# Instruction set


## Arithmetic

### ADD &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Add: &lt;op0&gt; = &lt;op1&gt; + &lt;op2&gt;

### DEC &lt;op0&gt; &lt;op1&gt;
Decrease: &lt;op0&gt; -= &lt;op1&gt;

### DIV &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Divide (unsigned): &lt;op0&gt; = &lt;op1&gt; / &lt;op2&gt;

### IDIV &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Divide (signed): &lt;op0&gt; = &lt;op1&gt; / &lt;op2&gt;

### IMOD &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Modulo (signed): &lt;op0&gt; = &lt;op1&gt; % &lt;op2&gt;

### IMUL &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Multiply (signed): &lt;op0&gt; = &lt;op1&gt; * &lt;op2&gt;

### INC &lt;op0&gt; &lt;op1&gt;
Increase: &lt;op0&gt; += &lt;op1&gt;

### MOD &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Modulo (unsigned): &lt;op0&gt; = &lt;op1&gt; % &lt;op2&gt;

### MUL &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Multiply (unsigned): &lt;op0&gt; = &lt;op1&gt; * &lt;op2&gt;

### NEG &lt;op0&gt; &lt;op1&gt;
Negate: &lt;op0&gt; = -&lt;op1&gt;

### SUB &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Substract: &lt;op0&gt; = &lt;op1&gt; - &lt;op2&gt;


## Control flow

### CALL &lt;op0&gt;
Call subroutine at address &lt;op0&gt;

### CLI
Disable interrupts

### ENTER &lt;op0&gt;
Enter subroutine: set frame pointer and allocate &lt;op0&gt; bytes on stack for local variables

### INT &lt;op0&gt;
Call interrupt &lt;op0&gt;

### IRET
Return from interrupt

### JA &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &gt; &lt;op1&gt; (unsigned)

### JAE &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &gt;= &lt;op1&gt; (unsigned)

### JB &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &lt; &lt;op1&gt; (unsigned)

### JBE &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &lt;= &lt;op1&gt; (unsigned)

### JE &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; = &lt;op1&gt;

### JGE &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &gt;= &lt;op1&gt; (signed)

### JGT &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &gt; &lt;op1&gt; (signed)

### JLE &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &lt;= &lt;op1&gt; (signed)

### JLT &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; &lt; &lt;op1&gt; (signed)

### JMP &lt;op0&gt;
Jump to &lt;op0&gt;

### JNE &lt;op0&gt; &lt;op1&gt; &lt;op2&gt;
Jump to &lt;op2&gt; if &lt;op0&gt; != &lt;op1&gt;

### JNZ &lt;op0&gt; &lt;op1&gt;
Jump to &lt;op1&gt; if &lt;op0&gt; is non-zero

### JZ &lt;op0&gt; &lt;op1&gt;
Jump to &lt;op1&gt; if &lt;op0&gt; is zero

### LEAVE
Leave subroutine: free stack allocated for local variables

### RET
Return from subroutine

### RETPOP &lt;op0&gt;
Return from subroutine and pop &lt;op0&gt; bytes

### SETINT &lt;op0&gt; &lt;op1&gt;
Set IVT[&lt;op0&gt;] to &lt;op1&gt;

### STI
Enable interrupts


## Data transfer

### IN &lt;op0&gt; &lt;op1&gt;
Transfer input data from IOPort &lt;op0&gt;B into memory at address &lt;op1&gt;W, set CX to its length and send ACK

### MOV &lt;op0&gt; &lt;op1&gt;
Move data so that &lt;op0&gt; = &lt;op1&gt;

### OUT &lt;op0&gt; &lt;op1&gt;
Transfer output data (CX bytes) from memory at address &lt;op1&gt;W to IOPort &lt;op0&gt;B

### POP &lt;op0&gt;
Pop &lt;op0&gt; from stack

### POPF
Pop FLAGS from stack

### PUSH &lt;op0&gt;
Push &lt;op0&gt; to stack

### PUSHF
Push FLAGS to stack


## Misc

### HLT
Halt CPU so it&#x27;s inactive until a hardware interrupt occurs

### NOP
No operation

### PRINT &lt;op0&gt;
Print &lt;op0&gt; as word to CPU log

### PRINTCHAR &lt;op0&gt;
Print &lt;op0&gt; as char to CPU log

### SETTMR &lt;op0&gt; &lt;op1&gt; &lt;op2&gt; &lt;op3&gt; &lt;op4&gt;
Set subtimer &lt;op0&gt; of Timer to mode=&lt;op1&gt;, speed=&lt;op2&gt;, phase=&lt;op3&gt;, interrupt_number=&lt;op4&gt;

### SHUTDOWN
Shut down Aldebaran
