#!/usr/bin/env python3
"""build_v5_8.py — v5.8: Card batch (191 → 216 cards) + 2 daily questions + journal prompts + 1 SEED_TASK
Source: daddy-duty-v5_7.html -> daddy-duty-v5_8.html

Changes:
  1. Version bump v5.7 → v5.8
  2. Add 25 new LIBRARY_CARDS (n-034–n-043, t-022–t-029, s-025–s-029, f-042–f-043)
  3. Add q-022 (birth-plan milestone) and q-023 (wills milestone) to DAILY_QUESTIONS
  4. Add birth-plan and hospital-tour entries to MILESTONE_JOURNAL_PROMPTS
  5. Add paternity leave research task to SEED_TASKS
"""

import os, re, shutil, subprocess, sys
sys.stdout.reconfigure(line_buffering=True)


def load_env(path='.env'):
    env = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return env


env = load_env()
SUPABASE_URL      = env.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = env.get('SUPABASE_ANON_KEY', '')

src = open('daddy-duty-v5_7.html', encoding='utf-8').read()
print(f'Loaded source: {len(src)} chars')

# ── 1. Credentials (always regex) ─────────────────────────────────────────────
src = re.sub(r"const SUPABASE_URL\s*=\s*'[^']*'",
             f"const SUPABASE_URL      = '{SUPABASE_URL}'", src, count=1)
src = re.sub(r"const SUPABASE_ANON_KEY\s*=\s*'[^']*'",
             f"const SUPABASE_ANON_KEY = '{SUPABASE_ANON_KEY}'", src, count=1)
print('  - Credentials injected')

# ── 2. Version ─────────────────────────────────────────────────────────────────
OLD2a = "v5.7 \xb7 cloud sync"
NEW2a = "v5.8 \xb7 cloud sync"
assert OLD2a in src, "version string not found"
src = src.replace(OLD2a, NEW2a, 1)

OLD2b = "appVersion:'v5.7'"
NEW2b = "appVersion:'v5.8'"
assert OLD2b in src, "appVersion not found"
src = src.replace(OLD2b, NEW2b, 1)
print('  - Version: v5.7 → v5.8')

# ── 3. Add 25 new LIBRARY_CARDS ────────────────────────────────────────────────
# Insert immediately before the closing ]; of LIBRARY_CARDS (after n-033)
OLD3 = """   body:`The baby has arrived. You are holding them. Everything you worked toward is real. And sometimes — without warning, without apparent reason — the grief of the journey surfaces alongside the joy of where you've ended up. Research on new parenthood after fertility treatment consistently documents this experience: the arrival of the baby does not simply replace what was lost or resolve the emotional complexity of what the path cost. For intended parents who experienced prior losses, the newborn phase can carry an unexpected emotional resonance — moments of profound joy interrupted by unexpected tears, or a quiet sadness alongside the celebration that is confusing precisely because everything has finally worked out. Clinical psychologists describe this as the grief completing itself in a context of safety. The protective emotional armor built to survive the uncertainty is no longer needed, and in some parents, its dismantling releases what was held inside it. This is not pathological. It does not mean you're not grateful, or not bonded, or not happy. It means the journey was real, and you are human, and both things can be true at once.`},
];"""

