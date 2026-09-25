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

---

## Pracovní pravidlo specifikace

Tento dokument je průběžná specifikace Latflixu 2.0. Každé další potvrzené upřesnění vzhledu, funkcí, GUI nebo chování aplikace se má průběžně zapracovat sem, aby existoval jeden konzistentní zdroj pravdy pro pozdější kompletní implementaci.
