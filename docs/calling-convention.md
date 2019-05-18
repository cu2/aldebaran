# Calling convention

When writing functions in assembly, you can use any calling convention you like. But the recommended and supported way is the following.

Caller:
```
PUSH param1
PUSH param2
CALL sub
# AX (and/or BX, CX, DX) contains the return value
```

Callee:
```
ENTER 0x04 0x??  # 4 bytes for parameters, ?? bytes for local variables
# access param2 in [BP+0x07]
# access param1 in [BP+0x09]
# do stuff
# put return value in AX (and/or BX, CX, DX)
LVRET
```

So the caller pushes parameters on the stack and uses the `CALL` instruction. Once the sub has returned, the caller should expect return value in `AX` (and possibly other registers).

The callee sets up the stack frame with the `ENTER` instruction. The first operand is the number of bytes used by the parameters, the second is the number of bytes used by local variables. These two byte counts are pushed onto the stack (as bytes), then `BP` is pushed as well, then `BP` is set to `SP` and `SP` is decreased to allocate space for local variables.

This way the call stack can be easily mapped (for debugging), not to mention accessing parameters and local variables with `BP`. Parameters can be accessed via `[BP+0x07]`, `[BP+0x09]`... Local variables via `[BP-0x01]`, `[BP-0x03]`...

The stack frame for this single call looks like this:

```
address             content
=======             =======
SP                  top of stack
SP-0x01             local variable or random stuff pushed after ENTER
...                 ...
BP-0x02             ...
BP-0x01             ...
BP                  local variable
BP+0x01             BP high
BP+0x02             BP low
BP+0x03             byte count of local variables
BP+0x04             byte count of parameters
BP+0x05             IP high
BP+0x06             IP low
BP+0x07             param2 high
BP+0x08             param2 low
BP+0x09             param1 high
BP+0x0A             param1 low
---                 ---
BP+0x0B             previous frame(s)
...                 ...
```

The `LVRET` instruction destroys the stack frame, returns to the instruction after `CALL` and pops the parameters. Because byte count for parameters is stored on the stack, `LVRET` doesn't need it as an operand (as opposed to the typical `LEAVE` + `RET 0x??` combo). This way both byte counts are defined in `ENTER` at the beginning of the subroutine (kinda like a function signature).

If there are multiple nested calls, the call stack looks like this:

```
...
random stuff
local variables
BP
byte-count
IP
params
---
random stuff
local variables
BP
byte-count
IP
params
---
random stuff
local variables
BP
byte-count
IP
params
```
