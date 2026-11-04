"""What's on screen in each FAQ video, anchored to Jean's words in the cut (see plan_faq.py for the building blocks).
Same design system as the thank-you video v2."""


def faq_label(P, a):
    return ([{"w": "FAQ", "t": round(a + 0.05, 3)}], 76, 300, {"face": "hand", "accent": True})


def v0321(P):
    s, until, L, ACCU, HAND = P.s, P.until, P.L, P.ACCU, P.HAND
    # "is JeanFX legit? Am I legit? Is Yvan legit?"
    a, b = s("is jeanfx legit") - 0.1, until("what has it done")
    P.card_title(a, b, [faq_label(P, a), L("is jeanfx", a, 130, 500, "IS JEANFX"), L("legit", a, 240, 730, "LEGIT?", **ACCU)])
    # "I'm going to show you some of my students and some of my payouts... just this year"
    a, b = s("so i'm going to show") - 0.05, until("so you guys can go ahead")
    P.results_wall(a, b)
    # Topstep and FTMO on his actual screen: the payout total, then this month's FTMO reward and the overall rewards
    a, b = s("i'm a real funded") - 0.05, until("if you gather")
    P.screenrec(a, b, [(60.0, 1720, 720, 2560), (66.3, 1944, 1049, 1300), (90.9, 1720, 720, 2560), (97.8, 2064, 760, 1100),
                       (102.0, 1480, 760, 1100), (104.6, 1770, 760, 1800)])
    # "that's over $70,000 in just under 4 months, trading with FTMO and Topstep alone"
    a, b = s("if you gather") - 0.1, until("next thing we can go")
    w = P.words("$70,000", a, text="$70,000+")
    w[0].update(accent=True, underline=True, count=[0, 70, "$%d,000+"])
    P.card_title(a, b, [L("if you gather that all together", a, 84, 400, "FTMO + TOPSTEP"), (w, 230, 610, None),
                        L("in just under 4 months", a, 92, 750, **HAND)])
    P.sfx("roll10", w[0]["t"], -24)
    # Alpha Capital on his screen: the dashboard, then the certificates ($4,956)
    a, b = s("this is my alpha capital") - 0.05, s("over $12,000") - 0.1
    P.screenrec(a, b, [(147.2, 1720, 720, 2560), (153.5, 2976, 470, 1300), (161.5, 774, 1013, 1300), (164.0, 1720, 720, 3000)], leak_out=False)
    # "on the platform before that I had made over $12,000 in payouts that I never got to receive" (red)
    a, b = s("over $12,000") - 0.1, until("and if i'm to go straight")
    w = P.words("$12,000", a, text="$12,000")
    w[0].update(accent=True, underline=True, count=[0, 12, "$%d,000"])
    P.card_title(a, b, [(w, 230, 560, None), L("in payouts that i never got to receive", a, 92, 700, "that I never got to receive", **HAND)],
                 palette="red", accent_rgb=P.RED)
    P.add(type="neonline", t0=round(a, 3), t1=round(b, 3), dur=1.2, z=30, op=0.7)
    # the Discord reviews on his screen, scrolling through the students' results
    a, b = s("we go to the review") - 0.05, until("so the whole point")
    P.screenrec(a, b, [(226.0, 1720, 720, 2560), (227.5, 1400, 720, 2000), (264.5, 1720, 720, 1800), (272.0, 1400, 720, 2000),
                       (280.0, 1720, 720, 2560)])
    # "from being literally a beginner in trading all the way to the advanced level"
    a, b = s("from being literally") - 0.1, until("as long as you")
    P.card_title(a, b, [L("a beginner in trading", a, 120, 470, "BEGINNER"), L("advanced level", a, 170, 650, "ADVANCED", **ACCU)])
    P.add(type="neonline", t0=round(a + 0.2, 3), t1=round(b, 3), dur=1.4, rgb=[62, 255, 142], op=0.55, z=30,
          pts=[(-40, 980), (300, 900), (520, 940), (820, 760), (1060, 800), (1350, 560), (1560, 600), (1980, 300)])
    P.ZOOM_CUES.extend([("know that i'm actually legit", 1.1), ("we can go to alpha", 1.08), ("this is a new platform", 1.1), ("how much results", 1.1)])
    P.ZOOM_CUES.extend([("this point of this video", 1.07), ("what has it done to show", 1.1), ("help us get", "out"),
                        ("so you guys can go ahead", 1.08), ("next thing we can go", 1.08), ("as you guys can see", "out"),
                        ("so far as i told", 1.08), ("and if i'm to go straight", 1.1), ("just to show you guys how", "out"),
                        ("serious traders", 1.1), ("we are willing to show", "out"), ("as long as you are", 1.1),
                        ("inside the program", 1.08)])


