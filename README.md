LCT
===

Lazy Combat Tracker

A very simple log parser for EverQuest 2
That only parses DPS and has support for auido triggers.
You need espeek for the text-to-speek to use triggers.

LCT.py can be placed and run from anywhere, it will place its extra files in ~/LCT/
(except for LCT.log witch is placed in your home directory)

LCT downloads it's Tray icons from my server. If you fork LCT please have your version not do this.

You point it at the right directory (Server name) that contains the log files.
When you click start it will open the logfile that has been most recently modifyed
and scan through it to the end to find your current zone. (Witch has no function at all atm. And can take a very long time if your log file is large. So I advice to delete/move them every now and then.)
It will place a small icon in the "tray" that will be white when its not parsing any file at all.
Green when it's parsing but no fight is going on with selected people. And Red when a fight is in progress.

As it starts it only parses the owner. you can add your whole group by typing /whogroup
in game while in the Green stage.
Or by adding individual names with /lct addpc [name]
It dose not remember the list of names to parse between runs.

It the time parsed is allways between first hit by someone in list to last hit by someone in list.
It ends automaticly after a few seconds of noone doing any damage.
It can also be ended manually with /lct stopdps

There is atm. One hardcoded trigger for "weekness" (Ranger/Assasin ability)
It may very well crash LCT if you do not have espeek and this triggers.

To add custom triggers use: /lct trigger [string to trigger on]=[text to espeek]
the added triggers only scan group chat atm.

As you can see this parser has a lot of short commings. And maybe a few bugs.
I have no plan to actually fix these in this release but Im rather planing a total rewrite of the parser.
If I ever get to it. I will post it here as LCT2 or something :)

This program is ONLY designed to run on a Linux distribution.
Not sure if it will run on Mac. Windows users and anyone else who want a propper parser is adviced to use ACT.
