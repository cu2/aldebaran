# System config


## Interrupt numbers

- 00-3F: reserved for hardware interrupts
    - 00-1D: unused (so far)
    - 1E: device_registered (called when a device is registered)
    - 1F: device_unregistered (called when a device is unregistered)
    - 20-2F: ioport_in (called when a device sends data to an IOPort)
    - 30-3F: device_status_changed (called when a device's status changes)
- 40-7F: reserved for OS and device driver (system) interrupts
- 80-FF: free (user) interrupts


TO BE EXTENDED...
