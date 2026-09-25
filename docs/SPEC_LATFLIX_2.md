# Latflix 2.0 – pracovní specifikace

## 1. Základní směr aplikace

Latflix 2.0 má být multiplatformní program pro správu hereček, videí a příbuzných dat.

### Cílové platformy
- Linux
- Windows
- do budoucna pokud možno Android

### Zásadní vlastnosti
- Latflix 2.0 není přehrávač.
- Prioritou je rychlost, svižnost a dobrá práce s velkým množstvím dat.
- Vzhled je důležitý, ale nesmí být na úkor výkonu.
- Do budoucna se počítá s tisíci záznamů a větším množstvím tabulek.

### Platnost současné specifikace
- Aktuální písemný popis aplikace a všechny přiložené screenshoty jsou primárně specifikací pro desktopovou verzi Latflixu 2.0, tedy Linux a Windows.
- Budoucí Android verze má zachovat podobnou logiku, datový model a základní funkční principy, ale její GUI bude navrženo samostatně pro mobilní prostředí.
- Vzhled desktopové verze se tedy nemá mechanicky přenášet na Android.
- Android verze je zatím vzdálená budoucnost a současná specifikace ji neřeší jako vizuální referenci.

## 2. Hlavní rozložení aplikace

Aplikace má mít klasické desktopové rozložení:

1. horní systémové/menu pásmo,
2. levé navigační menu,
3. horní pracovní panel,
4. hlavní pracovní plochu,
5. spodní stavový řádek.

### Horní nabídka
V horní části bude klasická nabídka:
- Soubor
- Úpravy
- Nástroje
- Zobrazení
- Nastavení
- Nápověda

## 3. Levé menu

Levé menu bude ve výchozím nastavení viditelné.

Bude obsahovat:
- nahoře hlavní sekce,
- dole vedlejší sekce,
- pod nimi rychlé filtry.

Nad seznamem hlavních sekcí bude šipka pro skrytí levého menu, aby bylo možné získat více prostoru pro hlavní pracovní plochu.

### Hlavní sekce
- Přehled
- Girls
- Oblíbené
- Odkazy
- Videa
- Super
- Studia

### Vedlejší sekce
Umístěné dole v levém menu:
- Stavy
- Kvality
- Tagy
- Typy

### Rychlé filtry
Budou umístěné pod vedlejšími sekcemi.

Budou skrytelné a do budoucna půjde:
- přidávat,
- mazat,
- přesouvat,
- dále upravovat.

Přesné chování rychlých filtrů bude doplněno později.

## 4. Horní pracovní panel

Horní pracovní panel bude ve výchozím nastavení viditelný.

Nebude zasahovat přes levé menu. Začne až napravo od levého menu a bude pokračovat přes hlavní pracovní plochu až k pravému okraji aplikace.

Při zobrazeném levém menu tedy horní panel zleva „narazí“ do pravého okraje levého menu.

Horní pracovní panel půjde skrýt přes nabídku **Zobrazení**.

### Pevná výška horního pracovního panelu

Ze současné implementace Latflixu vychází základní výška horního detailního/pracovního panelu na **136 px**.

Pro Latflix 2.0 platí:
- výška horního panelu bude pevně **136 px**,
- tato výška se nebude měnit podle obsahu, sekce, šířky okna ani jiného stavu aplikace,
- panel se nesmí automaticky zvětšovat ani zmenšovat,
- jediná změna jeho vertikálního prostoru bude úplné skrytí panelu přes nabídku **Zobrazení**,
- po opětovném zobrazení se panel vrátí na pevnou výšku **136 px**.

Poznámka k současnému kódu: současný panel používá základní hodnotu `GIRL_DETAIL_HEIGHT = 136`, ale může se dynamicky zvětšovat podle obsahu odkazů. Toto dynamické zvětšování se do nové specifikace nepřenáší.


## 5. Stavový řádek

Úplně dole v aplikaci bude stavový řádek.

### Levá část
Bude zobrazovat počet záznamů.

Pravidla:
- v sekci Přehled se počet záznamů nezobrazuje,
- v ostatních sekcích se zobrazuje počet záznamů aktuální sekce,
- při použití filtru nebo hledání se zobrazuje počet výsledků filtru nebo hledání.

