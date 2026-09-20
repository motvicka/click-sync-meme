# putin-vote-2026 — what happens when

Source: 44.6 s, 1920x1080, 23.976 fps, 1070 frames. Times are seconds from the start of the **source** clip
(the finished meme starts at frame 140 = 5.84 s by default, so subtract 5.84 for times in the output).
Camera is locked off in both shots. He sits facing the monitor on the left; his right hand is on a black mouse.

| source time | what he does | what it is good for |
|---|---|---|
| 0.0 – 5.7 | loud Russian voice-over + "Москва / 18 сентября 2026" caption; hand moves the mouse forward twice (0.6–1.5, 1.9–3.4), lifts it once (1.5–2.1) | normally cut (default start frame 140) |
| 5.7 – 7.15 | sits still, looks at the screen | establishing shot: viewer reads your fake screen |
| 7.15 – 7.60 | quick move forward-right | cursor travels onto the first target |
| **7.61** | audible press | grab / click #1 |
| 7.6 – 8.6 | three small nervous movements (7.6–7.95, 8.05–8.4, 8.45–8.75) | indecisive drag: overshoot, back, settle |
| **8.63** | audible release | drop |
| 8.84 – 9.5 | small move back towards himself | cursor goes a short way (e.g. to a button just below) |
| **9.76**, **11.11 / 11.23** | two clicks, hand does not move between them | press the same button twice |
| 11.3 – 13.0 | still | — |
| 13.0 – 14.5 | **leans right into the monitor**, right hand OFF the mouse, pointing at the screen (thump at 13.18 is the hand, not a click) | he inspects your result up close; cursor must not move |
| 14.6 – 17.1 | still leaning in, hand back on the mouse, moves it by ~1 px (15.8–17.1) | pixel-peeping nudge of a few px at most |
| 17.2 – 18.3 | sits back, open-palm gesture at the screen ("well, look at that"), hand off the mouse | reaction beat; cursor frozen |
| 18.4 – 19.4 | hand returns to the mouse (tracking unreliable until 19.0 → use `prof:'ease'`) | cursor travels to the next target |
| 19.4 – 20.15 | big move towards himself | drag far "down" … |
| 20.15 – 20.85 | most of the way back | … changes his mind, back "up" |
| 20.85 – 23.0 | slow creeping adjustment | fine positioning (`prof:'easeOut'`) |
| **23.88** | faint release | drop |
| 25.3 – 26.6 | barely perceptible drift | lazy short cursor travel |
| **27.52** | very faint click | small click (reinforce it) |
| 28.17 – 29.17 | moderate move towards himself, then creeps until 30.4 | travel to the next target, hover |
| **30.51 / 30.70** | loud clean click | select / confirm |
| 32.34 – 33.0 | **fast, large push forward-right** | the big gesture of the clip |
| 33.2 – 33.95 | pulls about half of it back | overshoot correction — reads as "oops, too far" |
| 34.0 – 34.9 | small drift | — |
| **34.96 / 35.09** | loud clean click | **final action** |
| 35.1 – 36.8 | looks at the screen, tiny drift | viewer sees the finished state for ~2 s |
| **36.9 – 39.5** | lifts both hands, spreads them, satisfied smile | the "done!" moment — the screen must already be in its final state |
| 39.5 – 42.0 | closes his folder, smiling | — |
| 42.04 – 44.6 | **cut to over-the-shoulder shot: the real monitor is in frame**, he smiles at it and stands up | `make_patches.py` puts your final screen onto that monitor |

Direction hints (loose — nobody can read direction from this camera angle, timing is what sells it):
hand moving left in the picture = mouse pushed forward = cursor up; hand moving up in the picture = mouse to his right = cursor right.
Picture-x movement is the larger, more visible component.

Fun fact the template uses: the real monitor showed an "Activate Windows" watermark (unlicensed Windows on a Dell),
which is why the fake desktop has one too.
