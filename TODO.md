# Funkční/logické změny
- opravit logování a docstrings, aby to bylo trochu více přehledné
- všechny operace dát do jednoho DB contextu a zajistit revertibilitu v případě chyby
- po provedení archivace pravděpodobně budeme chtít původní soubory smazat (s tím souvisí i další bod šifrování)
- je třeba vyřešit nějak šifrování - momentálně se ukládá soubor zašifrovaný nextcloudem, co klíče?
- archivationsystem databáze:
    - db_library neposkytuje možnost záznamy z tabulky mazat - to je možná dobře? minimálně pro údržbu by to chtělo vytvořit nějaký admin_db_handler?
    - v ArchivedFile se na kombinaci FileName+Owner nahlíží jako na UNIQUE constraint - to je možná až moc omezující, možná bych dal jen FilePath UNIQUE, pokud opravdu chceme zamezit znovu-archivování stejného souboru
- rabbitmq umí u queues a messages nastavit durable=True, což znamená, že pád serveru neohrozí stav front
    - tohle je už možná implementováno všude, ale bude fajn otestovat, jak ovlivnitelná je performance spojená s meziukládáním dat na disk při vyšším provozu
- každý vytvořený proces si vytváří svého (např.) vlastního Archivera
    - ten však asi klidně může být jeden pro všechny procesy, nutné ověřit tento stav paralelismu
- na spoustě míst je logika workeru taková, že se na konci vrací "OK" nebo se vyvolá exception, která se ve wrapperu odchytí a return value se změní např. na "FAILED" nebo "KNOWN_ERROR"
    - možná existuje jednodušší logická struktura operací, než vracení statického "OK" na konci funkce
    - nebo např. také metoda "_validate_initial_package", akorát tam se vrací na konci True, nikdy se nevrátí False, jenom exceptions
- celý systém configu se mi také moc nelíbí, při každém spuštění workera nebo jiné operace je třeba do argumentu vždy psát plnou cestu ke configu
    - možná by bylo lepší config dát na statické místo, dokud si spouštěcí skripty budou data tahat bez nutnosti uživatele zadat místo configu
    - nebo dát config přímo do spouštěcích skriptů (uživatel si spouštěcí skript nakonfiguruje a spustí)
- v kódu existuje nekonzistence mezi vkládáním a taháním dat z DB
    - při vkládání dat do FilePackages se nad PackageHashSha512 automaticky volá b64encode v "_get_formated_query_insert_file_packages", ale při tahání dat z DB se to už nedekóduje a programátor na to musí myslet sám

# Strukturální změny
- v utils rozdělit metody do tříd nebo modulů na základě jejich využití (crypto_utils, file_utils, db_utils atd.)
- dát více duplicitního kódu do common
    - např. parsování argumentů v start_X
    - "_get_expiration_date", "_create_new_timestamp",...
    - _parse_message_body
- ConnectionMaker dát do samotného modulu, oddělit od TaskConsumera
    - nebo přinejmenším přejmenovat celý modul
- některé funkce v sobě volají další funkce, jméno první funkce pak úplně neodráží, co funkce dělá
    - např. funkce "_create_new_timestamp" v sobě nejen vytváří timestamp, ale zároveň i tento timestamp ukládá do souboru a také volá další lokální metodu "_store_used_cert_files" (která je btw duplicitní)
    - tohle by chtělo asi nějak přeuspořádat
- na konci možná dát configs do /etc/archivationsystem/config?
- database.db_library: _get_formated_XXX jsou možná zbytečné

# Bezpečnostní změny
- `"".format()` údajně umožňuje se dostat ke globals např. přes `"{person.__init__.__globals__[CONFIG][API_KEY]}".format(person)`
    - je tohle bezpečnostní slabina?
- odebrat relativní importy (někdo si tam může dosadit vlastní package)
    - nicméně k tomu by potřeboval přístup do systému a tím pádem by i tak byl schopen upravit existující package?
- hesla k autentizaci u rabbimq serveru jsou uložena v plaintextu v configu

# Dokumentace
- placeholder

# Návrhy
- některé configy jsou duplicitní a vždy budou stejné
    - např. TSA se využívá u archivation i retimestamping, bude to někdy potřeba rozdílné? 
- u té manuální validace s výsledkem do mailu:
    - výběr je založen na základě znalost jména souboru, jména vlastníka nebo pokud člověk dokonce zná ID v DB
    - asi by bylo fajn ještě přidat např. "zvaliduj posledních X souborů"
    - ještě to pak třeba zautomatizovat
    - navíc se zbytečně posílá několik tasku pro každý FileID - jeho recipients budou vždy stejní
- možná z rabbitmq přejít na Twisted?, vypadá to jednoduššeji (nebo také nějaké jiné tools?)
    - má v sobě dohromady:
        - echo server
        - web server
        - publish/subscribe servery+klienty (tohle by mohlo nahradit rabbitmq)
        - mail client (na posílání reportu z validation)
        - SSH client (pokud by archivační systém běžel na jiném stroji?)
- obecně mi rabbitmq připadá až moc zbytečně složitý
    - hlavně jeho architektura, ale i implementace v pythonu
    - v podstatě je v tomto projektu využit hlavně takový workaround, jak nepoužívat exchanges
        - protože pro jednoho producera máme vždy jednoho consumera, tudíž mezi nimi stačí jedna konkrétní fronta
        - jenže exchange je v rabbitmq CORE komponenta, která je třeba i když nám stačí jedna jediná fronta
            - proto se nyní využívá workaround s nameless=default exchange, která je přeposílá zprávy 1 ku 1
    - nevíc jeho dokumentace je docela omezená a odpovědi na stackoverflow také nic moc
    - struktura a orientace v dokumentaci je poměrně složitá, příklad:
        - vůbec se v "Get Started" neřeší přihlašování k serveru, někde v půlce dokumentace o autentizaci najdu, že default je guest/guest
        - že prý jde pak v configu nastavit, kteří uživatelé se mohou k serveru připojit remote a kteří jen z localhostu
        - jenže když přejdu na stránku o configu, tak tam čtu, že v logu najdu jeho lokaci
        - na stránce o logování informace o tom, kde log je, není a odkazují mě na File and Directory Locations
        - tam je však jen tuna environment variables, ty jsou však po instalaci v systému prázdné
        - nakonec log najdu - jenže v logu je strašně moc nerelevantní záznamů a ja v něm musím hledat lokaci configu, tak jak to bylo napsané v dokumentaci
        - jakmile to najdu, zjistim, že lokace configu je tam nastavená na (none), takže po googlení jsem zjistil, že vlastně config k serveru vlastně defaultně ani neexistuje a já si ho musím kdyžtak sám vytvořit
        - to, že config vlastně neexistuje a musí se vytvořit manuálně, mi přijde dost nestandardní a aspoň v dokumentaci to mohli zmínit hned ze začátku někde