### Pravá část
Bude obsahovat nastavení velikosti řádků / buněk.

Rozsah:
- 1 až 5

Výchozí hodnota:
- 1

Jednotlivé sekce mohou mít ve stavovém řádku další vlastní informace. Ty budou specifikovány později.

## 6. Viditelnost základních panelů

### Levé menu
- ve výchozím nastavení viditelné,
- skrývá se šipkou v levém menu.

### Horní pracovní panel
- ve výchozím nastavení viditelný,
- skrývá se přes nabídku Zobrazení.


## 7. Chování hlavního okna vůči okrajům obrazovky

Jednou ze základních funkcí desktopové verze je systémové přichytávání okna k okrajům monitoru.

Požadované chování:
- po přetažení okna k pravému okraji obrazovky se aplikace přichytí a vyplní pravou polovinu obrazovky,
- po přetažení okna k levému okraji obrazovky se aplikace přichytí a vyplní levou polovinu obrazovky,
- aplikace má respektovat běžné chování operačního systému pro přichytávání oken k okrajům a rohům monitoru,
- tato funkce je základní požadavek pro desktopovou verzi na Windows i Linuxu a musí být zohledněna už od návrhu hlavního okna.


## 8. Tabulkový základ aplikace

Srdcem Latflixu 2.0 bude tabulkové zobrazení podobné principu Excelu, ale navržené jako lehká a svižná datová tabulka, nikoli jako plnohodnotný tabulkový procesor.

Základní požadavky:
- tabulka bude hlavní pracovní prvek aplikace,
- musí zvládat tisíce záznamů bez pocitu těžkopádnosti,
- priorita je rychlé vykreslování, rychlá odezva a nízká režie,
- vzhled a efekty nesmí být na úkor výkonu,
- tabulka má působit jednoduše, čistě a lehce,
- konkrétní chování sloupců, řádků, výběrů, editace, řazení, filtrů a dalších funkcí bude doplněno postupně.

### Sdílené chování tabulek napříč sekcemi

Základní tabulkový systém bude napříč sekcemi co nejvíce jednotný.

Platí zejména:
- chování řádků bude stejné ve všech sekcích,
- obecné chování buněk bude stejné ve všech sekcích,
- zámky a jejich logika budou stejné ve všech sekcích,
- výběr, zvýraznění, základní editace a další obecné interakce tabulky budou řešeny jedním společným systémem,
- jednotlivé sekce se budou primárně lišit názvy a skladbou sloupců,
- výjimkou mohou být specifické typy buněk nebo celé sloupce se zvláštním chováním,
- tyto výjimky se budou definovat postupně pro konkrétní sekce a sloupce.

Cílem je zabránit duplikování stejné tabulkové logiky v každé sekci a držet jednotné chování celé aplikace.

### Zamykání řádků a hlavičky tabulky

První sloupec tabulky bude sloužit jako zamykací sloupec.

#### Zamykání jednotlivých řádků
- každý datový řádek bude mít v prvním sloupci zámek,
- odemčený řádek bude mít u zámku bílé pozadí,
- zamčený řádek bude mít u zámku tmavé pozadí,
- kliknutím na zámek v daném řádku se řádek přepne mezi zamčeným a odemčeným stavem,
- zamčený řádek nebude možné běžně editovat,
- některé buňky nebo sloupce mohou být z tohoto pravidla výjimkou; tyto výjimky budou definovány později,
- toto chování bude společné napříč sekcemi.

#### Zamykání hlavičky tabulky
Úplně první řádek tabulky, tedy řádek s názvy sloupců, bude mít vlastní zámek vlevo.

Výchozí stav:
- hlavička bude zamčená,
- sloupce nepůjdou přesouvat,
- nepůjde měnit jejich šířka.

Po kliknutí na zámek hlavičky:
- hlavička se odemkne,
- sloupce půjdou přesouvat mezi sebou chycením a tažením,
- půjde měnit jejich šířku tažením hranice mezi sloupci podobně jako v Excelu.

Po opětovném zamknutí:
- přesouvání sloupců se znovu zakáže,
- změna jejich šířky se znovu zakáže.

#### Ukládání rozložení sloupců
Aplikace si bude pamatovat:
- pořadí sloupců,
- šířku jednotlivých sloupců.

