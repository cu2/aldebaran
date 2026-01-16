# How to use the debugger?

Go to the root dir of the project, and assemble some source code to executable:

```
./asm software/hello.ald
```

Then run the executable with debugger enabled:

```
./ald -d software/hello
```

This will start Aldebaran with debugger control, which means that the Clock that drives the CPU doesn't tick periodically, but is controlled by commands from the debugger. The debugger itself can be controlled by the user via HTTP requests to http://localhost:8000, or more easily the debugger UI.

Go to the root dir of the debugger UI (hardware/debugger/frontend), and start it:

```
npm run dev
```

Now you can access the debugger UI in a browser here: http://localhost:5173/

You can step through the code by clicking the "STEP 1" button. You can see different parts of the internal state of Aldebaran:

- CPU: cycle count, halt and shutdown statuses, IP (instruction pointer)
- Next and last instructions
- Register values
- Userlog: another debugger tool, controlled directly by the CPU (to which e.g. the hello world program prints its output)
- Stack
- Memory (the first 256 bytes of it) (paging is not implemented yet)

If the program finished running (indicated by the shutdown status of the CPU), you have to stop Aldebaran by pressing Ctrl+C in the shell you are running it. If you start it again (or run another executable) in debugger mode, the debugger UI will automatically reconnect.
