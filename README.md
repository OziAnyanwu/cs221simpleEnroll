# Running Instructions for Simple Enroll:

To start Simple Enroll, run:
```
$ python3 simpleenroll.py
```
Follow the wizard's instructions word for word:
When it asks for the quarter, you must enter either :"Aut", "Win", or "Spr" (it is case sensitive)

When inputting a class, The format must be "[Department Intials][Space][class code]" e.g (CS 106A). Don't forget the space and it's also case sensitive!
The wizard will (hopefully) detect errors if you input something incorrectly.

You can also directly define an input state by modifying the bottom of simpleenroll.py. Comment the line that says "startState = simpleEnroll(bulletin)", then uncomment the following line and change it as needed.

If you've taken a WAYS class for which we haven't scraped data, just input the ways initial in lower case. E.g. if we didn't scrape MUSIC 12A for Creative Expression, and you took it, just put "ce" for the calss code. Only input ways initials that aren't taken case of by the CS core though (er, ce, ed, si, aii).


To run our baseline model, run:
```
$ python3 baseline.py
```
You will need to make modification on the last line of the baseline.py file if you wish to change the input state for the baseline