NEW3 = """   body:`The baby has arrived. You are holding them. Everything you worked toward is real. And sometimes — without warning, without apparent reason — the grief of the journey surfaces alongside the joy of where you've ended up. Research on new parenthood after fertility treatment consistently documents this experience: the arrival of the baby does not simply replace what was lost or resolve the emotional complexity of what the path cost. For intended parents who experienced prior losses, the newborn phase can carry an unexpected emotional resonance — moments of profound joy interrupted by unexpected tears, or a quiet sadness alongside the celebration that is confusing precisely because everything has finally worked out. Clinical psychologists describe this as the grief completing itself in a context of safety. The protective emotional armor built to survive the uncertainty is no longer needed, and in some parents, its dismantling releases what was held inside it. This is not pathological. It does not mean you're not grateful, or not bonded, or not happy. It means the journey was real, and you are human, and both things can be true at once.`},

  // ── BATCH v5.8 — Newborn (n-034 to n-043) ──
  {id:'n-034',phase:'newborn',weekRange:null,track:'Emotional',tags:['first-time-parent'],
   title:`The bonding gap`,
   body:`Research on intended fathers shows that oxytocin synchrony — the neurochemical basis of attachment — rises not at birth but through sustained caregiving contact over the first weeks and months. Feldman et al. (2010) documented this specifically in non-birthing fathers: the bond assembles through interaction, not through a moment. Greenberg and Morris coined the term "engrossment" to describe the intense absorption new fathers feel toward their newborns, but their original research also found it uneven and variable. Approximately 30–40% of new fathers report not feeling immediate, overwhelming attachment at birth. This figure is poorly publicized — the cultural expectation of instant love means that a slower bond feels like a private failure rather than a documented norm. It is a documented norm. The bond is not something you feel — it is something you build. Holding, bathing, feeding, soothing, reading: these are not preparation for bonding. They are the bonding. If the feeling you expected hasn't arrived yet, you are not behind. You are in the middle of the process that produces it.`},
  {id:'n-035',phase:'newborn',weekRange:null,track:'Emotional',tags:['anxiety-content'],
   title:`Postpartum parental anxiety`,
   body:`Postpartum depression in fathers is documented and measurable — Paulson and Bazemore's 2010 meta-analysis in JAMA found a 10.4% prevalence rate among new fathers, highest in weeks 3–6 post-birth. But anxiety is more prevalent still and even less discussed. The specific form it takes in new fathers is hypervigilance: intrusive thoughts about the baby's safety (SIDS, falls, choking), a chronic scanning quality, difficulty fully relaxing even when the baby is fine. These thoughts are not signs of psychosis or instability. They are the threat-detection system running at a volume calibrated to a situation that feels existentially high-stakes — which it is. The clinical threshold is whether this hypervigilance disrupts sleep, function, or daily life. If it doesn't, it's a normal adaptation to a genuinely new responsibility. If it does, it's treatable postpartum anxiety — which responds well to therapy and, when warranted, medication. The most important thing is naming the difference. "I keep checking on him" is different from "I cannot stop checking on him and I haven't slept in three days." Both deserve attention. Only the second requires intervention.`},
  {id:'n-036',phase:'newborn',weekRange:null,track:'Emotional',tags:['has-partner'],
   title:`The load imbalance`,
   body:`The Gottman Institute's "Bringing Baby Home" research — one of the most rigorous longitudinal studies of couples through the transition to parenthood — found that 67% of couples experience a significant drop in relationship satisfaction in the first three years after birth. The primary driver is not love or compatibility. It is perceived unfairness in who carries the cognitive and physical load of childcare and household management. The pattern typically emerges at weeks 4–8, after the acute survival intensity of the first weeks has softened and the actual distribution of labor has become visible. The research is specific about the mechanism: it is not the amount of work that damages relationships, it is the perception that the work is distributed unequally and that the unequal distribution is not acknowledged. What this means practically: explicit conversations about the division of labor — who is responsible for what, by name, not by assumption — are more protective than any amount of goodwill. The couples who navigate the transition best are not the ones who love each other most. They are the ones who negotiated explicitly, renegotiated as needed, and acknowledged each other's contributions consistently.`},
  {id:'n-037',phase:'newborn',weekRange:null,track:'Logistics',tags:['first-time-parent'],
   title:`First 48 hours home`,
   body:`Hospital discharge is one of the most disorienting moments new parents describe — not because of the baby, but because the support infrastructure disappears. The nurse call button, the bassinet with wheels, the lactation consultant on the next floor — gone. Here is what actually happens in the first 48 hours and what makes it manageable. Car seat: inspect and install the base before discharge day; a certified technician check beforehand removes last-minute anxiety. Home temperature: the American Academy of Pediatrics recommends 68–72°F — newborns cannot regulate their own body temperature and are dressed appropriately for the room. Feeding log: start a written log on day one — time, duration or ounces, wet diapers. The weight check at day 3–5 requires this data to interpret. Visitors: hold all but essential support people for the first 48 hours. Not because of pathogens — because the first two nights are for you to find your footing. One designated adult per overnight shift: document who covers midnight to 5am and who covers 5am to 9am. Improvising at 3am under sleep deprivation is measurably worse than following a plan you made 48 hours earlier.`},
  {id:'n-038',phase:'newborn',weekRange:null,track:'Logistics',tags:['insurance'],
   title:`Adding baby to health insurance`,
   body:`Under the Affordable Care Act, the birth of a child triggers a Special Enrollment Period — typically 30 days from the date of birth to add the newborn to your health plan. Missing this window means waiting until open enrollment, which could be months away. For surrogacy-born children, documentation requirements vary by insurer and are inconsistently communicated. Some plans require the pre-birth order. Others require the birth certificate (which may not be issued for 2–4 weeks). Others require an agency letter confirming parentage. The correct approach: call your insurer before birth and ask explicitly: "What documentation do you require to add a child born via gestational surrogacy to our plan?" Get the answer in writing or document the call. Notify HR with a specific date of birth, not an estimated range — the 30-day clock starts from birth. The pediatrician visit at day 3–5 generates a bill. That bill requires active coverage at the date of service. Coverage gaps in the first weeks of a newborn's life are among the most expensive and stressful administrative problems new parents face. Solve this before the birth.`},
  {id:'n-039',phase:'newborn',weekRange:null,track:'Logistics',tags:['first-time-parent'],
   title:`Sleep progression`,
   body:`Newborn sleep is not random. It is governed by ultradian cycles (approximately 45–50 minutes per cycle in the first weeks) and by awake windows that expand predictably as the nervous system matures: week 1–2, awake windows of 45–60 minutes; week 6, 60–90 minutes; week 12, 90–120 minutes. The practical implication: watching for tired cues at the end of each awake window — yawning, eye rubbing, gaze aversion — and putting the baby down before overtiredness sets in, produces better sleep outcomes than waiting until the baby is crying. Mindell et al. (2006) found that establishing a consistent bedtime routine as early as 4–6 weeks predicted faster sleep consolidation at 3 and 6 months. The routine does not need to be long — a 10-minute sequence of bath, feed, dark room, and consistent sound (white noise, a song) is sufficient. The mechanism is Pavlovian: the sequence signals the circadian system that sleep is approaching. Newborns do not have fully developed circadian rhythms yet — external cues are what build them. A predictable sequence, applied consistently, is not a sleep training method. It is neurological calibration.`},
  {id:'n-040',phase:'newborn',weekRange:null,track:'Self',tags:['first-time-parent'],
   title:`Identity reconstruction timeline`,
   body:`Alexandra Sacks coined "matrescence" to describe the identity transformation of becoming a mother — the psychological, neurological, and relational reorganization that the transition to parenthood requires. The paternal equivalent — sometimes called "patrescence," formally documented by Singley and Edwards in 2015 — follows the same architecture on a different timeline. Research on paternal identity formation suggests the reconstruction takes 6–18 months, not days or weeks. The acute phase of new parenthood (the first 6–8 weeks) is dominated by logistics and survival. The identity disruption tends to surface later — at months 3–6, when the acute intensity has eased and you have more cognitive space to notice that you are not quite the same person you were before. Common experiences at this stage: a temporary loss of previous identity anchors (how you spent your time, your social rhythm, your sense of competence), a shift in what you care about, and a disorientation in your existing relationships. This is not regression or dysfunction. It is the integration of a new self into an existing one — a process that takes time and that is made harder by the cultural expectation that fathers simply adapt quickly and get back to their lives. You are not getting back to your life. You are building a different one.`},
  {id:'n-041',phase:'newborn',weekRange:null,track:'Self',tags:['leave-paperwork'],
   title:`Return to work`,
   body:`Nepomnyaschy and Waldfogel (2007) found that fathers who took two or more weeks of paternity leave were significantly more involved in childcare at nine months — feeding, bathing, reading, getting up at night — and that the effect persisted at 24 months. The research on why is straightforward: paternity leave creates the conditions for routinized caregiving, and routinized caregiving is what builds both competence and attachment. The return to work after leave is a separately studied experience. Guilt, distraction, and performance anxiety in the first weeks back are documented and transient — most fathers report they normalized within two to four weeks. What reduces the cognitive load on return: concrete handoff protocols agreed before the return date (who handles daycare pickup, what the feeding schedule is, what the emergency contact list looks like), a defined check-in rhythm with your partner, and explicit permission from yourself to be less efficient for a few weeks while the new routine stabilizes. The guilt about returning is real. It does not mean you made the wrong choice about the length of your leave, and it does not mean you are abandoning your child. It means you have built a bond that makes the separation uncomfortable — which is, by the research, exactly what is supposed to happen.`},
  {id:'n-042',phase:'newborn',weekRange:null,track:'Surrogacy',tags:[],
   title:`Telling your child their origin story`,
   body:`Golombok and colleagues at Cambridge have conducted some of the most rigorous longitudinal research on surrogacy-born children's psychological outcomes. Their consistent finding: children born via surrogacy who were told their origin story early — before age 4 or 5, before they were old enough to ask why — showed better psychological outcomes at age 10 than those who were told later. The mechanism is well-understood from adoption disclosure research: early disclosure normalizes the story before the child has developed a framework for it to feel unusual. Late disclosure, particularly in adolescence, is more likely to produce a sense of betrayal — not because the story is bad, but because the secrecy implied it was. The language at age 3 is simple and literal: "You grew in [name]'s belly because she helped us bring you here." That sentence, repeated matter-of-factly as part of the family story, is processed differently than it would be at age 9. Complexity — the why, the emotional texture, the full history — can come later, in layers. What cannot be undone is making the story shameful through silence. Disclosure is not a single conversation. It is an ongoing relationship with the truth, calibrated to age.`},
  {id:'n-043',phase:'newborn',weekRange:null,track:'Bonding',tags:['first-time-parent'],
   title:`Caregiving as bonding`,
   body:`Fleming et al. (2002) documented that paternal caregiving — diapering, bathing, feeding, soothing — triggers measurable changes in fathers' oxytocin and prolactin levels. These are the same hormonal pathways that birthing and nursing activate in mothers. Feldman's subsequent work on oxytocin synchrony showed that the neurochemical architecture of parent-child attachment is not fundamentally different between birthing and non-birthing parents — it is activated by contact and responsiveness, not by biological participation in birth. This has a specific implication for fathers, and for intended fathers in particular: every diaper change is a neurochemical deposit. Every bath. Every 3am feed. Every time you respond to crying and the baby quiets. The research term for this is "contingent responsiveness" — you respond, the baby responds to your response, your brain registers the exchange as meaningful, and the bond deepens. This is not metaphor. It is the actual mechanism. The practical consequence: the fathers who report the strongest early bonds are typically the ones who did the most caregiving, not the ones who felt the most in the delivery room. You build this bond with your hands and your presence, in the ordinary moments that do not feel like they count. They count most of all.`},

  // ── BATCH v5.8 — Third Trimester (t-022 to t-029) ──
  {id:'t-022',phase:'third',weekRange:[35,41],track:'Emotional',tags:['anxiety-content','prior-loss'],
   title:`Catastrophic thinking in the final weeks`,
   body:`Research on perinatal anxiety documents a specific pattern in the final weeks of pregnancy: a spike in catastrophic ideation at approximately weeks 35–38, when the outcome is close but not yet certain. Côté-Arsenault's research on pregnancy after perinatal loss describes this as the nervous system's threat-detection mechanism activating at precisely the moment when the stakes feel highest. For intended parents who have lived through prior losses or failed transfers, this spike is reliably amplified — the educated wariness of someone who has learned that proximity to success does not guarantee it. The clinical insight that applies here: behavioral interventions outperform cognitive ones for this kind of anxiety. Trying to think your way calm — telling yourself the odds are good, reviewing the data — tends to work briefly and then stop working. Structure and physical engagement work better: a daily routine that creates forward motion (walks, projects, commitments), specific tasks that channel the energy constructively, and physical exercise if medically appropriate. The anxiety is not irrational. It is adaptive hypervigilance running at the wrong intensity. The goal is not to eliminate it — you cannot and should not want to. The goal is to give it a constructive direction, so that the energy it generates does something useful rather than cycling.`},
  {id:'t-023',phase:'third',weekRange:[36,41],track:'Emotional',tags:['birth-attendance-ip'],
   title:`Being a bystander at labor`,
   body:`Surrogacy birth is one of the only scenarios in which the person with the most at stake in the outcome has the least control over the process. Research on IP birth experience — Söderström-Anttila et al. and Jadva et al. are the most cited sources — consistently identifies this as the single most commonly described psychological challenge of the delivery experience: being fully present and completely powerless at the same time. The findings on what helps are specific. First, a defined role agreed upon with your GC before labor: a physical position in the room, a specific task (photographing the first moments, cutting the cord if offered, receiving the baby for skin-to-skin), something that transforms you from observer to participant. Second, prior explicit agreements about what you are permitted to do and what you should hang back from — negotiated during the pregnancy, not improvised during active labor. Third, and perhaps most importantly: the explicit permission — from your GC, articulated beforehand, and from yourself — to simply witness. Witnessing is not the same as helplessness. It is presence at the highest intensity. The research documents that IPs who arrived at the delivery with a defined role and prior agreements consistently reported more positive birth experiences than those who arrived without them, regardless of whether the birth went as planned.`},
  {id:'t-024',phase:'third',weekRange:[38,41],track:'Emotional',tags:['birth-attendance-ip'],
   title:`The night before`,
   body:`There is no research citation adequate to this night. The research on IP birth experience captures what happens in aggregate; what happens for you tonight is particular. A birth that has been years in the making — a journey that included uncertainty and waiting and, for many intended parents, losses that preceded this — is not adequately described by clinical language. What the research on post-traumatic growth and anticipated joy does consistently document: the experience of holding both grief and gratitude simultaneously is not a sign of unresolved pathology. It is the appropriate emotional response to having arrived somewhere after a difficult journey. You are allowed to be terrified. You are allowed to feel the weight of what has led here. You are allowed to be flooded with something that doesn't have a clean name — something between grief for the journey and joy at where it ends. Whatever you feel tonight does not predict the quality of what comes tomorrow. The person who walks into that delivery room anxious and overwhelmed and uncertain is the same person who will hold their child and discover that the feeling they were looking for was there all along. Write something down tonight. Whatever it is.`},
  {id:'t-025',phase:'third',weekRange:[35,41],track:'Logistics',tags:['birth-attendance-ip','doc-folder'],
   title:`Delivery day IP checklist`,
   body:`The day of birth requires you to manage logistics under conditions of high emotion and sleep deprivation. Build the system before you need it. Documents to carry (originals or certified copies as specified by your attorney): pre-birth order, both parents' government IDs, GCA summary page, pediatrician contact, insurance card with newborn coverage details. Hospital logistics: confirm in advance whether you can be present for triage versus only active labor; confirm OR policy if a C-section becomes necessary; confirm hospital registration timing and which staff members to present the PBO to. Communication plan: decide before birth who you tell and in what order (immediate family before arriving at hospital is typical; a group text during active labor typically overwhelms); designate one person as the outbound communicator so you can be present. Phone prep: full charge the night before; decide now whether you're using a dedicated camera or your phone, and who is the backup photographer. Post-birth protocols to confirm with the OB team before labor begins: whether delayed cord clamping is requested, whether skin-to-skin immediately after birth has been communicated, and which parent receives the baby first. Build this as a literal checklist on your phone. Check it the day before birth.`},
  {id:'t-026',phase:'third',weekRange:[32,38],track:'Logistics',tags:['first-time-parent'],
   title:`Stocking the house`,
   body:`The week you bring a newborn home is not the time to figure out what you need. Concrete quantities for the first four weeks: diapers (newborn size for the first 1–2 weeks: 8–12 per day, stock approximately 60–80; move to size 1 at roughly 10 lbs, 8–10 per day); wipes (5–6 packs of 72-count); onesies (6–8 in newborn, 8–10 in 0–3 month — babies grow faster than the labels suggest); formula if using (a 7-pound baby consumes approximately 1 oz per feeding, 8 feedings per day, equating to roughly 56 oz per week — build to tolerance); burp cloths (8–10 minimum, laundry is relentless); swaddle blankets (4–6). Sleep surface: the American Academy of Pediatrics recommends a firm, flat surface in your room for at least the first 6 months — the bassinet should be in your bedroom, assembled and ready, before birth. The crib in the nursery comes later. Medicine cabinet essentials to stock before birth: saline nasal drops, a nasal aspirator, a rectal thermometer, and simethicone gas drops. You will not be in the mood to order these at 2am.`},
  {id:'t-027',phase:'third',weekRange:[28,36],track:'Self',tags:['leave-paperwork'],
   title:`Paternity leave architecture`,
   body:`Nepomnyaschy and Waldfogel's research established that fathers who took two or more weeks of paternity leave showed measurably higher involvement in childcare at nine months — and that the effect persisted at 24 months. How you structure your leave matters as much as how much you take. Front-loading — taking all of it consecutively beginning at birth — maximizes bonding density in the most neurologically critical window and ensures you are present for the first pediatrician visit, the first weeks of feeding, and the first sleep regression. The potential downside: it can leave you without coverage at weeks 6–8, when initial family support has typically departed and the cumulative sleep deficit is at its worst. Split leave — two weeks at birth, then two weeks at weeks 6–8 — addresses this. If your state has paid family leave (CA, NY, NJ, WA, CO, CT, OR, MA, MD, RI, HI, DE — confirm current law as policies change), it may run concurrently with federal FMLA by default. In some states, you can exhaust company leave first and then draw state benefits sequentially. This is not a small question — the answer can add two to four weeks of paid coverage. Ask HR explicitly: "Do state paid leave and FMLA run concurrently or can they be taken sequentially?" Get the answer in writing. File your paperwork at weeks 28–30. Do not wait until birth.`},
  {id:'t-028',phase:'third',weekRange:[36,40],track:'Surrogacy',tags:[],
   title:`Your GC's final weeks`,
   body:`At weeks 36–40, your gestational carrier is carrying a head-engaged fetus, managing the physical load of late pregnancy — reduced sleep, pelvic pressure, possible Braxton Hicks or prodromal labor — and navigating the specific emotional territory of a pregnancy she will not parent. Research on the GC third-trimester experience (Jadva et al. 2012; Söderström-Anttila et al. 2016) documents that the majority of gestational carriers approach the final weeks with focus and purposefulness, not ambivalence about the intended parents' parentage. But they carry the physical reality of this pregnancy entirely, in their body, every day. What the research also documents: GCs in the final weeks most commonly report wanting acknowledgment of their physical and emotional experience from the intended parents — not information management or logistics only. This is a specific and important distinction. Checking in to confirm the due date logistics is different from checking in because you genuinely want to know how she is doing. She is attuned to the difference. What helps in the final weeks: direct acknowledgment of what she is carrying, a question about what she needs from you (rather than an assumption), confirmation of the birth day communication plan, and a specific expression of gratitude before the birth — not perfunctory, but real.`},
  {id:'t-029',phase:'third',weekRange:[36,41],track:'Medical',tags:['birth-attendance-ip'],
   title:`Signs of labor: what IPs need to know`,
   body:`Your gestational carrier's labor will begin without you in the room. Understanding the clinical progression lets you calibrate when to move and when to wait. Early labor: irregular contractions that may be 10–20 minutes apart, possibly lasting 30–45 seconds. This is not the signal to drive to the hospital — it can last hours or days. Active labor: contractions 5 minutes apart, lasting 60 seconds, occurring consistently for at least one hour (the 5-1-1 rule). This is the "head in that direction" signal. Transition: contractions 2–3 minutes apart, intense, lasting 60–90 seconds — this is near-delivery and typically moves quickly. Signs of rupture of membranes (water breaking): clear to pale yellow fluid, which may be a gush or a trickle. This is not a guarantee of imminent delivery but does mean going in. Prodromal labor — irregular contractions that start and stop over hours or days — is extremely common and not the same as active labor. Do not drive to the hospital for prodromal labor. Establish with your GC before the due date: what is her threshold for calling you? When will she call versus text? What happens if labor progresses faster than expected and you are more than two hours away?`},

  // ── BATCH v5.8 — Second Trimester (s-025 to s-029) ──
  {id:'s-025',phase:'second',weekRange:[14,22],track:'Emotional',tags:[],
   title:`The mid-pregnancy disconnection dip`,
   body:`Research on expectant fathers consistently documents a pattern that most men experience but few discuss: an emotional engagement dip in the second trimester. Where the first trimester often carries acute anxiety that functions as a form of intense engagement, the second trimester's relative stability can produce what Premberg et al. (2008) describe as "waiting mode" — a psychologically protective withdrawal that reduces emotional investment during a period when the pregnancy still feels distant and uncertain. For intended parents in surrogacy arrangements, this pattern is often amplified: there are no visible physical changes in your household, the GC's pregnancy may feel like something happening elsewhere, and the acute anxiety of the first trimester has eased without being replaced by tangible evidence of approaching parenthood. It is worth naming this pattern not to pathologize it, but to prevent it from becoming entrenched. The research on paternal prenatal bonding finds that fathers who actively maintained engagement during the second trimester — attending appointments, reading about fetal development stage by stage, writing, creating — reported stronger early postnatal bonding than those who were passively waiting. The engagement is the bonding infrastructure. Deliberate re-engagement at this stage is not manufactured sentiment. It is the investment that produces what you want to feel later.`},
  {id:'s-026',phase:'second',weekRange:[14,27],track:'Self',tags:['has-partner'],
   title:`The relationship window before birth`,
   body:`Gottman's longitudinal research on couples through the transition to parenthood found that the quality of the couple relationship at nine months pregnant was the single strongest predictor of relationship satisfaction at one year postpartum — stronger than income, sleep, support networks, or the parents' individual psychological health. The causal mechanism is established: couples who used the pregnancy — particularly the second trimester — to actively invest in the relationship arrived at the postpartum period with more relational capital to draw on. The second trimester is the natural window for this investment. First trimester fatigue and anxiety have typically eased; third trimester physical strain and delivery preparation haven't arrived yet. What the research identifies as specifically protective: scheduled weekly conversations that are not about logistics or birth planning — about the relationship itself, how each person is feeling, what they need; explicit agreements about postpartum division of labor, made before the emotional intensity of the newborn phase makes negotiation harder; and experiences together that are entirely non-parenting-adjacent — a trip, a project, an evening that belongs to the two of you as a couple, not as parents-in-progress. These investments are not indulgences. They are documented protective factors for what comes next. The window is open now.`},
  {id:'s-027',phase:'second',weekRange:[14,22],track:'Logistics',tags:['daycare'],
   title:`Childcare waitlist strategy`,
   body:`The NICHD Study of Early Child Care — a 10-site, decade-long longitudinal study — established that quality of childcare predicts language development, social competence, and cognitive outcomes more robustly than most other variables in early childhood. Quality varies enormously, and access to high-quality infant care is constrained by supply: in most competitive markets, quality centers are waitlisted 18–24 months in advance. The window to act is now, during the second trimester. What to look for when evaluating centers: caregiver-to-infant ratio (the AAP recommends 1:3 for infants under 12 months — anything higher is a red flag for individualized care); caregiver turnover rate (high turnover disrupts attachment, which is the central developmental task of infancy); director tenure (long-tenured directors correlate with program stability); and unannounced visit policy (centers confident in their quality welcome them). Cost context: the national average for full-time infant care in urban markets is $1,500–$2,000 per month — more in high-cost cities. This figure frequently exceeds rent or mortgage. Build it into your financial model now, before it surprises you in the postpartum period when your cognitive resources for budget revision are at their lowest.`},
  {id:'s-028',phase:'second',weekRange:[14,27],track:'Logistics',tags:['leave-paperwork'],
   title:`Stacking paternity leave`,
   body:`Federal FMLA provides 12 weeks of unpaid, job-protected leave for the birth of a child. Surrogacy-born children qualify — FMLA covers "birth of a child" and does not specify the method of conception. Many states have added paid family leave on top of FMLA: California, New York, New Jersey, Washington, Colorado, Connecticut, Oregon, Massachusetts, Maryland, Rhode Island, Hawaii, and Delaware all have state paid leave programs as of 2025 — confirm current law, as programs expand. Your employer may also offer additional paid parental leave. The critical question that most fathers never ask: "Do state paid leave and FMLA run concurrently, or can they be taken sequentially?" By default in most states, they run concurrently — you are on FMLA and drawing state pay simultaneously. But some states and some employers allow you to exhaust company paid leave first, then trigger FMLA, then draw state benefits — effectively extending your covered leave by weeks. This is not a loophole. It is the intended use of these programs. Ask HR explicitly, in writing, what your options are. File paperwork at weeks 28–30. Do not wait until birth — HR needs lead time, and the paperwork is more complicated than people expect.`},
  {id:'s-029',phase:'second',weekRange:[14,27],track:'Surrogacy',tags:[],
   title:`The IP-GC communication rhythm`,
   body:`Jadva et al.'s research on IP-GC relationship dynamics and Teman's ethnographic work on gestational carriers converge on the same finding: both intended parents and gestational carriers report higher relationship satisfaction when the communication cadence was agreed upon explicitly rather than allowed to emerge organically. The organic cadence tends to be driven by IP anxiety — contact is more frequent when anxiety is high and less frequent when things are going well — which GCs experience as monitoring rather than relationship maintenance. IPs who contacted their GC frequently during anxious periods consistently reported reduced anxiety; GCs on the receiving end of that contact pattern consistently reported increased burden. The resolution that research supports: a structured rhythm — a weekly update at an agreed time, using an agreed channel — plus an open line for developments that can't wait. The structured rhythm does its work by existing: it is the signal that the relationship is ongoing and invested, independent of whether anything happened this week. The GC can plan around it. The IP can rely on it without anxiously wondering whether it's been too long. What the research does not support: high-intensity bursts of contact followed by gaps, which produce the uncertainty both parties are trying to avoid. Set the cadence explicitly at the beginning of the second trimester. Review it at the beginning of the third.`},

  // ── BATCH v5.8 — First Trimester (f-042 to f-043) ──
  {id:'f-042',phase:'first',weekRange:null,track:'Logistics',tags:['doc-folder'],
   title:`The documents folder`,
   body:`One folder — digital and physical — built during the first trimester, that will matter at the hospital, at the pediatrician, at HR, and at the courthouse. What goes in it: a copy of the executed gestational carrier agreement (GCA); the pre-birth order, once obtained (certified original for the hospital, copies for everything else); both parents' government-issued IDs; your current health insurance card; your agency's contact sheet (agency coordinator, case manager, 24-hour emergency line); your reproductive attorney's contact; a one-page summary of your parenting status for hospital staff who may be unfamiliar with surrogacy protocol. Digital backup: scanned PDFs of all documents in a clearly named folder in Google Drive or Dropbox, shared with your partner and your attorney. Label the folder unambiguously — "BABY DOCS" or similar — so anyone assisting you can find it. An important detail your attorney should confirm: hospital pre-registration with a PBO typically requires certified originals, not copies or PDFs. Certified originals are court-issued documents with a raised seal. Confirm with your attorney which documents need to be in original form and keep them in a separate, clearly labeled envelope inside the folder. Setting this system up in the first trimester means you are not hunting for paperwork at 2am when your GC goes into labor.`},
  {id:'f-043',phase:'first',weekRange:null,track:'Self',tags:['leave-paperwork'],
   title:`Telling your employer`,
   body:`You are not legally required to disclose how your child is being conceived or carried. You are required to disclose a leave request, with appropriate notice. Under FMLA, the qualifying reason is "birth of a child and care for the newborn child" — gestational surrogacy qualifies. You do not need to explain the reproductive method to HR or your manager to invoke this protection. What to disclose: your anticipated leave start date and return date, and the qualifying reason (birth of a child). What you are not required to disclose: that your child is being carried by a gestational carrier, the details of your fertility journey, or anything about your family path. Recommended timing: inform your manager informally at weeks 16–20, framing it as operational planning ("I want to give you as much runway as possible on coverage — I'm expecting a baby around [date] and planning approximately X weeks of leave"). File the formal FMLA paperwork at weeks 26–30. Most HR departments need 30 days of advance notice for FMLA. Frame every conversation operationally: what coverage looks like, who handles what, how you will transition out and back. This framing protects the relationship with your manager and keeps the conversation on professional ground, which is where you want it.`},
];"""

