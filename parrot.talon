app: sm64
mode: user.single_application
-

kappa:
    user.press_start()

reset:
    user.reset_state()

camera:
    user.camera_toggle()

parrot(kk):
    user.joystick_forward()

parrot(wa):
    user.single_jump()

parrot(pop):
    user.toggle_sustain()

parrot(cluck):
    user.march_fast()

parrot(cluck_low):
    user.march_slow()

parrot(shh):
    user.joystick_cw()
parrot(shh:repeat):
    user.joystick_cw()

parrot(sss):
    user.joystick_ccw()
parrot(sss:repeat):
    user.joystick_ccw()

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