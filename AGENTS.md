# Latflix 2.0 – závazná pravidla vývoje

Tento soubor je povinný pracovní kontext pro každého asistenta nebo vývojáře, který upravuje Latflix 2.0.

## 1. Povinné čtení před každou prací
Před jakoukoli změnou Latflixu 2.0 je nutné nejprve přečíst:
1. `AGENTS.md`
2. `docs/SPEC_LATFLIX_2.md`
3. `docs/IMPLEMENTATION_CHECKLIST_2_1.md`
4. `docs/ARCHITECTURE.md`

Bez přečtení těchto souborů se nesmí začít měnit kód. Pokud některý dokument odporuje aktuálnímu požadavku uživatele, rozpor se nesmí řešit tichým přepsáním.

## 2. SPEC je hlavní zdroj pravdy
`docs/SPEC_LATFLIX_2.md` je závazná a průběžně udržovaná specifikace. Žádný potvrzený požadavek uživatele nesmí zůstat pouze v chatu.

Nový nebo změněný požadavek:
1. porovnat se SPEC,
2. zapsat do SPEC,
3. teprve potom implementovat.

SPEC nesmí obsahovat vzájemně rozporná pravidla.

## 3. Checklist je závazný pracovní přehled
`docs/IMPLEMENTATION_CHECKLIST_2_1.md` je schválený kontrolní seznam implementace.

- `[x]` = implementováno a odpovídá SPEC,
- `[ ]` = chybí, je rozpracované nebo není dostatečně ověřené.

Bod se nesmí označit jako hotový jen proto, že existuje nějaký kód.

## 4. Povinná aktualizace dokumentace při každé změně
Před dokončením každé změny zkontrolovat:
- mění změna požadované chování? → aktualizovat SPEC,
- dokončuje nebo mění implementaci bodu? → aktualizovat checklist,
- mění technickou architekturu? → aktualizovat ARCHITECTURE.

## 5. Správný pracovní tok
`požadavek uživatele → SPEC → implementace → checklist`

Nikdy:
`chat → kód → později hledat, co uživatel vlastně chtěl`

## 6. Nový chat
Při pokračování v novém chatu se nejprve načte:
- `AGENTS.md`
- `docs/SPEC_LATFLIX_2.md`
- `docs/IMPLEMENTATION_CHECKLIST_2_1.md`
- `docs/ARCHITECTURE.md`

Aktuální stav repozitáře má přednost před starou konverzační pamětí.

## 7. Latflix 1 jako reference
Původní Latflix lze používat jako vizuální a funkční referenci, ale ne automaticky jako technickou předlohu.

## 8. Specifikace uvnitř aplikace
Latflix 2.0 má obsahovat uživatelsky dostupný pohled na:
- `docs/SPEC_LATFLIX_2.md`
- `docs/IMPLEMENTATION_CHECKLIST_2_1.md`

Doporučené umístění:
`Nápověda → Specifikace Latflixu`

Aplikace nesmí obsahovat ručně udržovanou kopii textu. Má načítat aktuální soubory.

Požadované minimum:
- obsah podle kapitol,
- zobrazení kapitoly,
- vyhledávání,
- přepnutí Specifikace / Stav implementace.

## 9. Před commitem
Před každým commitem ověřit:
1. Je požadavek ve SPEC?
2. Odpovídá implementace SPEC?
3. Změnil se checklist?
4. Změnila se architektura?
5. Jsou dokumentace a kód v souladu?
6. Teprve potom commitnout.

## 10. Kdy je projekt hotový
Latflix 2.0 je hotový až po:
- implementaci potvrzené SPEC,
- kontrole všech položek checklistu,
- praktickém ověření hlavních workflow,
- výkonovém ověření na reálných datech,
- finálním vizuálním průchodu proti referencím.

Do té doby platí povinná průběžná aktualizace SPEC, checklistu a architektury.
