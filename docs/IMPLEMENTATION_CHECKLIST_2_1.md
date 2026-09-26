# Latflix 2.1 – implementační kontrolní seznam

Zdroj pravdy: `docs/SPEC_LATFLIX_2.md`.

Tento seznam neslouží jako náhrada specifikace. Je to pojistka proti tomu, aby se při čistém přepisu znovu ztratily dříve potvrzené funkce.

## Aplikace a rozložení
- [x] Nativní `QMainWindow` pro běžné systémové snapování na Windows/Linuxu.
- [x] Horní menu: Soubor, Úpravy, Nástroje, Zobrazení, Nastavení, Nápověda.
- [x] Levé menu s hlavními i pomocnými sekcemi a jemným zvýrazněním aktivní sekce.
- [x] Sbalení levého menu šipkou.
- [x] Rychlé filtry v levém menu.
- [x] Horní pracovní panel 136 px v běžných datových sekcích, Přehled je výjimka.
- [x] Skrytí/zobrazení horního panelu přes Zobrazení.
- [x] Stavový řádek: počet aktuálních výsledků, velikost řádků 1–5, u Girls/Oblíbené průměrný věk.

## Společný tabulkový základ
- [x] Model/view: `QTableView + QAbstractTableModel + QSortFilterProxyModel`.
- [x] První sloupec zámek, druhý aktuální vizuální počet řádku.
- [x] Zámek patří záznamu; číslo se přepočítává podle aktuálního zobrazení.
- [x] Hlavička je výchozí zamčená, systémové sloupce jsou pevné.
- [x] Odemčená hlavička: resize/přesun datových sloupců.
- [x] Uložení pořadí/šířek zvlášť podle sekce.
- [x] Kontext záhlaví: přejmenovat / skrýt; Zobrazení obnovuje viditelnost.
- [x] Bílá / světle šedá alternace podle aktuálního pořadí.
- [x] Řádkový výběr bez samostatného Excel-like current-cell zvýraznění.
- [x] Souvislé vybrané řádky jsou kreslené jako jeden celek, zámek je mimo obrys.
- [x] Ctrl / Shift / tažený vícenásobný výběr přes společný Qt selection model.
- [x] Klik do prázdné části tabulky ruší výběr.
- [x] Data headers třídí oběma směry bez viditelné šipky.
- [x] Obyčejné editovatelné textové buňky se aktivují jedním klikem.
- [x] Textové editory používají standardní výběr textu, Ctrl+C/Ctrl+V a nativní Linux primary-selection prostřední tlačítko.
- [x] Enter je zpracován jen na KeyPress a posune editaci právě o jeden řádek dolů ve stejném textovém sloupci.
- [x] Esc nemá tabulkovou speciální akci.
- [x] Výběrové buňky: jeden klik, okamžitý zápis, bez šipky a bez vlastní změny barvy.
- [x] Přechod mezi aktivními editory/dropdowny je řešen stejným klikem.
- [x] Poznámky: jeden klik inline, dvojklik větší editor s aktuálním textem.
- [x] Zamčené Girls Jméno a Videa/Super Název: dvojklik kopíruje a ukáže „Zkopírováno“.
- [x] Nové zcela prázdné řádky se odstraní při opuštění sekce / ukončení.
- [x] Společná lišta používá stejné nízké prvky; běžná tlačítka nemají rozbalovací šipky.
- [x] Hledání je průběžný fulltext pouze aktuální sekce; koš maže jen hledání.
- [x] Vyčistit je vpravo a ruší hledání + filtry, nikoliv sort/layout.

## Girls / Oblíbené
- [x] Sdílený datový základ; Oblíbené je podmnožina, ne kopie.
- [x] Sloupce a jejich pořadí podle specifikace.
- [x] Přidat je split +1/+5/+10; nové řádky nahoře, prázdné a odemčené.
- [x] Oblíbené má Přidat/Smazat trvale deaktivované.
- [x] Smazání jen odemčených a vždy po potvrzení.
- [x] Hromadné akce: Přidat/Odebrat z Oblíbených + Hromadně přidat odkazy.
- [x] Filtry Národnost, Typ, Stav, Sex, Nahota, Obličej, Profilovka.
- [x] Národnost je řazená podle použití, prvních 10 + Další.
- [x] Věk drží zdrojovou hodnotu a mimo editaci zobrazuje odvozený věk.
- [x] Sledování = počet konkrétních uložených URL.
- [x] Počet výskytů = pouze platné/plnohodnotné Videa.
- [x] Tag popup: centrální tagy/barvy, řazení použití→abeceda, row-major, modalita, Uložit/Zrušit, klávesnice.
- [x] Profilová fotografie: výběr, multi-monitor výřez, pravé tlačítko s potvrzením smazání.
- [x] Horní panel: jméno, favorite, věk, výskyty, 2 řádky modrých link chips, pravé akce.
- [x] Modré link chips slučují stejný typ, ukazují (N), řadí podle globálního použití a otevírají všechny URL daného typu.
- [x] Detail herečky včetně dynamických aliasů po 4 polích v řádku; bez Sledování/Počtu výskytů.
- [x] Dialog Odkazy herečky: uložené odkazy nahoře + 10 kompaktních řádků Automaticky/URL.
- [x] Hromadné odkazy: jeden řádek na vybranou herečku.
- [x] Zobrazit odkazy přejde do Odkazů přes stabilní ID a zobrazí všechny odkazy herečky.
- [x] Průměrný věk reaguje na sloupcové filtry, ne na fulltext Hledání.

