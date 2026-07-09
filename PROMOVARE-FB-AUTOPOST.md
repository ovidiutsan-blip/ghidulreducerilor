# Autoposter Facebook personal — plan & operare

Agent: `agents/marketing/personal_fb_autoposter.py`
Scop: postează autonom pe profilul personal FB câte un deal cu comision, la interval
de ~2h în timpul zilei, cu disciplină anti-ban, ca să aducă trafic gratuit pe site.

## ⚠️ Realitatea riscului (citește o dată)

Automatizarea postării pe profil personal **încalcă ToS Facebook**. Riscul de ban
NU vine dintr-o postare, ci din **tipar de bot**: ore fixe, frecvență mare, sesiune
automatizată detectabilă. Agentul e proiectat să pară cât mai uman și să se
autoprotejeze, dar riscul rezidual există. De aceea:
- Frecvență mică (implicit max 4/zi, ~la 2h, doar ziua).
- Timing neregulat (jitter + skip aleator) — nu la fix.
- **HALT automat** la primul semn de checkpoint/captcha/limitare → oprește tot până
  când verifici manual contul. Asta previne escaladarea unui soft-block în ban.
- Prima săptămână: verifică zilnic că nu apar avertismente pe cont.

## Ce postează

- 1 deal per rulare, **doar magazine cu comision** (2Performant / Profitshare —
  exclude evomag brut). Reutilizează selecția din `personal_fb_generator.py`.
- **Rotație de magazine pe zi**: nu postează același magazin de două ori/zi
  (altfel Casa New Concept, cu 463 deal-uri, ar domina tot).
- Preț între 25 și 400 lei (produse de impuls, chilipir credibil de recomandat).
- Titlu curățat de coduri SKU (sună a om, nu a catalog).
- Dedup partajat cu generatorul (`fb_personal_log.json`) — nu repetă deal-uri.

### Link: în corp vs. în comentariu
- **Implicit `link_in_body=True`**: linkul (cu UTM) intră în corpul postării.
  FIABIL — nu poate rata. Reach ceva mai mic (FB temperează linkurile externe), dar
  pentru un agent autonom fiabilitatea bate optimizarea marginală de reach.
- `link_in_body=false` (în `data/marketing/fb_autopost_config.json`): tactica
  link-in-primul-comentariu (reach mai bun). Automatizarea comentariului e mai
  fragilă — o folosești doar dacă monitorizezi rezultatele.

## Model de rulare: Task Scheduler (recomandat)

Nu rulează ca daemon. Task Scheduler îl declanșează la fiecare 2h în fereastra de zi;
fiecare rulare postează **cel mult una** și iese. Sloturile: 10, 12, 14, 16, 18, 20.
Cu skip aleator (25%) rezultă ~3 postări/zi, nepredictibil.

Creează task-ul (PowerShell, o singură dată). Ajustează calea Python dacă e nevoie:

```powershell
$py  = "C:\Python314\python.exe"
$job = "C:\dev\ghidulreducerilor.ro\agents\marketing\personal_fb_autoposter.py"
$act = New-ScheduledTaskAction -Execute $py -Argument "`"$job`" --run" `
        -WorkingDirectory "C:\dev\ghidulreducerilor.ro"
# declanșează la 10:00 și repetă la 2h până la 20:00
$trg = New-ScheduledTaskTrigger -Daily -At 10:00AM
$trg.Repetition = (New-ScheduledTaskTrigger -Once -At 10:00AM `
        -RepetitionInterval (New-TimeSpan -Hours 2) `
        -RepetitionDuration (New-TimeSpan -Hours 10)).Repetition
Register-ScheduledTask -TaskName "GR_FB_Autopost" -Action $act -Trigger $trg `
        -Description "Autoposter FB personal ghidulreducerilor.ro"
```

Oprire temporară: `Disable-ScheduledTask -TaskName "GR_FB_Autopost"`
Repornire: `Enable-ScheduledTask -TaskName "GR_FB_Autopost"`

## Comenzi

```
python agents/marketing/personal_fb_autoposter.py --status        # câte postări azi, HALT, gap
python agents/marketing/personal_fb_autoposter.py --dry-run       # ce AR posta (fără browser)
python agents/marketing/personal_fb_autoposter.py --test-compose  # completează compozitorul, NU publică
python agents/marketing/personal_fb_autoposter.py --once-live     # 1 postare reală, supravegheat
python agents/marketing/personal_fb_autoposter.py --run           # 1 postare dacă regulile permit (Scheduler)
python agents/marketing/personal_fb_autoposter.py --reset-halt    # după ce ai rezolvat un block manual
```

## Config (`data/marketing/fb_autopost_config.json`, gitignored)

| cheie | implicit | rol |
|-------|----------|-----|
| window_start_hour / window_end_hour | 10 / 20 | fereastra de zi |
| max_per_day | 4 | plafon zilnic |
| min_gap_minutes | 110 | ~2h între postări |
| jitter_max_minutes | 35 | întârziere aleatoare la start (anti-ore-fixe) |
| skip_probability | 0.25 | șansa de a sări peste un slot (anti-tipar) |
| max_price / min_price | 400 / 25 | intervalul de preț |
| link_in_body | true | link în corp (fiabil) vs. în comentariu |

## Monitorizare

- `logs/fb_autopost/*.png` — screenshot la fiecare pas (posted, commented, erori, block).
- `--status` — rezumat rapid.
- Dacă vezi `HALTED: True` → intră MANUAL pe FB, rezolvă checkpoint-ul, apoi `--reset-halt`.

## Idei de creștere (după ce rularea autonomă e stabilă 1–2 săptămâni)

1. **Grupuri FB** (reach mult mai mare, risc mai mic decât profilul): `facebook_poster.py`
   deja postează în grupuri — sincronizează cadența cu autoposterul ca să nu suprapui.
2. **Poză produs atașată** — crește reach-ul organic; necesită download imagine → upload.
3. **Fereastră adaptată la trafic** — mută sloturile pe orele cu engagement maxim
   (verifică în GA4 / Meta când postările prind cel mai bine).
4. **Variație de ton** — hook-urile se rotesc deja; adaugă formate (întrebare, „top 3”).
5. **Măsurare** — filtrează în GA4 după `utm_medium=personal` ca să vezi ce magazine/
   deal-uri aduc click-uri și taie ce nu convertește.
