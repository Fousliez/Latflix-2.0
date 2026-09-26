# Pracovní pravidla Latflixu

Tento soubor zachycuje pravidla spolupráce, která nejsou funkcemi aplikace, ale musí se při dalším vývoji dodržovat.

1. `docs/SPEC_LATFLIX_2.md` je hlavní zdroj pravdy pro funkce, chování a vzhled aplikace.
2. Nový potvrzený požadavek se porovná se současnou specifikací:
   - pokud je kompatibilní, zapíše se do specifikace,
   - pokud je v rozporu, nesmí se staré pravidlo potichu přepsat; nejdřív se musí vyjasnit, která varianta platí.
3. Požadavky na chování tabulek jsou globální, pokud uživatel výslovně neurčí konkrétní sekci.
4. Screenshoty jsou vizuální/funkční reference tam, kde písemná specifikace není přesnější.
5. Funkce, které už existovaly a nebyly nově zrušeny, se při přepisu nesmí svévolně vynechat.
6. Implementace se kontroluje proti **celé** specifikaci, ne jen proti posledním zprávám.
7. **GitHub Actions se nesmí aktivně používat, kontrolovat ani číst bez výslovného svolení uživatele.** Pokud repository workflow spustí automaticky samotný commit, vývoj se na jeho výsledky bez povolení nedívá a netvrdí, že je ověřil přes Actions.
8. Vývoj Latflixu 2.1 může být rozdělen na více etap/commitů, ale nesmí to znamenat vynechání požadavků.