Toto nastavení bude:
- uložené zvlášť pro každou sekci, protože jednotlivé sekce mají rozdílné sloupce,
- zachované i po ukončení aplikace,
- po novém spuštění aplikace automaticky obnovené do posledního uloženého stavu dané sekce.

### Kontextová nabídka hlavičky sloupců

Po odemčení hlavičky tabulky bude možné pracovat i s názvy a viditelností sloupců.

Po kliknutí pravým tlačítkem na název běžného datového sloupce se zobrazí kontextová nabídka obsahující minimálně:
- **Přejmenovat sloupec** – umožní změnit zobrazovaný název sloupce,
- **Skrýt sloupec** – skryje daný sloupec z aktuálního zobrazení.

Pravidla:
- tyto volby budou dostupné pouze tehdy, když je hlavička tabulky odemčená,
- po opětovném zamknutí hlavičky nebude možné sloupce přejmenovávat ani skrývat tímto způsobem,
- způsob opětovného zobrazení skrytých sloupců bude řešen přes nabídku **Zobrazení**; přesné chování této části se doplní později.


### Velikost zámku hlavičky a číslování řádků

- zámek v hlavičce tabulky, který řídí přesouvání a změnu šířky sloupců, bude vizuálně větší než zámky jednotlivých datových řádků; vzhled se má řídit referenčním screenshotem,
- bezprostředně vpravo vedle zamykacího sloupce bude úzký sloupec s pořadovým číslem řádku,
- každý datový řádek bude mít číslo 1, 2, 3, ... podle své aktuální pozice v právě zobrazené tabulce,
- tato čísla nejsou trvalé identifikátory záznamů,
- při řazení, filtrování, vyhledávání nebo jiném přeskupení tabulky se číslování vždy přepočítá shora od 1,
- příklad: pokud je po seřazení první Anna Fox, zobrazí číslo 1; pokud je po jiném seřazení první Little Caprice, zobrazí číslo 1 ona,
- číslování tedy vyjadřuje pouze aktuální pořadí řádku v tabulce.

### Vazba zámku na konkrétní záznam

- stav zámku patří ke konkrétnímu záznamu, nikoli k jeho aktuální pozici v tabulce,
- zamykací buňka se proto při řazení, filtrování, vyhledávání a jiném přeskupení vždy přesouvá spolu se svým záznamem,
- pořadové číslo řádku se může změnit, ale stav zámku záznamu zůstává zachovaný,
- příklad: pokud je Little Caprice na řádku 1 odemčená a Anna Fox na řádku 2 zamčená, po vyhledání Anna Fox může být zobrazena jako řádek 1, ale její zámek musí zůstat zamčený,
- zamykací sloupec tedy reprezentuje vlastnost záznamu, zatímco číslovací sloupec reprezentuje pouze aktuální pořadí zobrazení.

### Střídání barev řádků a výběr řádků

#### Střídání barev řádků
- datové řádky budou mít vždy střídavé pozadí: světle modrá, světle zelená, světle modrá, světle zelená, ...
- toto střídání se řídí aktuálním pořadím zobrazených řádků, nikoli konkrétním záznamem,
- po filtrování, vyhledávání, řazení nebo jiném přeskupení se barvy vždy znovu přepočítají podle aktuálního pořadí shora dolů,
- tím pádem první zobrazený řádek bude vždy modrý, druhý zelený, třetí modrý atd.

#### Výběr řádků
- kliknutí na číslo řádku v úzkém číslovacím sloupci vybere celý daný řádek,
- zamykací buňka se do vizuálního zvýraznění vybraného řádku nezahrnuje,
- vybraný řádek nemění svou základní modrou/zelenou barvu,
- výběr se zobrazí zvýrazněným rámečkem po celé délce řádku, kromě zamykací buňky,
- více řádků lze vybrat současně pomocí Ctrl,
- souvislý rozsah řádků lze vybrat pomocí Shift,
- více řádků lze vybrat také kliknutím a tažením přes číslovací oblast/řádky,
- kliknutím do volné, prázdné části aplikace se aktuální výběr řádků zruší.

#### Hromadné akce
- při výběru více řádků bude možné provádět hromadné akce,
- konkrétní seznam hromadných akcí se bude definovat později zvlášť pro jednotlivé sekce/tabulky.