assert OLD3 in src, "LIBRARY_CARDS closing anchor not found — check n-033 body text"
src = src.replace(OLD3, NEW3, 1)
print('  - LIBRARY_CARDS: 25 new cards added (n-034–n-043, t-022–t-029, s-025–s-029, f-042–f-043)')

# ── 4. Add q-022 and q-023 to DAILY_QUESTIONS ──────────────────────────────────
OLD4 = """  {id:'q-021',phase:'any',weekRange:null,triggeredByTag:'support-network',
   question:`How's your support network for the newborn phase coming along?`,
   options:[
    {label:`Sorted — meals, coverage, and help are all organized`,stateUpdate:{addMilestone:'support-network'}},
    {label:`Working on it — some pieces in place but not locked in`,stateUpdate:{setMilestoneInProgress:'support-network'}},
    {label:`Haven't really started thinking about it`,stateUpdate:{setMilestoneNotStarted:'support-network'}},
    {label:`Skip`,stateUpdate:{skipQuestion:true}}
  ]},
];"""

NEW4 = """  {id:'q-021',phase:'any',weekRange:null,triggeredByTag:'support-network',
   question:`How's your support network for the newborn phase coming along?`,
   options:[
    {label:`Sorted — meals, coverage, and help are all organized`,stateUpdate:{addMilestone:'support-network'}},
    {label:`Working on it — some pieces in place but not locked in`,stateUpdate:{setMilestoneInProgress:'support-network'}},
    {label:`Haven't really started thinking about it`,stateUpdate:{setMilestoneNotStarted:'support-network'}},
    {label:`Skip`,stateUpdate:{skipQuestion:true}}
  ]},
  {id:'q-022',phase:'third',weekRange:null,triggeredByTag:'birth-plan',
   question:`Have you finalized the birth day plan with your GC and the medical team?`,
   options:[
    {label:`Yes — written, shared with GC and OB, I know my role`,stateUpdate:{addMilestone:'birth-plan'}},
    {label:`Working on it — some pieces in place but not finalized`,stateUpdate:{setMilestoneInProgress:'birth-plan'}},
    {label:`Not started yet`,stateUpdate:{setMilestoneNotStarted:'birth-plan'}},
    {label:`Skip`,stateUpdate:{skipQuestion:true}}
  ]},
  {id:'q-023',phase:'preparing',weekRange:null,triggeredByTag:'wills',
   question:`Have you updated your wills to name a guardian for your child?`,
   options:[
    {label:`Yes — updated, signed, and filed`,stateUpdate:{addMilestone:'wills'}},
    {label:`In progress — started but not finalized`,stateUpdate:{setMilestoneInProgress:'wills'}},
    {label:`Not yet — it's on the list`,stateUpdate:{setMilestoneNotStarted:'wills'}},
    {label:`Skip`,stateUpdate:{skipQuestion:true}}
  ]},
];"""

