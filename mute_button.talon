app: sm64
-
key(backspace:down):
    speech.disable()
    mode.disable("command")
    mode.disable("dictation")
    mode.disable("user.single_application")
    mode.enable("sleep")
    user.engine_sleep()

key(alt-backspace:down):
    speech.disable()
    mode.disable("command")
    mode.disable("dictation")
    mode.disable("user.single_application")
    mode.enable("sleep")
    user.engine_sleep()

key(backspace:up):
    speech.enable()
    mode.disable("command")
    mode.disable("sleep")
    mode.disable("dictation")
    mode.enable("user.single_application")
    user.engine_wake()

key(alt-backspace:up):
    speech.enable()
    mode.disable("command")
    mode.disable("sleep")
    mode.disable("dictation")
    mode.enable("user.single_application")
    user.engine_wake()


