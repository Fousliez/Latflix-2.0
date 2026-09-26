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



### Vzhled vícenásobného výběru řádků

Při výběru více sousedních řádků nesmí mezi vybranými řádky vznikat žádné drobné mezery ani optické oddělení.

Požadovaný princip:
- výběr může zůstat vizuálně podobný současnému zvýraznění / obrysu,
- sousední vybrané řádky však musí působit jako jeden souvislý celek,
- mezi nimi nesmí být viditelné malé bílé mezery ani dvojité horizontální linky,
- základní střídání bílá / světle šedá zůstává zachováno podle aktuálního pořadí řádků,
- sloupec zámku se nadále do vizuálního zvýraznění řádku nezahrnuje.

Latflix 5.36 může sloužit jako vizuální reference. Převzít lze vzhledový princip, ne automaticky starou implementaci. Pokud je starý kód technicky nečistý nebo komplikovaný, nový Latflix má stejného výsledku dosáhnout čistším způsobem.


### Vícenásobný výběr – bez zvýraznění cílové buňky

Při výběru více řádků tažením myši se po uvolnění levého tlačítka nesmí samostatně zvýraznit buňka, nad kterou bylo tlačítko uvolněno.

Požadované chování:
- výběr je vizuálně **řádkový**, ne buněčný,
- poslední / aktuální buňka může existovat interně kvůli navigaci, ale nesmí mít vlastní viditelný Excel-like rámeček, výplň ani jiné samostatné zvýraznění,
- po dokončení taženého výběru mají být vidět pouze vybrané řádky podle pravidel řádkového výběru,
- uvolnění myši nad konkrétní buňkou nesmí vytvořit druhou vizuální úroveň výběru,
- stejné pravidlo platí i při výběru více nesousedících řádků pomocí Ctrl nebo rozsahu pomocí Shift, pokud tabulka interně mění current index.

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


## 10. Sekce Girls / Oblíbené – horní panel

### Profilová fotografie herečky

V levé části horního panelu bude profilová fotografie herečky v přibližně portrétním poměru 9:16.

Chování:
- **jedno kliknutí levým tlačítkem** otevře dialog pro výběr obrázku,
- výchozí složka dialogu bude `/home/jirka/Plocha`; později bude tato cesta nastavitelná v Nastavení aplikace,
- **dvojklik levým tlačítkem** spustí výřez oblasti obrazovky; kurzor přejde do režimu výběru oblasti a uživatel může vyříznout obrázek i z jiného monitoru,
- po dokončení výřezu se vzniklý obrázek automaticky převezme a uloží jako profilová fotografie vybrané herečky do úložiště profilových obrázků,
- přesná interní implementace nástroje pro výřez se nyní neřeší; požadované je výsledné chování shodné s funkčním Latflixem 5.36,
- **pravé tlačítko** na fotografii otevře dialog pro smazání fotografie.

Důležité: při pozdější implementaci se nesmí dvojklik zaměnit za mazání fotografie. Mazání patří výhradně na pravé tlačítko; dvojklik je výhradně rychlý výřez obrazovky.

### Jméno, Oblíbené a základní údaje

- hvězdičkové hodnocení zobrazené ve starém Latflixu se do nové verze zatím nepřenáší a má být při návrhu ignorováno,
- ovládací prvek **Oblíbené** bude umístěn vpravo vedle jména herečky,
- pokud herečka **není v Oblíbených**, tlačítko/obdélník Oblíbené bude v běžném neaktivním vzhledu,
- pokud herečka **je v Oblíbených**, obdélník se vizuálně zvýrazní **žlutě**, podle dodané reference; text bude odpovídat stavu „★ V oblíbených“,
- změna stavu Oblíbené se musí v horním panelu projevit okamžitě bez nutnosti znovunačtení sekce.

Pod jménem herečky budou v jednom řádku zobrazeny základní údaje:
- **Věk:** tučný popisek `Věk:` a vedle něj aktuální hodnota,
- **Počet výskytů:** tučný popisek `Počet výskytů:` a vedle něj aktuální hodnota.

Rozložení a styl mají odpovídat referenčním screenshotům současného Latflixu.


### Pravá strana horního panelu – akce herečky

U pravého kraje horního panelu budou tři tlačítka **svisle pod sebou**, vzájemně zarovnaná do jednoho sloupce:

1. **Odkazy**
   - bude nahoře,
   - otevře přehled / dialog odkazů vztahujících se ke konkrétní aktuálně vybrané herečce.

2. **Detail**
   - bude uprostřed,
   - otevře editační dialog herečky,
   - dialog má vycházet z referenčního vzhledu současného Latflixu, ale může být upraven a zpřehledněn,
   - musí umožnit editaci všech běžných údajů herečky,
   - aliasy nemají být omezené jen na pevně dané tři položky; nová verze má umožnit přidat více aliasů, ideálně dynamicky tlačítkem typu **Přidat alias**.

3. **Zobrazit odkazy**
   - bude dole,
   - po kliknutí přepne aplikaci do sekce **Odkazy**,
   - v této sekci automaticky zobrazí pouze odkazy patřící aktuálně vybrané herečce,
   - implementace může použít interní filtr podle ID herečky, jména nebo předvyplnění vyhledávacího pole; důležité je výsledné chování, nikoliv konkrétní technický způsob,
   - po přechodu musí být jasně patrné, že jde o odkazy právě této herečky.

Všechna tři tlačítka mají být stejně zarovnaná a působit jako jeden kompaktní pravý ovládací sloupec.

### Hromadné přidání do Oblíbených

- přes tlačítko Oblíbené v horním detailu se pracuje vždy jen s právě vybranou herečkou,
- přidání více označených hereček do Oblíbených bude řešeno samostatným tlačítkem těsně nad tabulkou,
- přesná podoba a chování hromadného tlačítka budou doplněny zvlášť později,
- toto hromadné chování se nesmí míchat s tlačítkem Oblíbené v horním panelu.


### Dialog Odkazy u herečky

Tlačítko **Odkazy** v horním panelu otevře samostatné okno / dialog pro správu odkazů konkrétní aktuálně vybrané herečky.

#### Uložené odkazy nahoře

V horní části dialogu budou zobrazené již uložené odkazy herečky jako kompaktní položky.