assert OLD4 in src, "DAILY_QUESTIONS closing anchor not found — check q-021 text"
src = src.replace(OLD4, NEW4, 1)
print('  - DAILY_QUESTIONS: q-022 (birth-plan) and q-023 (wills) added')

# ── 5. Add birth-plan and hospital-tour to MILESTONE_JOURNAL_PROMPTS ───────────
OLD5 = """  'doc-folder': {
    'not-started': [
      `Your document folder isn't set up yet. What's the one document you'd be most stressed to not find in an emergency?`,
    ],
    'in-progress': [
      `Your docs are scattered but you're working on it. What has this revealed about how you handle logistics under pressure?`,
    ],
    'done': [
      `Documents organized. Write about the moment you felt like you were actually on top of this whole thing.`,
    ],
  },
};"""

NEW5 = """  'doc-folder': {
    'not-started': [
      `Your document folder isn't set up yet. What's the one document you'd be most stressed to not find in an emergency?`,
    ],
    'in-progress': [
      `Your docs are scattered but you're working on it. What has this revealed about how you handle logistics under pressure?`,
    ],
    'done': [
      `Documents organized. Write about the moment you felt like you were actually on top of this whole thing.`,
    ],
  },
  'birth-plan': {
    'not-started': [
      `You haven't written the birth plan yet. What do you actually want the day of birth to feel like? Not logistics — the feeling.`,
    ],
    'in-progress': [
      `You're working on the birth plan. What's the part you keep putting off writing, and what does that avoidance tell you?`,
    ],
    'done': [
      `The plan is written. What did you have to decide that surprised you? What do you hope happens — and what are you prepared for if it doesn't?`,
    ],
  },
  'hospital-tour': {
    'not-started': [
      `You haven't toured the hospital yet. What are you most uncertain about when you picture the day of birth?`,
    ],
    'in-progress': [
      `You're arranging the hospital tour. What specific question do you most need answered before you walk into that room for real?`,
    ],
    'done': [
      `You've toured the hospital. Write about walking those hallways knowing your child will be born there. What landed?`,
    ],
  },
};"""

