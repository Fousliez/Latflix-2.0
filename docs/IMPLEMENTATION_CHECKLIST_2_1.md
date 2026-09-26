# Latflix 2.1 – implementační checklist

Tento soubor je pracovní kontrolní seznam nad `docs/SPEC_LATFLIX_2.md`.
Specifikace zůstává zdroj pravdy. Checklist pouze hlídá, aby se při přepisu nic neztratilo.

Procesní pravidlo:
- GitHub Actions nepoužívat ani nekontrolovat bez výslovného svolení uživatele.
- Každé nové potvrzené pravidlo nejdřív porovnat se SPEC.
- Konflikt neřešit tichým přepsáním; vyžádat rozhodnutí uživatele.
- Starší funkční chování zůstává, pokud nebylo výslovně změněno.

## A. Globální kostra

- [x] Hlavní menu: Soubor / Úpravy / Nástroje / Zobrazení / Nastavení / Nápověda
- [x] Levé menu se všemi hlavními a pomocnými sekcemi
- [x] Aktivní sekce je zvýrazněná
- [x] Levé menu lze skrýt a znovu zobrazit
- [x] Horní pracovní panel je u datových sekcí pevně 136 px
- [x] Horní panel lze skrýt přes Zobrazení
- [x] Přehled je výjimka z 136 px panelu
- [x] Spodní stavový řádek
- [x] Počet aktuálně zobrazených záznamů
- [x] Girls / Oblíbené: průměrný věk ve stavovém řádku
- [x] Nastavení velikosti řádků 1–5
- [x] Přetrvávající uživatelské nastavení velikosti řádků

## B. Společný tabulkový základ

- [x] QTableView / model-view základ
- [x] První sloupec = zámek řádku
- [x] Druhý sloupec = aktuální vizuální číslo řádku
- [x] Zámek patří stabilnímu záznamu
- [x] Zamčený řádek nelze běžně editovat
- [x] Zamčené záznamy nelze běžnou akcí Smazat odstranit
- [x] Střídání řádků bílá / světle šedá
- [x] Výběr je řádkový, current-cell vrstva je vizuálně potlačená
- [x] Souvislý výběr je kreslen jako jeden obrys bez mezer
- [x] Ctrl / Shift vícenásobný výběr
- [x] Kliknutí do volné části tabulky ruší výběr
- [x] Jedno kliknutí otevře editor běžné editovatelné buňky
- [x] Výběrové buňky se otevřou jedním kliknutím
- [x] Výběrové buňky nemají viditelnou šipku
- [x] Výběrová buňka si nevytváří vlastní barevné zvýraznění
- [x] Enter v textovém editoru postupuje právě o jeden řádek níž
- [x] Poznámka: 1 klik inline, dvojklik velký editor
- [x] Zamčený hlavní text: dvojklik kopíruje do schránky
- [x] Potvrzení „Zkopírováno“
- [x] Hlavička tabulky je výchozí zamčená
- [x] Po odemčení lze měnit šířku a pořadí sloupců
- [x] Rozložení sloupců se ukládá po sekcích
- [x] Po odemčení: přejmenování / skrytí sloupce
- [x] Obnovení skrytých sloupců přes Zobrazení
- [ ] Větší vizuální zámek hlavičky než zámky řádků
- [ ] Přesná globální plynulost předání dropdown -> dropdown jedním klikem ověřit v praxi
- [x] Globální odstranění zcela prázdných nových řádků při opuštění sekce / zavření
- [x] Nový řádek se otevírá rovnou k editaci
- [x] Nové řádky jsou v netříděném pohledu nahoře
- [x] Dočasné řazení klikem na všechny datové hlavičky bez viditelné šipky
- [x] Hledání je lokální fulltext bez našeptávače
- [x] Koš vedle Hledání maže pouze Hledání
- [x] Vyčistit maže Hledání i všechny filtry
- [ ] Ukládání uživatelských přejmenování hlaviček ověřit napříč všemi sekcemi

## C. Girls / Oblíbené

- [x] Stejná tabulka, Oblíbené je podmnožina Girls
- [x] Sloupce dle SPEC
- [x] Přidat 1 / 5 / 10 řádků
- [x] V Oblíbené jsou Přidat a Smazat trvale vypnuté
- [x] Hromadné Přidat / Odebrat z Oblíbených
- [x] Hromadně přidat odkazy
- [x] Filtry Národnost / Typ / Stav / Sex / Nahota / Obličej / Profilovka
- [x] Národnost: top 10 + Další
- [x] Typ a Národnost se načítají z centrálních katalogů
- [x] Věk: 1–100 věk, >100 rok narození, mimo editaci vypočtený věk
- [x] Sledování = počet konkrétních URL
- [x] Počet výskytů dle platných videozáznamů
- [x] Tagy: popup, centrální katalog, barvy, řazení podle použití
- [x] Tag popup: Uložit/Zrušit, bez X, ukotvení k buňce
- [x] Horní panel: jméno, věk, počet výskytů
- [x] Horní panel: Oblíbené / ★ V oblíbených
- [x] Horní panel: rychlé modré odkazy, seskupení stejné platformy
- [x] Horní panel: Odkazy / Detail / Zobrazit odkazy
- [x] Dialog Detail: základní pole včetně aliasů po 4 na řádek
- [x] Dialog Odkazy: uložené odkazy + 10 řádků pro nové
- [x] Profilovka: klik = výběr souboru, pravé = smazání
- [x] Profilovka: dvojklik = výřez libovolné oblasti obrazovky včetně jiného monitoru
- [ ] Přesné vizuální doladění panelu proti screenshotům