Každá uložená položka bude obsahovat:
- název / platformu odkazu,
- vedle něj tlačítko **Editovat**,
- ještě více vpravo tlačítko **×** pro smazání.

Chování:
- kliknutí na **název odkazu nesmí otevřít web v prohlížeči**,
- kliknutí na název pouze zobrazí konkrétní uloženou URL adresu tohoto odkazu,
- **Editovat** otevře menší editační dialog pro úpravu daného odkazu,
- **×** otevře potvrzovací dialog typu „Chcete odkaz smazat?“ s volbou **Ano / Ne**,
- samotné otevření webu se případně bude řešit jiným explicitním ovládacím prvkem, ne kliknutím na název.

#### Přidání nových odkazů

Pod uloženými odkazy bude tabulková / řádková část pro přidávání nových odkazů.

Výchozí stav:
- zobrazí se **10 prázdných řádků**,
- každý řádek má vlevo pole **Zdroj / platforma**,
- vpravo pole **Adresa / URL**.

Pole **Zdroj / platforma**:
- ve výchozím stavu používá režim **Automaticky**,
- po zadání URL se aplikace pokusí podle adresy sama rozpoznat platformu / název odkazu, např. Facebook, Redgifs, Pornhub, Linktree apod.,
- pole bude zároveň rozbalovací a uživatel může automaticky zjištěnou hodnotu ručně změnit,
- seznam dostupných platforem se nebude definovat napevno v tomto dialogu,
- bude se načítat z centrálního seznamu / katalogu spravovaného v jiné části aplikace; přesná správa tohoto seznamu bude specifikována později v sekci Odkazy.

Pod řádky bude tlačítko **Přidat řádek**:
- každé kliknutí přidá přesně **jeden** nový prázdný řádek,
- nově přidaný řádek se chová stejně jako výchozích deset.

Rozložení a základní vizuální logika mají vycházet z dodané reference současného Latflixu, ale nový dialog má být čistý a bez zbytečného vizuálního balastu.


### Upřesnění tlačítek Detail a Zobrazit odkazy

#### Detail

Tlačítko **Detail** otevře editační dialog herečky podle dodané reference současného Latflixu.

Dialog má obsahovat stejné základní typy údajů jako na referenčním screenu, zejména:
- Jméno,
- Alias / aliasy,
- Typ,
- Sex,
- Nahota,
- Věk,
- Počet výskytů,
- Národnost,
- Hodnocení,
- Tagy,
- Sledování,
- Poslední kontrola,
- Obrázek,
- Poznámka,
- Datum přidání,
- Oblíbené,
- Poslední obrázek,
- Stav,
- Datum narození.

Požadavky:
- vzhled a rozložení mají vycházet z dodaného screenshotu,
- spodní část bude mít akce **Zrušit** a **Uložit**,
- aliasy nesmí být omezené pevně na tři položky; dialog musí umožnit přidávat další aliasy dynamicky,
- přesné názvy polí se mohou později sjednotit s datovým modelem nové verze, ale funkční rozsah má odpovídat referenci.

#### Zobrazit odkazy

Tlačítko **Zobrazit odkazy**:
- přepne aplikaci do sekce **Odkazy**,
- automaticky aktivuje filtr pro aktuálně vybranou herečku,
- výsledkem je zobrazení pouze odkazů patřících této herečce,
- preferovaný interní způsob je filtr podle stabilního ID herečky; jméno může být použito jen jako viditelný popisek filtru,
- po přechodu musí být zřejmé, pro kterou herečku jsou odkazy právě zobrazené.


### Modré odkazy v horním panelu Girls / Oblíbené

Zbývající prostor horního panelu mezi informacemi herečky a pravým sloupcem akčních tlačítek bude využit pro rychlé odkazy aktuálně vybrané herečky.

Každý typ uloženého odkazu herečky bude zobrazen jako samostatný **modrý obdélníkový prvek / štítek**:
- uvnitř bude název platformy / odkazu, např. `Facebook`, `Redgifs`, `Pornhub`,
- šířka prvku nebude pevná; přizpůsobí se tak, aby se celý text vešel bez zbytečného ořezávání,
- prvky budou klikací,
- kliknutí otevře skutečnou uloženou URL adresu daného odkazu ve výchozím prohlížeči.

#### Více odkazů stejného typu u jedné herečky

Pokud má jedna herečka více uložených URL stejné platformy:
- v horním panelu se platforma zobrazí pouze jednou,
- počet uložených URL se uvede v závorce, např. `Facebook (2)`,
- duplicity stejného typu u jedné herečky se tedy nesmí zobrazovat jako několik samostatných modrých prvků.

Pokud má štítek více URL stejné platformy, kliknutí na něj otevře **všechny uložené URL této platformy** pro danou herečku, každou samostatně ve výchozím prohlížeči.

#### Pořadí modrých prvků

Pořadí není abecední ani ručně pevně dané. Odkazy se řadí podle jejich celkového zastoupení v aplikaci:
- první bude platforma používaná u největšího počtu záznamů / hereček,
- následuje druhá nejčastější atd.,
- při výpočtu globálního pořadí se více URL stejné platformy u jedné herečky počítá pouze jako **jeden výskyt**,
- duplicity u jedné herečky tedy zvyšují pouze číslo v závorce u jejího štítku, ale nesmějí uměle zvyšovat globální popularitu dané platformy.

Příklad: pokud má jedna herečka dvě adresy Facebooku, pro globální pořadí se Facebook u této herečky započítá jednou, ale její štítek bude `Facebook (2)`.

#### Rozložení

- prvky se skládají zleva doprava podle uvedeného pořadí,
- po zaplnění dostupné šířky pokračují na druhém řádku,
- v horním panelu se zobrazí maximálně **dva řádky** těchto modrých odkazových prvků,
- výška horního panelu zůstává pevná; odkazy nesmějí panel roztahovat,
- vzhled má odpovídat modrým odkazovým obdélníkům z referenčních screenshotů současného Latflixu.


### Společná lišta tlačítek a filtrů nad tabulkou

Nad hlavní tabulkou bude v datových sekcích společná ovládací lišta podle dodané reference.

