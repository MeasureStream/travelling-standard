# travelling-standard
The Travelling standard is a physical device used to Calibrate other sensors.
it a portable device that could be used by a operator.
this device has to be easy to use and ready on demand.
to do so it was implemented using a rasoberrypi 3b using Raspbian os Lite, so without GUI
The Application it is written in python using kiosk and qt.

## How remove the rainbow color image 
go to /boot/firmware/config.txt and append a the bottom
```
disable_splash=1
```
## How hide boot messages

modify the string of the file /boot/firmware/cmdline.txt 
```
console=tty1 root=PARTUUID=cc93a908-02 rootfstype=ext4 fsck.repair=yes rootwait cfg80211.ieee80211_regdom=IT quiet splash loglevel=0 vt.global_cursor_default=0 consoleblank=0
```

## How start the application

Create an .bash_profile file 
replace marco with the user name 

```
if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then

    exec startx /home/marco/.xinitrc -- :0 vt1 -nolisten tcp > /dev/null 2>&1

fi
```

then create a .xinitrc file 
```
#!/bin/sh
exec sudo -u marco python3 /home/marco/kiosk_qt_pyside_6.py

```
