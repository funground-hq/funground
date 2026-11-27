# Project 12: A cardboard puppet that copies you (servos)

Raise your left arm. A cardboard puppet raises its left arm too. The camera sees you, funground measures the angle at each shoulder, and a small board turns two motors.

> **Not yet run on real hardware.** The two programs were checked against stand-ins: a pretend serial port and a pretend board. Expect to adjust them at the bench.
>
> **Desktop only.** This does not work in Play. The browser cannot reach a USB serial port from a sketch.

This is a guide page, not a gallery example. Funground has no hardware commands. The link to the board uses a separate library called **pyserial**. You install it yourself. It is not part of funground.

You need the models library as well. See [20. Models](../20_models.md) for the install lines.

## What you need

| Part | Notes |
|---|---|
| ESP32 development board | Any common board with a USB socket |
| 2 micro servo motors | The small SG90 type is enough for cardboard arms |
| 5 volt supply for the servos | A 4 x AA battery holder, or a 5 V 2 A adapter |
| Jumper wires and a breadboard | |
| Stiff cardboard, glue, a craft knife | For the puppet. Ask a grown-up to help with the knife |
| A USB data cable | Some cables only charge and carry no data |

## The wiring

Each servo has three wires. On an SG90 they are brown for ground, red for power and orange for signal.

- **Signal:** the left arm servo to pin 18 of the ESP32. The right arm servo to pin 19.
- **Power:** both red wires to the plus of the 5 V supply.
- **Ground:** both brown wires to the minus of the 5 V supply. Join that minus to a GND pin on the ESP32 too.

The shared ground is the connection people forget. Without it the servos twitch or ignore the signal.

**Why a separate supply?** A servo takes a short burst of current each time it starts to move. If it takes that from the ESP32's own pins, the board can restart. **Never connect a servo's red wire to the 3.3 V pin.**

## The puppet

1. Cut a body from cardboard, about 20 cm tall, with a head.
2. Glue the two servos to the back, one behind each shoulder. The shafts poke through holes to the front.
3. Cut two arms. Glue each to a servo horn. The horn is the small plastic arm that pushes onto the shaft.
4. Do not press the horns on yet. First run the board program below. It sets both servos to their middle, 90 degrees. Then push each horn on with the arm pointing straight out sideways.

## The program on the board

Install MicroPython on the ESP32. Then copy this file to it as `main.py`. The free Thonny editor does both. It has a menu entry for installing MicroPython and can save a file straight to the board.

This runs on the board, not on your computer.

```py
import sys
from machine import Pin, PWM

PINS = [18, 19]                                # signal wires: left arm servo, right arm servo
servos = [PWM(Pin(pin), freq=50) for pin in PINS]


def turn(servo, degrees):
    """Point a servo at an angle from 0 to 180 degrees."""
    degrees = max(0, min(180, degrees))
    pulse_ms = 0.5 + degrees / 180 * 1.9       # 0.5 ms is one end of the sweep, 2.4 ms the other
    servo.duty_u16(int(pulse_ms / 20 * 65535))


for servo in servos:
    turn(servo, 90)

while True:
    line = sys.stdin.readline().strip()
    try:
        angles = [int(part) for part in line.split(",")]
    except ValueError:
        continue                               # not numbers: ignore the line
    for servo, degrees in zip(servos, angles):
        turn(servo, degrees)
```

**How it works.**

- A servo is told its angle by the length of a pulse. Fifty times a second the board sends a short pulse on the signal wire. A pulse of about 0.5 milliseconds means one end of the sweep. About 2.4 milliseconds means the other end.
- `PWM(Pin(pin), freq=50)` starts those 50 pulses a second on a pin.
- `turn` changes degrees into a pulse length. Each pulse slot is 20 milliseconds long. `duty_u16` wants the pulse as a share of that slot, on a scale of 0 to 65535. That is the last line of `turn`.
- `max(0, min(180, degrees))` keeps the angle inside the range the servo can reach.
- The loop waits for a line of text from the USB cable, such as `45,135`. It splits the line at the comma and turns each servo. A line that is not numbers is skipped.

## The sketch on the computer