Základní pravidlo:
- stejný **typ prvků, vzhled, rozměrová logika, zarovnání a základní chování** bude používán ve všech sekcích s tabulkou,
- sekce **Přehled** tuto lištu mít nebude,
- jednotlivé sekce mohou mít jiný počet tlačítek, jiné popisky, jiné konkrétní akce a jinou sadu filtrů,
- tyto rozdíly se budou definovat zvlášť pro každou sekci,
- společná vizuální a interakční logika ale zůstává jednotná napříč aplikací.

Pro sekci **Girls / Oblíbené** má lišta vizuálně vycházet z dodané reference a počítá se zde s prvky typu:
- Přidat,
- Smazat,
- Hromadné akce,
- vyhledávací pole,
- doplňkové malé akční tlačítko / ikona,
- rozbalovací filtry jako Národnost, Typ, Stav, Hodnocení, Sex, Nahota.

Konkrétní chování jednotlivých prvků Girls / Oblíbené bude doplněno v následujících bodech specifikace.

Důležité architektonické pravidlo:
- tato lišta se má implementovat jako **sdílená komponenta / sdílená logika**, nikoliv znovu zvlášť pro každou sekci,
- sekce pouze dodá konfiguraci popisků, viditelnosti, pořadí a konkrétních akcí / filtrů.


### Girls / Oblíbené – tlačítko Přidat

První prvek v liště nad tabulkou je dělené tlačítko **Přidat**.

Chování:
- levá, větší část tlačítka přidá **jeden nový řádek**,
- pravá, menší část obsahuje šipku a otevře malou nabídku,
- nabídka obsahuje:
  - **Přidat 5 řádků**
  - **Přidat 10 řádků**

Pravidla pro nové řádky:
- nové řádky se vždy vloží **nahoru do tabulky**,
- každý nově přidaný řádek bude při vytvoření vždy **odemčený**,
- hromadné přidání 5 nebo 10 řádků se řídí stejnými pravidly jako přidání jednoho řádku,
- přidané řádky se nesmějí automaticky přesunout dolů kvůli třídění dřív, než uživatel dokončí jejich zadání; přesné chování při aktivním třídění bude případně ještě upřesněno.


### Automatické odstranění zcela prázdných nových řádků – globální pravidlo

Toto pravidlo platí **napříč celou aplikací** ve všech tabulkových sekcích:

- pokud je nově přidaný řádek **zcela prázdný** a uživatel:
  - opustí aktuální sekci, nebo
  - zavře aplikaci,
  bude tento prázdný řádek automaticky odstraněn,
- odstranění se týká pouze řádku, který neobsahuje žádnou uživatelskou hodnotu ani jiná skutečná data,
- jakmile uživatel do řádku zadá jakoukoli skutečnou hodnotu, řádek se nepovažuje za zcela prázdný a nesmí být tímto pravidlem smazán,
- pravidlo je společné pro všechny sekce s tabulkami a nemá se implementovat zvlášť pro každou sekci.


### Girls / Oblíbené – nové řádky jsou skutečně prázdné

Upřesnění tlačítka **Přidat**:
- po vytvoření je nový řádek **zcela prázdný**,
- žádný sloupec nesmí mít automaticky předvyplněnou hodnotu,
- jediný automatický stav nového řádku je, že je **odemčený**,
- toto pravidlo platí stejně pro přidání 1, 5 i 10 řádků.

### Girls / Oblíbené – tlačítko Smazat

Druhé tlačítko v liště nad tabulkou je **Smazat**.

Chování:
- pokud je označen jeden odemčený řádek, tlačítko vyvolá potvrzovací dialog a po potvrzení řádek smaže,
- pokud je označeno více odemčených řádků, tlačítko vyvolá potvrzovací dialog a po potvrzení smaže všechny označené řádky,
- potvrzení je povinné vždy, bez ohledu na počet označených řádků,
- zamčený řádek **nelze smazat**,
- pokud výběr obsahuje zamčené řádky, tyto řádky se nesmějí odstranit,
- přesné znění potvrzovacího dialogu může později uvádět počet řádků, které budou skutečně smazány.


### Girls / Oblíbené – Hromadné akce

Třetí tlačítko v liště nad tabulkou je **Hromadné akce**. Otevře nabídku s položkami:

- **Přidat do Oblíbených**
- **Odebrat z Oblíbených**
- **Hromadně přidat odkazy**

#### Přidat / odebrat z Oblíbených

- akce se použije na všechny aktuálně označené herečky,
- **Přidat do Oblíbených** přidá všechny označené herečky do Oblíbených,
- **Odebrat z Oblíbených** vyžaduje potvrzovací dialog před provedením,
- zamčenost řádku sama o sobě nemění členství v Oblíbených; jde o samostatnou hromadnou akci nad vybranými záznamy.

#### Hromadně přidat odkazy

Tato akce otevře samostatný dialog. Počet řádků v dialogu bude přesně odpovídat počtu označených hereček.

Každý řádek představuje jednu konkrétní herečku a obsahuje tři sloupce:

1. **Herečka**
   - zobrazí jméno herečky,
   - hodnota je pouze pro čtení a nelze ji editovat.

2. **Zdroj / platforma**
   - funguje stejně jako pole Zdroj / platforma v dialogu **Odkazy** z horního panelu,
   - ve výchozím stavu se aplikace pokusí podle zadané URL automaticky rozpoznat platformu / název odkazu,
   - uživatel může automaticky rozpoznanou hodnotu ručně změnit přes rozbalovací seznam,
   - seznam dostupných platforem se načítá ze stejného centrálního katalogu jako v běžném dialogu Odkazy,
   - v jednom hromadném dialogu mohou být různé platformy zároveň; není zde žádný společný typ odkazu pro celý dialog.

3. **URL**
   - uživatel zadá konkrétní adresu odkazu pro danou herečku.

Příklad použití: v jednom dialogu lze třem označeným herečkám přidat Instagram a dalším třem Facebook; platforma se určuje po jednotlivých řádcích, automaticky podle URL, s možností ruční opravy.


### Girls / Oblíbené – pole Hledání

Dalším prvkem v liště nad tabulkou je fulltextové pole **Hledání**.

Chování:
- hledání funguje vždy pouze v aktuální sekci,
- prohledává všechny buňky všech řádků v dané tabulce,
- řádek se zobrazí, pokud hledaný text obsahuje alespoň jedna jeho buňka,
- porovnání je **case-insensitive**; velká a malá písmena se nerozlišují,
- hledání má filtrovat průběžně podle obsahu pole,
- ostatní sekce nejsou hledáním ovlivněné.

