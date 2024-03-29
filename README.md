# GT911 Touch Controller Library for Micropython

This library interfaces the GT911 touch controller with a microcontroller running Micropython

## Examples
Complete examples are in the files:
- `example_polling.py`
- `example_interrupt.py`

### Polling 

To continuously checks for touch events in a loop:


```9:20:example_polling.py
tp = gt911.GT911(sda="PB7", scl="PB6", interrupt="PB4", reset="PB3")
tp.begin(gt.Addr.ADDR1)

while True:
    points = tp.get_points()
    if points:
        print(f"Received touch events: {points}")
```



### Interrupt

The interrupt example configures an interrupt handler to respond to touch events

#### Interrupt handler setup:

```9:14:example_interrupt.py
def on_touch(_):
    points = tp.get_points()
    if points:
        print(f"Received touch events: {points}")
```

Defining the rest of the program
```17:22:example_interrupt.py
tp = gt911.GT911(sda="PB7", scl="PB6", interrupt="PB4", reset="PB3")
tp.begin(gt.Addr.ADDR1)
print("Finished initialization.")
print(f"  Screen: {tp.width}x{tp.height}")

tp.enable_interrupt(on_touch)
```
