# Super Mario 64 with Talon

These are the files I'm using for playing SM64 with [Talon](talonvoice.com) and [Parrot](github.com/chaosparrot/parrot.py) (using the Talon parrot_integration.py script circa September 2022).

Unfortunately, this is not a "plug and play" situation. What I can say is that this folder is plopped into my talon `user` file. I'm using vanilla [Talon HUD](github.com/chaosparrot/talon_hud) and a stripped down version of the [knausj85 community talon](github.com/knausj85/knausj85_talon). The only _addition_ I made to the repo (besides a lot of subtraction) was adding a `single_application` mode in `knausj85_talon/modes/modes.py` and added a command "game mode" that turns switches to `single_application` mode while turning off other modes like command mode.

I installed a third party module [vgamepad](github.com/yannbouteiller/vgamepad), which I'm finding works great. This way I can map voice commands to a virtual gamepad, rather than playing with keyboard inputs, which are inferior due to a lack of analog control. This was installed via

```
cd %appdata%\talon\.venv\scripts
pip install vgamepad
```