Vpravo od pole Hledání bude malé tlačítko s ikonou **koše**:
- kliknutí vymaže celý obsah pole Hledání,
- současně zruší fulltextový filtr,
- tabulka se vrátí do stavu před aktivací hledání, při zachování ostatních nezávislých nastavení a filtrů dané sekce.


### Girls / Oblíbené – sloupcové filtry nad tabulkou

Za polem Hledání následují filtrační prvky:

- **Národnost**
- **Typ**
- **Stav**
- **Sex**
- **Nahota**

Filtr **Hodnocení** zde nebude.

Všechny tyto filtry používají stejnou společnou logiku:
- každý filtr je navázán na stejnojmenný sloupec v tabulce,
- po otevření nabídky lze vybrat konkrétní hodnotu,
- tabulka se následně vyfiltruje tak, aby zůstaly pouze řádky, které mají ve svém příslušném sloupci zvolenou hodnotu,
- názvy filtrů a názvy sloupců jsou přímo svázané; například filtr **Národnost** filtruje sloupec **Národnost**, filtr **Stav** sloupec **Stav** atd.,
- všechny tyto filtry mají stejný vzhled a interakční chování,
- konkrétní nabídka hodnot se odvozuje od příslušného sloupce / jeho povolených hodnot.

Filtry mohou fungovat současně s fulltextovým hledáním; výsledná tabulka musí respektovat všechny právě aktivní podmínky.


### Girls / Oblíbené – zdroj hodnot pro filtry

Filtry **Sex** a **Nahota** mají pevně danou nabídku hodnot:

- **Ano**
- **Ne**
- **Asi ne**
- **Asi ano**
- **Zjistit**

Filtry **Národnost** a **Typ** nemají hodnoty napevno v kódu.

Jejich nabídka se dynamicky načítá z odpovídajících vedlejších sekcí v levém menu:
- **Národnost** → sekce **Národnosti**
- **Typ** → sekce **Typy**

Filtr **Stav** v sekcích **Girls / Oblíbené** je naopak pevně daný a obsahuje:
- **Aktivní**
- **Neaktivní**
- **Smazaná**

Sekce **Stavy** v levém menu se tedy nepoužívá pro herečky. Je určena pro stavové hodnoty videí a dalších navázaných video částí aplikace.

Do levého menu mezi vedlejší sekce se proto přidá nová položka:

- **Národnosti**

Tyto pomocné sekce budou sloužit jako centrální katalog hodnot pro příslušné sloupce a filtry. Jejich detailní struktura se specifikuje později; předběžně se počítá s jednoduchými tabulkami, pravděpodobně s jedním hlavním sloupcem.

Pravidla dynamických nabídek:
- počet položek v nabídce filtru **Národnost** nebo **Typ** odpovídá aktuálnímu počtu hodnot / řádků v příslušné pomocné sekci,
- text každé položky filtru odpovídá hodnotě uložené v příslušném řádku pomocné sekce,
- přidání, přejmenování nebo odstranění hodnoty v pomocné sekci se musí projevit i v nabídce navázaného filtru,
- tyto katalogy se mají používat centrálně i pro další místa v aplikaci, kde se vybírá Národnost nebo Typ, aby nevznikaly různé nesynchronizované seznamy.


### Girls / Oblíbené – pořadí položek ve filtru Národnost

Po otevření filtru **Národnost** se nabídka rozdělí na dvě části podle četnosti použití národností u hereček.

Hlavní část nabídky:
- zobrazí **10 nejčastěji použitých národností**,
- pořadí je sestupně podle počtu hereček, které mají danou národnost,
- nejčastější národnost je první.

Pod touto hlavní desítkou bude vizuální oddělení:
- tenký gradient / jemný oddělovací prvek,
- pod ním položka / tlačítko **Další**.

Po otevření **Další**:
- zobrazí se všechny zbývající národnosti,
- i ty budou seřazené sestupně podle četnosti,
- začínají tedy od 11. místa globálního pořadí.

Zdroj hodnot zůstává sekce **Národnosti**; četnost se ale počítá podle skutečného použití hodnot u záznamů v sekci Girls / Oblíbené.


### Girls / Oblíbené – tlačítko Vyčistit

Na úplně pravé straně lišty nad tabulkou bude ve stejné výšce jako ostatní prvky samostatné tlačítko **Vyčistit**.

Chování:
- tlačítko **Vyčistit** vymaže obsah pole Hledání,
- zároveň zruší **všechny aktivní filtry** v této sekci,
- po použití se tabulka vrátí do běžného nevyfiltrovaného stavu sekce,
- tlačítko je od ostatních ovládacích prvků vizuálně oddělené tím, že je zarovnané úplně doprava.

Rozdíl oproti malé ikoně koše vedle pole Hledání:
- **koš vedle Hledání** smaže pouze text v poli Hledání a zruší pouze fulltextový filtr,
- **Vyčistit** smaže hledání a zároveň zruší i všechny aktivní sloupcové filtry.

Vizuální umístění má odpovídat dodané referenci: tlačítko **Vyčistit** je na pravém okraji stejného řádku ovládací lišty.


### Girls / Oblíbené – filtry Obličej a Profilovka

Vpravo od filtru **Nahota** budou ještě dva filtry:

#### Obličej

Filtr **Obličej** je navázán na stejnojmenný sloupec **Obličej** v tabulce a má pevně dané hodnoty:

- **Ano**
- **Asi ano**
- **Asi ne**
- **Ne**
- **Zjistit**

Po výběru hodnoty se tabulka vyfiltruje podle hodnoty ve sloupci Obličej.

#### Profilovka

Filtr **Profilovka** nemá vlastní sloupec v tabulce.

Má pouze dvě možnosti:
- **Ano**
- **Ne**

Filtruje podle existence profilového obrázku herečky:
- **Ano** = zobrazí pouze herečky, které mají uloženou profilovou fotografii,
- **Ne** = zobrazí pouze herečky, které profilovou fotografii nemají.

Tento filtr tedy pracuje přímo s datem / příznakem existence profilové fotografie, nikoliv s hodnotou v samostatném viditelném sloupci tabulky.