## Videa / Super
- [x] Jedna datová sada; Super je pouze příznak/podmnožina.
- [x] Sloupce podle specifikace včetně Dívka 1–3, Stav/Kvality, M+Ž a Poznámky.
- [x] Našeptávače Herečka/Studio s rankingem výskyty→abeceda; prefix před substring.
- [x] Alias se nabízí jen tehdy, když odpovídá právě psanému dotazu, a mapuje na stejný Girl záznam.
- [x] Neznámá herečka/studio nabízí vytvoření nového záznamu v Girls/Studia.
- [x] Detail videa spravuje libovolný počet účinkujících.
- [x] Všechny účinkující včetně detail-only vstupují do hledání, filtrů a výskytů.
- [x] Viditelné Dívka 1–3 jsou dynamicky seřazené podle globálního Počtu výskytů, tie = abeceda.
- [x] Platný videozáznam: nejméně 4 datová pole + 2 ze 3 klíčových Herečka/Název/Studio.
- [x] Stav NECHCI: Stav + číslo řádku červeně, Kvalita/Dostup. kvalita/Velikost šedé a neaktivní, hodnoty se nemažou.
- [x] Toolbar: Přidat, Smazat, SUPER membership, Hledání, Studio/Stav/Kvalita, Vyčistit; bez Hromadných akcí.
- [x] Studio filter: výskyty→abeceda, přibližně 15 viditelných výsledků a scrollbar.
- [x] Horní panel Studia/Herečky, 3 řádky modrých chips, Ctrl/Shift multi-select OR.
- [x] Detail vpravo nahoře.
- [x] Odebrat ze SUPER vyžaduje potvrzení.

## Studia
- [x] Název, Typ, Odkaz, Počet výskytů + systémové sloupce.
- [x] Počet výskytů počítá jen platná Videa.
- [x] Toolbar Přidat/Smazat/Hledání+koš/Vyčistit bez dalších sekčních filtrů.

## Odkazy
- [x] Režimy Vše / Sítě / Zdroje / Rozcestníky.
- [x] Modré typové filtry řazené použití→abeceda, stránkované v pevném panelu.
- [x] Ctrl/Shift multi-select modrých filtrů s OR.
- [x] Pravé akce Přidat odkazy / Seznam položek / Viditelné filtry / Exportovat / Zobrazit odkazy.
- [x] Hlavní tabulka a sloupce podle referenčního screenshotu.
- [x] Toolbar Přidat/Odebrat/Hromadné akce/Hledání/Obrázek/Vyčistit.
- [x] Katalog typů Síť/Zdroj/Rozcestník včetně Použití, obecného webu a slučování názvů.
- [x] Viditelné filtry přes checklist.
- [x] Hromadné přidání odkazů s 10 řádky a autodetekcí typu.
- [x] Export nabízí pouze typy skutečně přítomné v aktuálně vyfiltrované tabulce, seřazené podle počtu sestupně, a exportuje jen tyto viditelné URL.
- [x] Web otevírá konkrétní URL, Poslední obrázek má explicitní nahrání.

## Přehled
- [x] Karty Girls, Oblíbené, Videa, SUPER, Studia, Odkazy, Tagy.
- [x] Dynamické počty.
- [x] Klikací detailní dialog s přechodem do sekce.
- [x] Girls: počet, průměrný věk, národnosti, Oblíbené.
- [x] Oblíbené: počet, průměrný věk, národnosti, Ohodnoceno.
- [x] Videa: počet, nejčastější herečky z platných videí, Ohodnoceno.
- [x] SUPER: počet, nejčastější studia/herečky, Ohodnoceno.
- [x] Studia: počet, použitých ve videích, nejčastější.
- [x] Odkazy: celkem + Sítě/Zdroje/Rozcestníky.
- [x] Tagy: počet, použitých, nejpoužívanější; žádné kategorie tagů.

## Pomocné sekce
- [x] Stavy a Kvality jsou centrální katalogy pro Videa.
- [x] Typy a Národnosti jsou centrální katalogy pro Girls.
- [x] Tagy jsou centrální katalog s editovatelnou barvou.
- [x] Pomocné sekce používají společný tabulkový základ, lock+row, hledání a Vyčistit.

## Datová bezpečnost
- [x] Hlavní GUI nepíše SQL; vše vede přes Repository.
- [x] Latflix 2.1 používá `lf21_*` tabulky.
- [x] Startup nemigruje uživatelský obsah automaticky.
- [x] Import starších `lf2_*` dat je explicitní uživatelská akce.

## Co zůstává k praktickému ověření
Implementace je zapsaná v kódu, ale následující věci se musí potvrdit ručním používáním skutečného desktopového Qt prostředí:
- přesné pixelové rozměry proti screenshotům,
- přirozenost same-click handoff mezi otevřenými Qt dropdowny,
- chování systémového snapování na konkrétním Cinnamon/Windows prostředí,
- ergonomie multi-monitor výřezu,
- finální šířky sloupců a drobné spacingy.

Tyto body nejsou povolením funkci vynechat; jsou seznamem věcí, které se po spuštění 2.1 vizuálně doladí.