assert OLD5 in src, "MILESTONE_JOURNAL_PROMPTS closing anchor not found — check doc-folder entry"
src = src.replace(OLD5, NEW5, 1)
print('  - MILESTONE_JOURNAL_PROMPTS: birth-plan and hospital-tour entries added')

# ── 6. Add paternity leave research task to SEED_TASKS ────────────────────────
OLD6 = "  { phase:'post-birth', cat:'Logistics', tags:[],       title:'Send birth announcements to family and friends' }\n];"
NEW6 = ("  { phase:'post-birth', cat:'Logistics', tags:[],       title:'Send birth announcements to family and friends' },\n"
        "  { phase:'pre-transfer', cat:'Financial', tags:[],     title:`Research your state's paternity leave law and what your company policy provides` }\n"
        "];")

assert OLD6 in src, "SEED_TASKS closing anchor not found — check last task text"
src = src.replace(OLD6, NEW6, 1)
print("  - SEED_TASKS: paternity leave research task added")

# ── 7. Write output ────────────────────────────────────────────────────────────
outfile = 'daddy-duty-v5_8.html'
with open(outfile, 'w', encoding='utf-8') as f:
    f.write(src)
shutil.copy(outfile, 'docs/index.html')

sw_src = open('docs/sw.js', encoding='utf-8').read()
sw_new = re.sub(r"(const CACHE\s*=\s*'daddy-duty-)[^']*(')",
                r"\1v5-8\2", sw_src)
