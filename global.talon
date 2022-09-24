app: sm64
mode: user.single_application
-

settings():
    key_wait = 1.5
    #key_hold = 32
    speech.timeout = 0.06

fix please:
	key("shift:up")
	key("alt:up")
	key("ctrl:up")
	user.mouse_drag_end()