def v0322(P):
    s, until, L, ACCU, HAND = P.s, P.until, P.L, P.ACCU, P.HAND
    # "will I work with Jean Yvan, or will I work with his assistant?"
    a, b = s("will i work with jean") - 0.1, until("so just to let you")
    P.card_title(a, b, [faq_label(P, a), L("will i work with jean", a, 104, 500, "WILL I WORK WITH JEAN"),
                        L("his assistant", a, 150, 670, "OR HIS ASSISTANT?", **ACCU)])
    # "you're going to be working one-on-one with me"
    a, b = s("one-on-one with me") - 0.25, until("my assistant is only")
    P.card_title(a, b, [L("one-on-one", a, 190, 560, "ONE-ON-ONE", **ACCU), L("working with me", a + 1.0, 96, 710, "with me, personally", **HAND)])
    # "my assistant is only going to be answering Q&As in the Discord community"
    a, b = s("my assistant is only") - 0.05, until("again this program runs")
    P.results_wall(a, b, P.WALL)
    # "this program runs for six months"
    a, b = s("this program runs") - 0.1, until("within these six months")
    w = P.words("six months", a, text="6 MONTHS")
    w[0].update(accent=True, count=[0, 6, "%d"])
    w[1].update(accent=True, underline=True)
    P.graphic(a, b, text_at=(960, 640))
    P.add(type="icontile", t0=round(a + 0.02, 3), t1=round(b, 3), icon="time", cx=960, cy=300, size=220, z=82)
    P.sfx("pop", a + 0.02, -17)
    P.title(a, b, [L("this program runs for", a, 84, 560, **HAND), (w, 200, 740, None)])
    # "all I need from you is to be consistent and be disciplined, keep showing up"
    a, b = s("all i need from you") - 0.1, until("that's all i need")
    P.graphic(a, b)
    P.title(a, b, [L("all i need from you", a, 92, 230, "all I need from you", **HAND)])
    P.tiles(a, b, [("consistent", "check", "CONSISTENT"), ("disciplined", "shield", "DISCIPLINED"), ("keep showing up", "chart", "SHOW UP")], y=520)
    # "let me show you how you can actually make money": results drifting past
    a, b = s("let me show you how") - 0.05, until("you guys are going to be working with me personally")
    P.results_wall(a, b)
    # "you're not going to be working with my assistant, you're going to be working with me"
    a, b = s("you're not going to be working") - 0.1, until("if not go ahead")
    w = P.words("with me", a, text="WITH ME.")
    w[1].update(accent=True, underline=True)
    w[0].update(accent=True)
    P.card_title(a, b, [L("not going to be working with my assistant", a, 92, 460, "NOT MY ASSISTANT"), (w, 190, 650, None)])
    # "go ahead and fill in the application"
    a, b = s("go ahead and fill") - 0.1, until("see you in the next")
    P.application(a, b)
    P.ZOOM_CUES.extend([("let you guys know", 1.08), ("learn how to trade and become", 1.1)])
    P.ZOOM_CUES.extend([("explaining a question", 1.07), ("a lot of you guys", "out"), ("again you guys are going", 1.08),
                        ("i'm going to be helping you", 1.1), ("within these six months", 1.07), ("become a trader", "out"),
                        ("give me six months", 1.1), ("let me change your life", "out"), ("personally", 1.1), ("me and you", "out"),
                        ("so i can clear", 1.08), ("see you in the next", 1.1)])