sw_new = re.sub(r"(cache key: daddy-duty-)[^\s*]*",
                r"\1v5-8", sw_new)
with open('docs/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_new)
print(f'  - Output written: {outfile} + docs/')

# ── 8. JS syntax check ───────────────────────────────────────────────────────
node = '/opt/homebrew/bin/node'
if not os.path.exists(node):
    node = '/usr/local/bin/node'
if os.path.exists(node):
    scripts = re.findall(r'<script(?!\s+src)[^>]*>(.*?)</script>', src, re.DOTALL)
    app_script = max(scripts, key=len)
    with open('/tmp/check_v5_8.js', 'w') as f:
        f.write(app_script)
    result = subprocess.run([node, '--check', '/tmp/check_v5_8.js'], capture_output=True, text=True)
    assert result.returncode == 0, f"JS syntax error:\n{result.stderr}"
    print('  - JS syntax: ✓ (node --check passed)')
else:
    print('  - JS syntax: ⚠ skipped (node not found)')

# ── 9. Sanity assertions ─────────────────────────────────────────────────────
content = open(outfile, encoding='utf-8').read()
assert "v5.8 \xb7 cloud sync"          in content, "version string missing"
assert "appVersion:'v5.8'"             in content, "appVersion missing"
assert "window.confirm("           not in content, "window.confirm() regression"
assert "id:'n-043'"                    in content, "n-043 missing"
assert "id:'t-029'"                    in content, "t-029 missing"
assert "id:'s-029'"                    in content, "s-029 missing"
assert "id:'f-043'"                    in content, "f-043 missing"
assert "id:'q-022'"                    in content, "q-022 missing"
assert "id:'q-023'"                    in content, "q-023 missing"
assert "'birth-plan'"                  in content, "birth-plan journal prompts missing"
assert "'hospital-tour'"               in content, "hospital-tour journal prompts missing"
assert "paternity leave law"           in content, "SEED_TASK missing"
# Card count check
card_count = content.count("id:'n-") + content.count("id:'t-") + content.count("id:'s-") + content.count("id:'f-") + content.count("id:'a-") + content.count("id:'b-")
# Rough check: should be at least 210+ unique IDs in LIBRARY_CARDS
assert card_count >= 210, f"Card count seems low: {card_count}"
print('  - Sanity assertions: ✓ all passed')
print()
print('✨ Build complete: daddy-duty-v5_8.html')