> **Since 0.2.** In Play now; on your computer with funground 0.2.

Install the serial library once. This is your own install, so type it yourself in a terminal:

```
python -m pip install pyserial
```

Save a photo of a person as `person.jpg` next to the sketch. The sketch uses it when there is no camera, so you can test the measuring without any hardware.

```py
import funground as f
from funground import camera, ml
import serial                                  # from the pyserial package

PORT = "COM5"                                  # Windows: COM5 or similar. Linux: /dev/ttyUSB0. Mac: /dev/tty.usbserial-...

photo = f.load_image("person.jpg")             # used when there is no camera
cam = None
link = None
last_sent = 0


def setup():
    global cam, link
    f.size(640, 480)
    try:
        link = serial.Serial(PORT, 115200)
    except serial.SerialException:
        link = None
    try:
        cam = camera.open()
        cam.start(640, 480)
    except RuntimeError:
        cam = None


def angle_at(a, b, c):
    """The angle at b, between the line to a and the line to c: 0 to 180 degrees."""
    return abs((a - b).angle_between(c - b))


def draw():
    global last_sent
    source = cam if cam is not None and cam.is_ready() else photo
    f.background("black")
    f.image(source, 0, 0)
    body = ml.pose(source)
    if body is None:
        return
    left = round(angle_at(body.left_hip, body.left_shoulder, body.left_elbow))
    right = round(angle_at(body.right_hip, body.right_shoulder, body.right_elbow))
    if link and f.millis() - last_sent > 100:
        link.write((str(left) + "," + str(180 - right) + "\n").encode())
        last_sent = f.millis()
    f.fill("white")
    f.text_size(24)
    f.text("left arm " + str(left) + "   right arm " + str(right), 20, 16)
    if link is None:
        f.text("No board found on " + PORT, 20, 50)


f.run(fps=24)
```

**How it works.**

- `angle_at(hip, shoulder, elbow)` is the angle at the shoulder between your side and your upper arm. An arm hanging down gives about 15. An arm straight out gives 90. An arm straight up gives about 170. That range suits a servo, which turns from 0 to 180.
- The right servo is mounted as a mirror image of the left. So it receives `180 - right`.
- Ten messages a second is enough. `f.millis() - last_sent > 100` lets a message through only when a tenth of a second has passed. A servo cannot follow 24 commands a second, and a flood of messages makes it shake.
- `.encode()` turns the text into bytes, which is what a serial cable carries. The `"\n"` at the end marks the end of the line for the board's `readline`.
- With no board connected, the sketch still runs and shows the two angles. You can test the measuring part alone.

## Running it

1. Close Thonny. Only one program can use the serial port at a time.
2. Find the port name. On Windows it is in Device Manager under Ports. Put it in `PORT`.
3. Switch on the servo supply, then run the sketch.
4. Wait two seconds. Opening the port restarts most ESP32 boards, and they need a moment to start `main.py`.
5. Raise one arm slowly.

## If it does not work

| What you see | Likely cause |
|---|---|
| "No board found" | Wrong port name, Thonny still open, or a charge-only cable |
| Servos twitch or do nothing | The ground of the servo supply is not joined to the ESP32's GND |
| The board restarts when an arm moves | The servos are powered from the board. Use the separate supply |
| An arm moves the wrong way | Change `str(left)` to `str(180 - left)`, or the same for the right |
| An arm hits its limit and buzzes | That servo's sweep is narrower. Change `1.9` to `1.7` in `turn` |
| No body is found | Step back so the camera sees you from head to foot, and add light |
| The puppet shakes | Lower the frame rate, or send fewer messages (change `100` to `200`) |

## Going further

- Add elbows with two more servos on pins 21 and 22, mounted on the upper arms. Add both elbow angles to the message, so it carries four numbers. Add the two pins to `PINS`. The board program needs no other change, because it turns as many servos as it receives numbers for.
- Use a recorded list of angles instead of the camera, so the puppet dances with no camera at all.

## See also

- Guide: [Models](../20_models.md), for `ml.pose` and the body points.
- Gallery: [Show the numbers](../../gallery/README.md#show-the-numbers), which measures angles the same way.
