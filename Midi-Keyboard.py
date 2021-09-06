import pygame
import pygame.midi
import time # needed to add a time delay to avoid crazy cpu usage
import ctypes # needed to send the keyboard command
#import sys  # Used to flush output when testing

# These are other methods I attempted but pygame (MAS) did not register the keypresses.
#from pyautogui import press
#from pynput.keyboard import Controller
#from pykeyboard.mac import Pykeyboard  # outdated, required far too many other installs, never even got this library imported


#=========================================================================
# Code for simulating keypresses in windows using scancodes via the ctypes library.
# Taken from https://stackoverflow.com/questions/14489013/simulate-python-keypresses-for-controlling-a-game


SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions 
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Actuals Functions

def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

#===================================================================

# Map midi codes to scan codes.
# Can find scancodes at http://www.philipstorr.id.au/pcbook/book3/scancode.htm

# Midi codes found by printing the midi event and looking at the "data1" field.
# Midi events have the following fields:
    # Status: unsure what this number represents, probably the type of midi event
    # data1: the note played
    # data2: the velocity of the played note, 0 means the note was released
    # data3: no clue, always reads 0 for me
    # timestamp: when the event was recieved
    # vice_id: maybe the input_id?

def midi2scancode(midicode):
    codes = {
        65 : 0x10,      # F3 : Q
        66 : 0x03,      # F# : 2
        67 : 0x11,      # G3 : W
        68 : 0x04,      # G# : 3
        69 : 0x12,      # A3 : E
        70 : 0x05,      # A# : 4
        71 : 0x13,      # B3 : R
        72 : 0x14,      # C4 : T
        73 : 0x07,      # C# : 6
        74 : 0x15,      # D4 : Y
        75 : 0x08,      # D# : 7
        76 : 0x16,      # E4 : U
        77 : 0x17,      # F4 : I
        78 : 0x0A,      # F# : 9
        79 : 0x18,      # G4 : O
        80 : 0x0B,      # G# : 0
        81 : 0x19,      # A4 : P
        82 : 0x0C,      # A# : -
        83 : 0x1A,      # B4 : [
        84 : 0x1B       # C5 : ]
    }
    return codes.get(midicode, None)

#===================================================================
# Connect to default midi device and continuously poll incoming midi events
# Any that match the above midicodes trigger a keypress event using scancodes

def main():
    pygame.init()
    pygame.fastevent.init()
    pygame.midi.init()

    # Connect to the default midi device
    input_id = pygame.midi.get_default_input_id()
    print("Using input_id: %s" %input_id)
    i = pygame.midi.Input(input_id)

    pygame.display.set_mode((1,1))

    going = True
    while going:
        events = pygame.fastevent.get()
        for e in events:
            if e.type in [pygame.QUIT]: # If the pygame window is closed exit the loop
                going = False
            elif e.type in [pygame.KEYDOWN]:  # If a key is pressed while pygame is the active window exit the loop
                going = False
            elif e.type in [pygame.midi.MIDIIN]:
                if(e.data2 != 0): # midi key pressed, start pressing the keyboard key
                    #print(e) # Testing, print the full event details
                    #sys.stdout.flush()
                    scancode = midi2scancode(e.data1)
                    if scancode != None:
                        PressKey(scancode)
                elif(e.data1 != 0): # midi key released (since pressed is already handled), release the keyboard key
                    scancode = midi2scancode(e.data1)
                    if scancode != None:
                        ReleaseKey(scancode)


        # The poll command will continue reading empty commands continuously,
        # so add a small time delay to avoid using crazy amount of cpu
        time.sleep(0.001)
        if i.poll():
            midi_events = i.read(10)
            midi_evs = pygame.midi.midis2events(midi_events, i.device_id)
            for m_e in midi_evs:
                pygame.fastevent.post(m_e)
    del i
    pygame.midi.quit()

if __name__ == "__main__":
    main()