Filtry **Obličej** a **Profilovka** se mohou kombinovat s fulltextovým hledáním a ostatními aktivními filtry.


### Girls / Oblíbené – priorita umístění filtrů Obličej a Profilovka

Referenční screenshoty mohou zobrazovat prvky **Obličej** a **Profilovka** na jiném místě.

Pro Latflix 2.0 platí výslovně:
- filtr **Obličej** bude v liště nad tabulkou **vpravo od filtru Nahota**,
- filtr **Profilovka** bude hned **vpravo od filtru Obličej**,
- toto umístění má přednost před polohou těchto prvků na starých screenshotových referencích.

Screenshoty zde slouží pouze jako vizuální reference vzhledu, nikoliv jako závazná reference jejich pozice.


### Girls / Oblíbené – pořadí a názvy sloupců tabulky

Výchozí pořadí datových sloupců v sekcích **Girls / Oblíbené** bude:

1. **Jméno**
2. **Obličej**
3. **Sex**
4. **Typ**
5. **Nahota**
6. **Věk**
7. **Národnost**
8. **Tagy**
9. **Sledování**
10. **Posl. kontrola**
11. **Počet výskytů**
12. **Pozn.**
13. **Stav**

Toto pořadí se týká datových sloupců; systémové sloupce pro zámek a číslo řádku zůstávají vlevo podle globálních pravidel tabulky.

Po odemknutí záhlaví:
- sloupce lze přesouvat tažením,
- sloupce lze přejmenovat,
- změny pořadí a názvů se mají pamatovat podle obecných pravidel konfigurace tabulky.

Výchozí názvy a pořadí uvedené výše slouží jako počáteční stav nové instalace / resetu rozložení.


### Girls / Oblíbené – editační režim nově přidaného řádku

Po přidání nového řádku se tento řádek automaticky otevře v **editačním režimu**.

Chování klávesy **Enter**:
- stisknutí Enteru potvrdí / ukončí editaci aktuálního řádku,
- následně se aktivní pozice přesune na **následující řádek**,
- tento následující řádek se automaticky otevře v editačním režimu,
- automatické otevření dalšího řádku v editačním režimu nastane **pouze při potvrzení Enterem**.

Jinými způsoby opuštění nebo změny výběru řádku se tento automatický přechod do editačního režimu dalšího řádku nespouští.



### Enter v textové editaci – právě jeden řádek

Jedno fyzické stisknutí klávesy Enter smí ukončit editaci a posunout editaci **právě o jeden řádek dolů** ve stejném sloupci.

Implementační poznámka:
- obsluha Enteru musí reagovat pouze jednou na jedno stisknutí (typicky jen na KeyPress),
- nesmí se zpracovat znovu při KeyRelease ani jinou druhou cestou,
- nesmí tak dojít k přeskočení ob řádek.

### Girls / Oblíbené – chování našeptávače a ukončení editace myší

Při editaci řádku, zejména pole **Jméno**, platí:

- pokud uživatel vybere hodnotu z našeptávače / automatického doplnění, hodnota se vloží do buňky,
- tím se ale **editační režim neukončí**,
- kurzor zůstane aktivní v daném editačním poli na konci vloženého jména,
- uživatel může bez dalšího klikání pokračovat v editaci.

Pokud uživatel během textové editace klikne myší do jiné buňky:
- aktuálně editovaná hodnota se nejprve uloží / potvrdí,
- další chování se řídí globálním pravidlem **plynulého předávání editačního režimu mezi buňkami**,
- pokud je cílová buňka odemčená a editovatelná, její editor / výběrový prvek se aktivuje okamžitě jediným kliknutím,
- pokud je cílová buňka zamčená nebo needitovatelná, stávající editace se pouze ukončí.

Automatický přechod na **následující řádek** zůstává vyhrazený pro potvrzení klávesou **Enter**.


### Girls / Oblíbené – našeptávač v poli Hledání

Pole **Hledání** v sekcích **Girls** a **Oblíbené** bude mít našeptávač jmen hereček.

Řazení a výběr položek:
- základní pořadí vychází z **počtu výskytů herečky ve videích**, od nejčastějších,
- po začátku psaní se zobrazují pouze odpovídající herečky,
- shoda od začátku hlavního jména nebo aliasu má přednost před shodou uprostřed textu,
- uvnitř stejné skupiny shod rozhoduje:
  1. vyšší počet výskytů,
  2. následně abecední pořadí,
- v sekci **Oblíbené** se v našeptávači zobrazují pouze herečky, které jsou v Oblíbených.

Vzhled popupu:
- větší písmo než běžný drobný systémový našeptávač,
- vyšší řádky pro pohodlné klikání,
- řádek pod kurzorem myši se výrazně zvýrazní modře, aby bylo před kliknutím jasné, která položka bude vybrána.

Toto chování odpovídá již hotové funkci v předchozí verzi Latflixu ze dne **28. 8. 2026** a má být zachováno i v Latflixu 2.0.


### Globální tabulkové chování – výběr a kopírování textu při editaci

V aktivním textovém editoru buňky tabulky musí být možné:

- myší označit libovolnou část textu,
- označení musí fungovat standardním způsobem jako v běžném textovém poli,
- označený text lze zkopírovat pomocí **Ctrl+C**,
- kopíruje se pouze aktuálně označená část textu.

Toto chování platí obecně pro editovatelné textové buňky v tabulkách napříč aplikací.


### Globální tabulkové chování – vložení primárního výběru prostředním tlačítkem

V aktivním editačním režimu textové buňky musí být na Linuxu zachováno běžné systémové chování primárního výběru:

- text označený myší v jiné aplikaci nebo jiném textovém poli lze vložit do právě editované buňky kliknutím **prostředního tlačítka myši**,
- vložení proběhne na aktuální pozici textového kurzoru,
- tato akce nesmí ukončit editační režim buňky,
- funkce má být dostupná ve všech editovatelných textových buňkách napříč aplikací,
- klasické Ctrl+C / Ctrl+V zůstává současně zachováno.


### Globální tabulkové chování – aktivace editačního režimu myší

Pro sloupec **Jméno** v sekcích Girls / Oblíbené a obecně pro všechny sloupce, které budou označené jako **editovatelné**, platí:

- **jedno kliknutí** do řádku / buňky pouze označí řádek podle běžných pravidel výběru,
- jedno kliknutí samo o sobě nesmí zapnout textový editační režim buňky,
- **dvojklik** do editovatelné buňky zapne editační režim této buňky,
- po aktivaci dvojklikem fungují běžné textové operace včetně výběru části textu, Ctrl+C / Ctrl+V a na Linuxu vložení primárního výběru prostředním tlačítkem,
- toto pravidlo platí jednotně pro všechny sloupce, které budou ve specifikaci nebo konfiguraci označené jako editovatelné.

Výjimka z aktivace dvojklikem:
- nově přidaný řádek se otevře v editačním režimu automaticky podle již definovaného pravidla,
- následující řádek se může otevřít v editačním režimu automaticky po potvrzení předchozího řádku klávesou Enter.


### Girls / Oblíbené – editace výběrem z nabídky

V tabulce Girls / Oblíbené se následující sloupce neupravují volným textem, ale výběrem z nabídky:

- **Obličej**
- **Sex**
- **Typ**
- **Nahota**

U odemčeného řádku se příslušná nabídka otevře už **jedním kliknutím** do výběrové buňky; nejde o klasický textový editační režim.
Toto chování se odlišuje od běžně editovatelných textových buněk, které se při neaktivním editačním režimu otevírají až **dvojklikem**.

Zdroj hodnot:
- **Obličej**: pevné hodnoty `Ano`, `Asi ano`, `Asi ne`, `Ne`, `Zjistit`,
- **Sex**: pevné hodnoty `Ano`, `Ne`, `Asi ne`, `Asi ano`, `Zjistit`,
- **Nahota**: pevné hodnoty `Ano`, `Ne`, `Asi ne`, `Asi ano`, `Zjistit`,
- **Typ**: dynamické hodnoty načítané z pomocné sekce **Typy**.

Výběr hodnoty z nabídky okamžitě zapíše a uloží hodnotu do buňky. Tyto buňky tedy používají výběrový mechanismus namísto běžného textového editačního režimu.


### Girls / Oblíbené – sloupec Věk

Sloupec **Věk** bude podporovat dva způsoby zadání podle hodnoty:

- pokud uživatel zadá číslo **1–100**, bere se jako přímo zadaný věk a zobrazí se beze změny,
- pokud uživatel zadá číslo **větší než 100**, bere se jako **rok narození** (např. 1992, 2004, 1986) a aplikace z něj vypočítá zobrazovaný věk.

Při zadání roku narození:
- zobrazovaný věk se vypočítá podle aktuálního kalendářního roku,
- například v roce 2026: `1992 → 34`, `2004 → 22`, `1986 → 40`,
- protože je zadán pouze rok a nikoli přesné datum narození, jde o věk odvozený z roku narození,
- původní rok narození se má interně zachovat jako zdrojová hodnota, aby se vypočítaný věk mohl v dalších letech automaticky aktualizovat,
- uživatel tedy nemusí věk ručně každý rok opravovat.

Sloupec zůstává editovatelný podle obecných pravidel tabulky.


### Girls / Oblíbené – zobrazení a editace hodnoty ve sloupci Věk

Sloupec **Věk** rozlišuje mezi zdrojovou hodnotou a zobrazovanou hodnotou.

#### Mimo editační režim
- pokud byla zadána přímo hodnota věku `1–100`, zobrazuje se tato hodnota,
- pokud byl zadán rok narození, např. `1992`, `2004` nebo `1986`, zobrazuje se **vypočítaný věk**, nikoliv rok narození,
- běžný pohled tabulky tedy vždy ukazuje věk.

#### V editačním režimu
Po dvojkliku do buňky:
- pokud byla původně zadána hodnota věku, editor zobrazí tuto původní hodnotu, např. `20`,
- pokud byl původně zadán rok narození, editor zobrazí právě tento rok, např. `1992`,
- uživatel tedy vždy edituje původní zdrojovou hodnotu, ne pouze právě vypočítaný zobrazovaný věk.

Příklad:
- zdrojová hodnota `20` → mimo editaci se zobrazí `20`, v editaci `20`,
- zdrojová hodnota `1992` → mimo editaci se zobrazí aktuálně vypočítaný věk, v editaci `1992`.

Toto chování je nutné zachovat tak, aby bylo možné kdykoliv rozlišit ručně zadaný věk od roku narození.


### Globální tabulkové chování – plynulé předávání editačního režimu mezi buňkami

Toto pravidlo platí **napříč celou aplikací** pro všechny tabulkové sekce a všechny typy editovatelných buněk.

Pokud je právě aktivní editační režim v jedné buňce a uživatel klikne myší do jiné buňky:

- aktuální editace se nejprve korektně potvrdí / ukončí,
- pokud je cílová buňka **odemčená a editovatelná**, její editor se **okamžitě aktivuje jediným kliknutím**,
- není tedy nutný další dvojklik, protože aplikace už je v aktivním editačním toku,
- pokud je cílová buňka zamčená nebo needitovatelná, pouze se ukončí stávající editační režim a nový editor se neotevře.

Toto chování platí mezi libovolnými typy editorů, například:
- textové pole → textové pole,
- textové pole → výběrové pole,
- výběrové pole → textové pole,
- výběrové pole → výběrové pole.

Příklad:
- je aktivní editace ve sloupci **Jméno** a bliká textový kurzor,
- uživatel jednou klikne do odemčené buňky **Obličej**,
- editace Jména se ukončí a nabídka Obličej se okamžitě otevře.

Další příklad:
- nabídka **Obličej** je otevřená a uživatel z ní nic nevybere,
- klikne do odemčené buňky **Sex**,
- nabídka Obličej se zavře bez změny hodnoty a okamžitě se otevře nabídka Sex.

Toto pravidlo je výjimkou z běžného chování „jedno kliknutí = pouze označení řádku“. Toto běžné pravidlo platí tehdy, když před kliknutím **není aktivní žádný editační režim**.



### Plynulé předání mezi výběrovými buňkami

Pokud je právě otevřená nabídka výběrové / dropdown buňky a uživatel **jednou klikne do jiné výběrové buňky**, nesmí být potřeba druhý klik.

