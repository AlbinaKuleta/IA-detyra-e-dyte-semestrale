"""
Enigmat Killer Sudoku, te gjeneruara me generator.py dhe te kontrolluara qe
kane saktesisht nje zgjidhje.

Formati: 9 rreshta me 9 simbole (qelizat me te njejtin simbol jane ne te njejtin
kafaz), pastaj shumat e kafazeve ne formen simboli=shuma.

Nivelet ndryshojne sipas madhesise se kafazeve: sa me te medhenj kafazet, aq me
shume kombinime numrash ka secili dhe aq me pak informacion jep.
"""

import os

from killer_sudoku import parse_map

PUZZLES = {
    "easy-1": """
nnEEERRTC
mmQvvpwwC
rUFbbkwLS
xuucckHdd
iiaahhqqq
JgaKoDeee
GgNooBOsI
GgPMttssA
jllyzzfAA
a=20 b=7 c=4 d=14 e=16 f=6 g=10 h=16 i=12 j=2 k=5 l=12 m=6 n=14 o=14 p=7 q=6
r=7 s=14 t=13 u=9 v=14 w=16 x=5 y=9 z=4 A=13 B=6 C=16 D=2 E=14 F=5 G=10 H=9
I=5 J=3 K=6 L=6 M=7 N=8 O=7 P=4 Q=1 R=9 S=2 T=1 U=9
""",
    "easy-2": """
zaljTQWNg
aalXCmwUg
tYVpSMuUU
ttxfSouKe
cExGsJbbb
ciiGsJhhA
BikPHHqhA
ByOrLnZFA
ddIIIRvvD
a=20 b=19 c=10 d=7 e=7 f=8 g=9 h=9 i=21 j=6 k=8 l=12 m=1 n=6 o=5 p=5 q=5 r=9
s=9 t=13 u=11 v=16 w=6 x=7 y=3 z=2 A=12 B=16 C=4 D=6 E=1 F=4 G=9 H=9 I=13
J=13 K=6 L=5 M=8 N=8 O=1 P=4 Q=7 R=3 S=3 T=9 U=14 V=6 W=1 X=3 Y=4 Z=2
""",
    "medium-1": """
onBBBGFFy
nnBbqqqFy
tCCbbkkss
tCaccwwsd
iiaachhhd
llazzAAee
HggEpppee
jrgvvvuuD
jrmmvffxx
a=22 b=15 c=11 d=9 e=25 f=9 g=15 h=12 i=12 j=11 k=9 l=4 m=16 n=14 o=6 p=15
q=16 r=11 s=16 t=12 u=5 v=21 w=13 x=12 y=16 z=14 A=7 B=15 C=21 D=1 E=4 F=10
G=5 H=1
""",
    "medium-2": """
nnuuIKptt
nhhuIJppp
EFAjjaavv
yDmddbwss
yymzfbccx
ymmzfkkcr
lllziiCcr
qqggiioee
qBBggooGH
a=15 b=17 c=21 d=7 e=8 f=7 g=28 h=8 i=12 j=8 k=9 l=17 m=19 n=14 o=17 p=26
q=14 r=13 s=15 t=5 u=16 v=5 w=1 x=7 y=22 z=11 A=2 B=10 C=6 D=4 E=7 F=8 G=3
H=2 I=16 J=4 K=1
""",
    "hard-1": """
llvvqqttt
ilbbqoott
iyybbgwww
iDccggggd
iCaaahhsd
ECfAaummd
fffnnnepx
zjjBknepx
jjkkkreex
a=26 b=16 c=3 d=13 e=19 f=21 g=25 h=10 i=24 j=17 k=22 l=16 m=12 n=20 o=10
p=12 q=20 r=3 s=2 t=26 u=2 v=5 w=16 x=14 y=14 z=9 A=6 B=7 C=5 D=7 E=3
""",
    "hard-2": """
EnFGkiqqJ
DnFGiiiIH
lnjjjaaIH
lojBBbdss
oottCbdcc
womymhdcA
wpmmmhvrr
wpgghhvee
wzuuuxfff
a=15 b=17 c=16 d=6 e=8 f=9 g=13 h=18 i=21 j=17 k=7 l=10 m=21 n=22 o=20 p=10
q=7 r=14 s=15 t=7 u=24 v=14 w=22 x=5 y=1 z=1 A=8 B=7 C=4 D=1 E=4 F=9 G=10
H=10 I=9 J=3
""",
    "expert-1": """
AAxwyfnoo
zzbwbfnnn
hsbbbffld
hcccfflld
haaaaggld
qerkagggd
iejkkgmmd
iejvutmmm
iijjjtttp
a=30 b=19 c=10 d=20 e=10 f=28 g=30 h=20 i=17 j=29 k=12 l=25 m=22 n=21 o=8
p=8 q=3 r=9 s=9 t=21 u=5 v=7 w=10 x=3 y=9 z=6 A=14
""",
    "expert-2": """
nnAzzzddd
uuBaaadhd
cttoahhhl
ccpmbbhkk
wvmmbjjjk
ssCCCjxrk
eEDCijxyy
eeegiiiqq
gggggifff
a=19 b=15 c=14 d=35 e=17 f=14 g=29 h=15 i=26 j=24 k=17 l=1 m=18 n=3 o=6 p=4
q=17 r=8 s=16 t=15 u=9 v=3 w=5 x=9 y=7 z=15 A=5 B=9 C=15 D=7 E=8
""",
}


def load(name):
    if name in PUZZLES:
        return parse_map(PUZZLES[name], name)
    with open(name, encoding="utf-8") as f:
        return parse_map(f.read(), os.path.basename(name))
