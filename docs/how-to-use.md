# How to use


## Quickly

Assemble source code to executable:
```
./asm software/hello.ald
```

Run executable:
```
./ald software/hello
```


## More details

Assemble source code to executable with verbose output:
```
./asm -v software/hello.ald
```


## Devices

Run the chat example program:
```
./asm software/chat.ald
./ald software/chat
```

Now Aldebaran will wait for terminal devices to connect.

In two other terminal windows, run two terminals:

```
./dev terminal 0
```

```
./dev terminal 1
```

They will connect to Aldebaran's IOPort 0 and 1.

Now you can chat with yourself.