def v0323(P):
    s, until, L, ACCU, HAND = P.s, P.until, P.L, P.ACCU, P.HAND
    # "can you do this with a full-time job?"
    a, b = s("can you do this") - 0.1, until("so guys just so")
    P.card_title(a, b, [faq_label(P, a), L("can you do this with a", a, 100, 500, "CAN YOU DO THIS WITH A"),
                        L("full-time job", a, 160, 670, "FULL-TIME JOB?", **ACCU)])
    # "yes, you can still learn how to trade"
    a, b = s("yes you can still") - 0.1, until("while you still have")
    w = P.words("yes", a, text="YES.")
    w[0].update(accent=True, underline=True)
    P.card_title(a, b, [(w, 280, 600, None), L("you can still learn how to trade", a, 92, 750, **HAND)])
    # "there's three sessions we can trade: London session, New York session and Asia session"
    a, b = s("three sessions that we") - 0.1, until("so out of those")
    P.graphic(a, b)
    w = P.words("three sessions", a, text="3 SESSIONS")
    w[0].update(accent=True, underline=True)
    P.title(a, b, [(w, 120, 260, None)])
    P.tiles(a, b, [("london", "location", "LONDON"), ("new york", "location", "NEW YORK"), ("asia", "location", "ASIA")], y=560)
    # "I personally trade two sessions, because the Asia session I'm always not available, it's late at night"
    a, b = s("i personally trade") - 0.1, until("you guys do not have")
    w = P.words("i personally trade two sessions", a, text="I TRADE 2 SESSIONS")
    w[2].update(accent=True, underline=True)
    P.card_title(a, b, [(w, 110, 520, None), L("it's late at night", a, 92, 660, "Asia is late at night for me", **HAND)])
    # "you do not have to quit your job to actually learn how to trade"
    a, b = s("you guys do not have") - 0.1, until("you guys can still work")
    P.card_title(a, b, [L("do not have to", a, 100, 470, "YOU DON'T HAVE TO"), L("quit your job", a, 180, 650, "QUIT YOUR JOB", **ACCU)])
    # "just like I used to work a 9-to-5 while I was still learning how to trade": his own photos from back then
    a, b = s("just like i used to") - 0.1, until("so trading helped")
    P.graphic(a, b, caps=True, dark=0.4)
    P.photo("job_shirt", a, b, 700, 500, h=720, rot=-4)
    P.photo("dd_night", s("9-to-5") - 0.05, b, 1220, 500, h=720, rot=4, z=61)
    # "so trading helped me get to the next level": his results drifting past
    a, b = s("so trading helped") - 0.05, until("but other than that guys yes")
    P.results_wall(a, b)
    P.ZOOM_CUES.extend([("just so i answer", 1.07), ("the same job", 1.08)])
    P.ZOOM_CUES.extend([("so guys just so", 1.08), ("what i mean by this", "out"), ("not really as complicated", 1.1),
                        ("there's a lot of different", "out"), ("different times of the day", 1.08), ("and get profitable", 1.0),
                        ("get profitable with", 1.1), ("that's literally what it is", 1.08), ("you guys can still work", 1.1),
                        ("you can actually still work", 1.1), ("see you guys in the next", "out")])