Požadované chování:
- první klik na jinou výběrovou buňku ukončí / zavře předchozí otevřenou nabídku,
- **tím samým klikem** se okamžitě otevře nabídka nové cílové výběrové buňky,
- nesmí vzniknout mezikrok, kdy první klik pouze zavře starou nabídku a druhý teprve otevře novou,
- chování má být plynulé stejně jako již definované předání z textové editace do výběrové buňky,
- pravidlo platí globálně pro všechny tabulky a všechny výběrové / dropdown buňky, pokud není u konkrétní sekce výslovně stanoveno jinak.


### Výběrové buňky – bez viditelné šipky

Výběrové / dropdown buňky v tabulkách nesmí v klidovém ani editačním stavu zobrazovat žádnou standardní rozbalovací šipku / indikátor comboboxu vpravo.

Požadované chování:
- buňka má vizuálně působit jako běžná tabulková buňka,
- kliknutí stále otevře výběrovou nabídku podle stávajících pravidel,
- funkce dropdownu se tím nemění, mění se pouze jeho vzhled,
- žádný malý trojúhelník, šipka ani pravý comboboxový ovladač nesmí být vidět,
- pravidlo platí globálně pro všechny výběrové / dropdown buňky ve všech tabulkách, pokud není u konkrétní sekce výslovně stanoveno jinak.

### Globální tabulkové chování – rychlé kopírování hlavního názvu ze zamčeného řádku

U zamčených řádků bude dvojklik do hlavního textového sloupce sloužit jako rychlé kopírování hodnoty.

Platí zejména pro:
- **Girls / Oblíbené** → sloupec **Jméno**,
- **Videa / Super** → sloupec **Název videa**.

Chování:
- pokud je řádek zamčený, **jedno kliknutí** pouze označí řádek podle běžných pravidel výběru,
- pokud je řádek zamčený a uživatel **dvakrát klikne** do příslušné hlavní textové buňky, její text se okamžitě zkopíruje do systémové schránky,
- editační režim se u zamčeného řádku neotevírá,
- po zkopírování se krátce zobrazí malé nenápadné potvrzení **„Zkopírováno“**,
- vizuální styl a chování tohoto potvrzení mají odpovídat současnému Latflixu, kde tato funkce již existuje a uživateli vyhovuje,
- u odemčeného řádku se dvojklik nadále používá pro vstup do editačního režimu u editovatelných buněk.

Tato logika se má implementovat sdíleně tak, aby ji bylo možné použít i u dalších hlavních textových sloupců, pokud budou později označeny pro stejné chování.


### Girls / Oblíbené – sloupec Tagy

Sloupec **Tagy** používá výběrový popup podobný dodané referenci.

Chování a vzhled:
- popup zobrazuje existující tagy jako **barevné štítky**,
- barva každého štítku se bere z centrální sekce **Tagy**,
- v tomto popupu se tagy pouze vybírají / odebírají pro konkrétní herečku,
- správu seznamu tagů a jejich barev řeší samostatná sekce **Tagy**.

V popupu nebudou:
- pole **Nový tag**,
- tlačítko **+** pro přidání nového tagu,
- tlačítko **Smazat**.

Dole zůstanou pouze:
- **Zrušit**
- **Uložit**

### Girls / Oblíbené – sloupce Sledování, Posl. kontrola a Pozn.

#### Sledování
- sloupec **Sledování** zobrazuje celkový počet uložených odkazů u dané herečky,
- počítá se každý uložený odkaz samostatně,
- pokud má herečka například dva různé uložené odkazy na Instagram, oba se započítají,
- hodnota je tedy počet konkrétních URL, nikoliv počet unikátních platforem.

#### Posl. kontrola
- sloupec **Posl. kontrola** je editovatelný,
- používá běžný textový editor,
- bez našeptávače / automatického doplňování.

#### Pozn.
- sloupec **Pozn.** je editovatelný,
- používá běžný textový editor,
- bez našeptávače / automatického doplňování.


### Girls / Oblíbené – sloupec Stav

Sloupec **Stav** je editovatelný výběrem z nabídky.

Nabídka obsahuje pevně dané hodnoty:
- **Aktivní**
- **Neaktivní**
- **Smazaná**

Po aktivaci editačního režimu se otevře nabídka těchto stavů a zvolená hodnota se zapíše do buňky.


### Girls / Oblíbené – Národnost, Počet výskytů a Sledování

#### Národnost
- sloupec **Národnost** je editovatelný výběrem z nabídky,
- logika je stejná jako u sloupce **Typ**,
- nabídka se dynamicky načítá ze sekce **Národnosti**,
- po dvojkliku do odemčené buňky se otevře nabídka dostupných národností,
- zvolená hodnota se zapíše do buňky.

#### Počet výskytů
- sloupec **Počet výskytů** je automaticky vypočítávaný,
- nelze jej ručně editovat,
- hodnota odpovídá počtu videí / výskytů, ve kterých je daná herečka evidovaná.

#### Sledování
- sloupec **Sledování** je automaticky vypočítávaný,
- nelze jej ručně editovat,
- hodnota odpovídá celkovému počtu uložených URL u herečky,
- každý konkrétní odkaz se počítá samostatně, včetně více odkazů stejné platformy.


### Girls / Oblíbené – doplnění chování buněk a řazení

#### Výběrové buňky
Pro výběrové buňky, např. **Obličej, Sex, Typ, Nahota, Národnost, Stav**:
- nejde o klasický textový editační režim,
- v odemčeném řádku se nabídka otevře už **prvním kliknutím** do buňky,
- po výběru hodnoty se zvolená hodnota ihned uloží do buňky,
- tím je akce hotová,
- klávesa **Enter** u těchto výběrových buněk nemá žádnou speciální funkci,
- klávesa **Esc** zde ani obecně v tabulce nespouští žádnou speciální akci.

#### Tagy – budoucí nastavení zobrazení
- způsob zobrazení tagů přímo v buňce se bude řešit později,
- v nastavení aplikace bude volba, zda se tagy v tabulce zobrazují:
  - textově,
  - nebo jako barevné štítky.

#### Posl. kontrola
- zůstává volný editovatelný text bez pevného formátu,
- žádné vynucené datum ani validace formátu se nyní nepoužívá.

#### Pozn.
- běžně se zobrazuje jako jednořádková hodnota v tabulce,
- dvojklik otevře větší editační pole pro pohodlnější úpravu poznámky.