### Vztah tabulek Girls a Oblíbené

- tabulka v sekci **Girls** a tabulka v sekci **Oblíbené** budou z hlediska tabulkového systému úplně totožné,
- budou sdílet stejné sloupce, stejné chování řádků, buněk, zámků, výběrů, řazení, editace, výjimek i všechny budoucí změny tabulkové logiky,
- jakákoli budoucí úprava nebo výjimka definovaná pro tabulku Girls se automaticky vztahuje i na tabulku Oblíbené, pokud uživatel výslovně neurčí jinak,
- toto pravidlo se vztahuje pouze na samotnou tabulku; netýká se tlačítek, panelů ani dalších prvků nad tabulkou,
- rozdíl mezi sekcemi je pouze v datech: sekce **Oblíbené** zobrazuje pouze vybranou podmnožinu dat ze sekce **Girls**.








### Vztah tabulek Videa a Super

- tabulka v sekci **Videa** a tabulka v sekci **Super** budou z hlediska tabulkového systému úplně totožné,
- budou sdílet stejné sloupce, stejné chování řádků, buněk, zámků, výběrů, řazení, editace, výjimek i všechny budoucí změny tabulkové logiky,
- jakákoli budoucí úprava nebo výjimka definovaná pro tabulku Videa se automaticky vztahuje i na tabulku Super, pokud uživatel výslovně neurčí jinak,
- toto pravidlo se vztahuje pouze na samotnou tabulku; netýká se tlačítek, panelů ani dalších prvků nad tabulkou,
- rozdíl mezi sekcemi je pouze v datech: sekce **Super** zobrazuje pouze vybranou podmnožinu dat ze sekce **Videa**.


### Sdílené horní panely mezi párovými sekcemi

Stejné párování jako u tabulek platí také pro horní pracovní panel daných sekcí:

- **Girls** a **Oblíbené** budou mít stejný základ, rozložení a chování horního panelu,
- **Videa** a **Super** budou mít stejný základ, rozložení a chování horního panelu,
- mezi členy páru se mohou lehce lišit konkrétní tlačítka nad tabulkou; přesné rozdíly budou definovány později,
- budoucí společné změny horního panelu se mají promítat do obou členů daného páru, pokud uživatel výslovně neurčí výjimku.


### Rozdíly mezi párovými sekcemi

Párové sekce **Girls / Oblíbené** a **Videa / Super** se mají vizuálně a funkčně držet co nejblíže sobě.

Rozdíly budou pouze v tom, že:
- v levém navigačním menu bude jako aktivní zvýrazněna právě otevřená sekce,
- některá tlačítka nad tabulkou se mohou lehce lišit; budou definována později,
- v tabulce budou zobrazena jiná data podle otevřené sekce.

Samotný základ tabulky a její chování zůstává uvnitř každého páru stejné podle pravidel uvedených výše.


## 9. Vizuální reference jednotlivých sekcí

Dne 26. 9. 2026 byly dodány referenční screenshoty současného Latflixu pro jednotlivé desktopové sekce. Slouží jako vizuální podklad pro vzhled, rozložení a obsah dané sekce; neznamenají automaticky, že se beze změny přebírá každá současná funkce.

Mapování screenshotů:
- **Girls** – `docs/images/girls`
- **Přehled** – `docs/images/prehled`
- **Odkazy** – `docs/images/odkazy`
- **Videa** – `docs/images/videa`
- **Studia** – `docs/images/studia`
- **Stavy** – `docs/images/stavy`
- **Kvality** – `docs/images/kvality`
- **Tagy** – `docs/images/tagy`
- **Typy** – `docs/images/typy`

Screenshoty sekcí **Oblíbené** a **Super** nebyly samostatně dodány, protože jejich základ je svázaný s párovými sekcemi **Girls** a **Videa** podle pravidel této specifikace.

Při pozdějším doplňování konkrétních funkcí má písemná potvrzená specifikace přednost před starým screenshotem, pokud by si odporovaly.

---

## Pracovní pravidlo specifikace

Tento dokument je průběžná specifikace Latflixu 2.0. Každé další potvrzené upřesnění vzhledu, funkcí, GUI nebo chování aplikace se má průběžně zapracovat sem, aby existoval jeden konzistentní zdroj pravdy pro pozdější kompletní implementaci.