## D. Videa / Super

- [x] Stejná tabulka, Super je podmnožina Videa
- [x] Sloupce dle SPEC
- [x] Přidat / Smazat
- [x] Přidat do SUPER / Odebrat ze SUPER s potvrzením odebrání
- [x] Bez Hromadných akcí
- [x] Filtry Studio / Stav / Kvalita
- [x] Studio filtr se řadí podle výskytů
- [x] Stav a Kvalita se načítají z centrálních katalogů
- [x] Stav NECHCI: červený Stav + číslo řádku, Kvalita/Dostup./Velikost disabled
- [x] Více účinkujících přes Detail videa
- [x] Viditelné Dívka 1–3 se řadí dynamicky podle výskytů
- [x] Fulltext prohledává všechny účinkující, hlavní jména i aliasy
- [x] Našeptávač Herečka: hlavní jméno + aliasy, jen odpovídající label
- [x] Našeptávač Studio
- [x] Chybějící herečka/studio: potvrdit a vytvořit nový centrální záznam
- [x] Horní panel Studia / Herečky
- [x] Modré filtry řazené podle výskytů
- [x] Ctrl / Shift vícenásobné modré filtry s OR
- [x] Max. 3 řádky modrých prvků
- [x] Detail videa
- [x] Vzhled našeptávače: větší font/řádky, modrá aktivní položka s bílým textem
- [x] Studio dropdown filtr: cca 15 viditelných položek + scrollbar explicitně nastavit
- [ ] Detail videa vizuálně dorovnat referenci

## E. Studia

- [x] Zámek + číslo
- [x] Název / Typ / Odkaz / Počet výskytů
- [x] Přidat / Smazat / Hledání / koš / Vyčistit
- [x] Počet výskytů podle stejné validity videa
- [x] Nová studia nahoře v netříděném pohledu

## F. Odkazy

- [x] Tabulka konkrétních odkazů
- [x] Horní karty Vše / Sítě / Zdroje / Rozcestníky
- [x] Modré filtry podle názvu odkazu
- [x] Ctrl / Shift vícenásobný výběr s OR
- [x] Seznam položek / centrální katalog názvů odkazů
- [x] Viditelné filtry
- [x] Hromadně přidat odkazy
- [x] Export pracuje jen s aktuálně vyfiltrovanou tabulkou
- [x] Exportní typy řazené počtem sestupně, při shodě abecedně
- [x] Každý exportní typ má vlastní checkbox
- [x] TXT = jedna URL na řádek
- [x] Vyčistit ruší i modré filtry a filtr herečky
- [x] Viditelný indikátor aktivního filtru „odkazy konkrétní herečky“
- [x] Stránkování modrých filtrů podle reference (např. 1/2 + šipky)
- [x] Tlačítko Zobrazit odkazy – nyní otevírá po potvrzení právě aktuálně zobrazené URL; případné odlišné chování upravit podle praktického testu
- [ ] Přesné významy a workflow Kontrola / Staženo / Akt. / Poslední text / Poslední obrázek doladit v testování

## G. Přehled

- [x] Karty Girls / Oblíbené / Videa / SUPER / Studia / Odkazy / Tagy
- [x] Dynamické počty
- [x] Kliknutí otevře malý detailní dialog
- [x] Girls: počet / průměrný věk / národnosti / Oblíbené
- [x] Studia: počet / použitá / nejčastější
- [x] Odkazy: celkem / sítě / zdroje / rozcestníky
- [x] Tagy: počet / použité / nejpoužívanější
- [x] Oblíbené: položka Ohodnoceno dle SPEC
- [x] Videa: položka Ohodnoceno dle SPEC
- [x] SUPER: položka Ohodnoceno dle SPEC
- [ ] Přesnější vzhled karet podle původního Latflixu

## H. Pomocné sekce

- [x] Stavy
- [x] Kvality
- [x] Tagy
- [x] Typy
- [x] Národnosti
- [x] Tagy mají uloženou barvu
- [x] Barvu tagu lze měnit
- [ ] Vizuální styl pomocných tabulek dorovnat screenshotům

## I. Zbývající integrační ověření

- [ ] Linux: prostřední tlačítko v aktivním QLineEdit v tabulce
- [ ] Přechod editor -> jiný editor jedním klikem ve všech kombinacích
- [ ] Přechod dropdown -> dropdown jedním klikem
- [ ] Ověřit, že jedno fyzické Enter nikdy nepřeskočí dva řádky
- [ ] Ověřit persistenci pořadí/šířek/skrytí/přejmenování po restartu
- [ ] Ověřit chování se stovkami až tisíci řádky
- [ ] Finální průchod každou sekcí proti screenshotům