#### Řazení sloupců kliknutím na záhlaví
- řazení kliknutím na záhlaví je aktivní u **všech datových sloupců**,
- opakovaným kliknutím se přepíná mezi vzestupným a sestupným řazením,
- aktuální stav řazení se **neukládá natrvalo** a po novém spuštění / návratu se nemusí obnovovat,
- řazení je pouze dočasný stav aktuálního zobrazení.


### Girls / Oblíbené – průměrný věk ve stavovém řádku

Pouze v sekcích **Girls** a **Oblíbené** se ve spodním stavovém řádku přibližně uprostřed zobrazí údaj o **průměrném věku hereček**.

Chování:
- hodnota se počítá z aktuálně zobrazené sady hereček po použití sloupcových filtrů,
- změna filtrů tedy průměrný věk okamžitě přepočítá,
- fulltextové pole **Hledání** tento údaj neovlivňuje,
- při použití hledání se tedy průměr počítá stále z dat odpovídajících filtrům, nikoliv jen z řádků dočasně zobrazených hledáním,
- údaj se nezobrazuje v ostatních sekcích aplikace.

Umístění:
- přibližně střed spodního stavového řádku,
- tak, aby nekolidoval s levým počtem záznamů ani pravými ovládacími prvky stavového řádku.


### Vizuální upřesnění tabulek a lišty nad tabulkou

Nové společné vizuální pravidlo pro Latflix 2.0:

#### Střídání barev řádků
- střídání barev řádků bude **bílá / světle šedá**,
- dříve uvažovaná kombinace světle modré / světle zelené se ruší,
- střídání se nadále řídí aktuálním pořadím zobrazených řádků.

#### Šipky v záhlaví a na tlačítkách
- po kliknutí na název sloupce se v záhlaví **nesmí zobrazovat šipka řazení**,
- řazení kliknutím na záhlaví zůstává funkční oběma směry, pouze bez viditelného indikátoru šipkou,
- běžná tlačítka v liště nad tabulkou rovněž nemají zobrazovat šipku / rozbalovací indikátor,
- výjimkou je pouze dělené tlačítko **Přidat**, kde je šipka samostatnou pravou částí tlačítka podle již definovaného chování.

#### Výška prvků v liště nad tabulkou
- všechna tlačítka v liště nad tabulkou mají být stejně vysoká jako pole **Hledání**,
- společná výška se má držet jednotně napříč sekcemi, které tuto lištu používají.


### Lišta nad tabulkou – šířka tlačítek a text

Pro tlačítka v liště nad tabulkou platí:
- text tlačítka se musí zobrazit **vždy celý**, bez zkrácení nebo ořezu,
- šířka tlačítka se proto přizpůsobí délce jeho textu,
- uvnitř tlačítka musí zůstat alespoň minimální vodorovná rezerva odpovídající přibližně **jedné mezeře před textem a jedné mezeře za textem**,
- větší rezerva je v pořádku, pokud to odpovídá vzhledu a rozložení,
- toto pravidlo neznamená doslovné vkládání znaků mezery do popisku, ale minimální vnitřní odsazení tlačítka.


### Levé menu – zvýraznění aktivní sekce

- tlačítko právě vybrané / aktivní sekce v levém menu bude mít **lehce odlišnou barvu** než ostatní tlačítka,
- zvýraznění má být jemné, nikoliv křiklavé,
- účelem je na první pohled ukázat, ve které sekci se uživatel právě nachází,
- ostatní rozměry, typografie a základní styl tlačítka zůstávají stejné.


### Globální tabulkový základ napříč sekcemi

Tabulky v ostatních datových sekcích budou vycházet ze stejného společného základu jako **Girls / Oblíbené**.

Společná bude zejména:
- logika výběru řádků,
- zámky řádků,
- číslování,
- řazení,
- střídání barev,
- aktivace editovatelných buněk,
- výběrové buňky,
- předávání aktivního editačního toku,
- chování Enter / Esc podle typu buňky,
- kopírování hlavního textového pole u zamčených řádků tam, kde bude určeno,
- našeptávače tam, kde je daný sloupec používá,
- filtry,
- fulltextové hledání,
- společná ovládací lišta nad tabulkou,
- společná vizuální a interakční logika.

Jednotlivé sekce se budou lišit především:
- názvy sloupců,
- pořadím sloupců,
- typem sloupce / editoru,
- povolenými hodnotami,
- zdrojem hodnot pro výběrové seznamy,
- konkrétními filtry,
- případnými sekčně specifickými akcemi.

Cílem je jedna sdílená tabulková komponenta / logika s konfigurací podle sekce, nikoliv samostatná implementace tabulky pro každou sekci.



### Výchozí rozsah pravidel chování tabulek

Pokud uživatel při ladění chování tabulky, buněk, výběru, editace, myši, klávesnice, řazení, zvýraznění nebo podobných interakcí výslovně neurčí konkrétní sekci, bere se takový požadavek jako **globální pravidlo pro všechny tabulky v programu**.

Výjimka:
- pokud uživatel výslovně řekne, že dané chování platí jen pro konkrétní sekci (např. Girls), zůstává pravidlo omezené na tuto sekci.

Toto pravidlo pouze zpřesňuje již definovaný společný tabulkový základ a nemění sekčně specifické názvy sloupců, hodnoty, filtry ani speciální akce.

### Girls vs. Oblíbené – rozdíl tlačítek nad tabulkou

V sekci **Girls** zůstávají tlačítka **Přidat** a **Smazat** v liště nad tabulkou aktivní podle běžné logiky sekce.

V sekci **Oblíbené** budou tlačítka:
- **Přidat**
- **Smazat**

trvale **zašedlá a neaktivní**.

Důvod:
- sekce Oblíbené je pouze podmnožina záznamů z Girls,
- nové herečky se přidávají v Girls,
- mazání samotného záznamu se provádí v Girls,
- změna členství v Oblíbených se řeší akcemi pro přidání / odebrání z oblíbených, nikoliv tlačítkem Smazat.

---

## Pracovní pravidlo specifikace

Tento dokument je průběžná specifikace Latflixu 2.0. Každé další potvrzené upřesnění vzhledu, funkcí, GUI nebo chování aplikace se má průběžně zapracovat sem, aby existoval jeden konzistentní zdroj pravdy pro pozdější kompletní implementaci.