def v0324(P):
    s, until, L, ACCU, HAND = P.s, P.until, P.L, P.ACCU, P.HAND
    # "do I need a lot of money to start trading?"
    a, b = s("do i need a lot") - 0.1, until("these are a lot")
    P.card_title(a, b, [faq_label(P, a), L("do i need a lot of", a, 100, 500, "DO I NEED A LOT OF"),
                        L("money to start trading", a, 150, 670, "MONEY TO START?", **ACCU)])
    # "do I need $10,000, $20,000, $30,000 to start trading?"
    a, b = s("do i need $10,000") - 0.1, until("you guys do not need that")
    P.card_title(a, b, [L("do i need", a, 92, 420, "DO I NEED", **HAND), L("$10,000 $20,000 $30,000", a, 150, 600, "$10K? $20K? $30K?")])
    # "you do not need that $10,000... $50,000 just to become profitable"
    a, b = s("you guys do not need that") - 0.1, until("the reason why i'm saying")
    P.card_title(a, b, [L("you guys do not need", a, 120, 470, "YOU DON'T NEED"),
                        L("$10,000 $20,000 $40,000 $50,000", a, 112, 630, "$10K $20K $30K $40K $50K", accent=True),
                        L("just to actually become profitable", a, 88, 760, "to become profitable", **HAND)], accent_rgb=P.RED)
    # "learning how to trade in 2026 is not the same as learning how to trade in 2015"
    a, b = s("learning how to trade in 2026") - 0.1, until("so 2015 was way")
    w = P.words("2026", a, text="2026")
    w[0].update(accent=True, underline=True)
    P.card_title(a, b, [(w, 240, 580, None), L("is not the same as learning how to trade in 2015", a, 96, 740, "is not 2015", **HAND)])
    # "there's a new industry called prop firms, willing to give you money to trade with"
    a, b = s("called prop firms") - 0.1, until("they're willing to fund")
    P.card_title(a, b, [L("called prop firms", a, 180, 560, "PROP FIRMS", **ACCU),
                        L("willing to give you guys money to actually trade with", a, 92, 710, "give you money to trade with", **HAND)])
    # "pay $200 to get access to over $100,000, and still get paid every single 14 days"
    a, b = s("meaning you can pay") - 0.1, until("show you guys this payout")
    w = P.words("$100,000", a, text="$100K")
    w[0].update(accent=True, underline=True, count=[0, 100, "$%dK"])
    P.card_title(a, b, [L("pay $200", a, 110, 400, "PAY $200"), L("to get access to over", a, 84, 500, "to trade", **HAND), (w, 230, 690, None),
                        L("still get paid every single 14 days", a, 88, 820, "and get paid every 14 days", **HAND)])
    P.sfx("roll10", w[0]["t"], -24)
    # "I'm showing you these payout certificates. How do you think I'm getting these payouts?"
    a, b = s("show you guys this payout") - 0.05, until("do you think i'm paying")
    P.proofs(a, b, [("crop/ftmo_26915.png", a), ("crop/topstep_19770.png", s("how do you think")), ("crop/alpha_4956.png", s("getting this payout"))],
             w=760)
    # "I only invested a fee of $500 and I managed to get a return of over $35,000"
    a, b = s("i only invested") - 0.1, until("why because")
    w = P.words("$35,000", a, text="$35,000")
    w[0].update(accent=True, underline=True, count=[0, 35, "$%d,000"])
    P.card_title(a, b, [L("i only invested a fee of $500", a, 96, 400, "I INVESTED $500"),
                        L("and i managed to get a return", a, 88, 520, "and got back over", **HAND), (w, 230, 720, None)])
    P.sfx("roll10", w[0]["t"], -24)
    # "one single $100,000 account that managed to pay me over and over again"
    a, b = s("one single") - 0.05, until("guys you do not need")
    P.proof(a, b, "crop/ftmo_account.png", w=780, label="ONE $100K ACCOUNT")
    # "all you need is a bit of an investment and discipline"
    a, b = s("all you need is a bit of an") - 0.1, until("you guys need to trust")
    P.graphic(a, b)
    P.title(a, b, [L("all you need is", a, 92, 230, "all you need is", **HAND)])
    P.tiles(a, b, [("investment", "dollar", "INVESTMENT"), ("discipline", "shield", "DISCIPLINE")], y=520)
    # "all you need is a bit of money, $100, $500 to $1,000, to invest in yourself"
    a, b = s("all you need is a bit of money") - 0.1, until("all you need is a real")
    P.card_title(a, b, [L("$100 $500 to $1,000", a, 160, 560, "$100 – $1,000", **ACCU),
                        L("to actually invest in yourself", a, 92, 710, "to invest in yourself", **HAND)])
    # "...inside the JeanFX Elite Mentorship"
    a, b = s("inside the jeanfx elite") - 0.1, until("if you've not filled")
    P.card_title(a, b, [L("inside the", a, 84, 470, "INSIDE THE"), L("jeanfx elite mentorship", a, 112, 620, "JEANFX ELITE MENTORSHIP", **ACCU)])
    # "go ahead and fill in the application"
    a, b = s("if you've not filled") - 0.05, until("if you've already filled")
    P.application(a, b)
    # "be on the lookout for a call with my team"
    a, b = s("be on the lookout") - 0.06, until("they're going to reach")
    P.phone_call(a, b, L("be on the lookout", a, 112, 720, "BE ON THE LOOKOUT"), L("for a call with my team", a, 90, 835, **HAND))
    P.ZOOM_CUES.extend([("goes around everybody", 1.07), ("lower fee", 1.08), ("access to $100,000 account", 1.1), ("i managed to trade the account", 1.08), ("you do not need over", 1.1), ("level of profitability", 1.1), ("already filled out", 1.07)])
    P.ZOOM_CUES.extend([("a lot of questions", 1.07), ("everybody asking", "out"), ("we built a system", 1.1), ("trading has got", "out"),
                        ("way harder", 1.1), ("a longer time", "out"), ("starting out how to trade in 2026", 1.08),
                        ("the reason why i'm saying this is because there's", 1.08), ("do you think i'm paying", 1.1), ("no i only", "out"),
                        ("why because", 1.1), ("guys you do not need to", 1.08), ("trust this industry", 1.1), ("invest your money", "out"),
                        ("you do not need a lot", 1.1), ("all you need is a real", 1.08), ("make sure to answer", 1.1),
                        ("see you guys inside", 1.08)])


BEATS = {"0321": v0321, "0322": v0322, "0323": v0323, "0324": v0324}
