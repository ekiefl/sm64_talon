app: sm64
mode: user.single_application
-

chatty:
    user.toggle_chat_hack()

kappa:
    user.press_start("kappa")

outy:
    user.camera_out("outy")

inny:
    user.camera_in("inny")

lefty:
    user.camera_left("lefty")

righty:
    user.camera_right("righty")

reset:
    user.reset_state("reset")

camera:
    user.camera_toggle("camera")

parrot(kk):
    user.joystick_forward("kk")

parrot(wa):
    user.single_jump("wa")

parrot(hoo):
    user.single_jump("hoo")

parrot(ho):
    user.punch("ho")

parrot(yuh):
    user.ground_pound("ya")

parrot(tut):
    user.joystick_invert("tut")

parrot(cluck):
    user.march_fast("cluck")

parrot(cluck_low):
    user.march_slow("clook")

parrot(shh):
    user.joystick_cw("shush")
parrot(shh:repeat):
    user.joystick_cw("shush")

parrot(sss):
    user.joystick_ccw("hiss")
parrot(sss:repeat):
    user.joystick_ccw("hiss")

parrot(whis_hi):
    user.noise_debounce("whis_hi", 1)
parrot(whis_hi:stop):
    user.noise_debounce("whis_hi", 0)

parrot(whis_lo):
    user.noise_debounce("whis_lo", 1)
parrot(whis_lo:stop):
    user.noise_debounce("whis_lo", 0)

parrot(ll):
    user.noise_debounce("ll", 1)
parrot(ll:stop):
    user.noise_debounce("ll", 0)

parrot(rr):
    user.noise_debounce("rr", 1)
parrot(rr:stop):
    user.noise_debounce("rr", 0)