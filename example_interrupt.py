import micropython

import gt911
import gt911_constants as gt

micropython.alloc_emergency_exception_buf(100)


def on_touch(_):
    points = tp.get_points()
    if points:
        print("Received touch events:")
        for i, point in enumerate(points):
            print(f"  Touch {i+1}: {point.x}, {point.y}, size: {point.size}")


tp = gt911.GT911(sda="PB7", scl="PB6", interrupt="PB4", reset="PB3")
tp.begin(gt.Addr.ADDR1)
print("Finished initialization.")
print(f"  Screen: {tp.width}x{tp.height}")

tp.enable_interrupt(on_touch)
