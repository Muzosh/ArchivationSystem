# Návrhy na vylepšení

## NEW

### Funkční a logické návrhy

1. **Vytvořit detailnější logování a popis kódu pomocí Python docstrings.**
    - Aktuální informace zaznamenávané v logu jsou poněkud nepřehledné a málo informativní.
    - Dále také chybí detailní popis funkcí v jednotlivých modulech.
1. **Zajistit kompletní reverzibilitu operací v případě chyby,**
    - v databázi i v souborovém systému.
1. **Smazat původní soubory v Nextcloud databázi po jejich úspěšném archivování.**
1. **Navrhnout způsob archivování souborů ve vztahu k šifrování na straně klienta.**
    - Aktuálně se archivuje soubor již zašifrovaný systémem Nextcloud s využitím interních klíčů.
    - Bude vhodné se zamyslet nad tím, zda bude vhodné soubor ukládat dešifrovaný, re-šifrovaný s použitím nových klíčů nebo se budou také archivovat interní klíče.
1. **Vytvořit knihovnu pro administrativní práci s databází.**
    - Aktuální knihovna pro práci s databází db_library neposkytuje možnost záznamy z databáze mazat.
    - Pro účely archivace souborů je tato skutečnost příhodná, nicméně pro účely lepší údržby a využitelnosti systému bude vhodné zvážit vytvoření nové knihovny (např. admin_db_library), která bude sloužit k těmto administrátorským účelům.
1. **Redefinovat unikátní identifikátor záznamů v databázi archivačního systému.**
    - V ArchivedFile se na kombinaci atributů FileName a Owner nahlíží jako na UNIQUE CONSTRAINT (tedy jako na unikátní identifikátor záznamu).
    - Tato skutečnost může být až příliš omezující v případě nutnosti zamezit znovu-archivování stejného souboru.
    - Bude vhodné se zamyslet nad tím, zda je vůbec toto omezení třeba a jestli ano, jakou jinou kombinaci unikátního identifikátoru záznamu (např. pouze FilePath) je třeba využít.
1. **Namísto MySQLConnector využít nějaký jiný, více podporovaný framework pro připojení archivačního systému k jeho databázi (například SQLAlchemy).**
1. **Otestovat výkon systému v případě ukládání zpráv na disk za účelem ochrany dat.**
    - Služba RabbitMQ umožňuje u definovaných front a zpráv nastavit atribut durable (= pád serveru neohrozí stav front).
    - Bude vhodné otestovat, jak moc je výkon systému s tímto nastavením ovlivněn (dochází totiž k vyššímu ukládání a čtení dat na disk) při vyšším provozu.
1. **Otestovat možnosti využití jedné sdílené instance pomocné třídy pro všechny procesy.**
    - Každý vytvořený proces spojený s různými operacemi si vytváří vlastní instanci podpůrné třídy. Bude vhodné otestovat možnost využití pouze jedné instance a její sdílení mezi různé procesy.
    - Např. třída ArchivationWorker ve funkci archive() pokaždé vytváří třídu Archiver. Je třeba otestovat, zda by nestačilo mít pouze jednu instanci třídy Archiver a tu globálně využívat ve funkci archive().
1. **Redefinovat logickou strukturu některých funkcí v projektu.**
    - Na několika místech v projektu je aktuální logika taková, že se na konci funkce vrací např. „OK“ nebo se vyvolá výjimka, která se ve wrapperu odchytí a hodnota funkce se změní například na „FAILED“ nebo „KNOWN_ERROR“.
    - Bude vhodné se zamyslet, zda neexistuje jednodušší logická struktura operací, která staticky nevrací na konci funkce jeden konkrétní řetězec (např. by funkce nemusely vracet nic a chybové stavy by se odchytávaly výše).
    - To samé platí i pro funkce, které na svém konci staticky vrací True (např. funkce _validate_initial_package)
1. **Redefinovat konfiguraci všech operací v archivačním systému.**
    - Aktuální systém konfigurace operací je příliš zmatečný, neefektivní a v některých případech duplicitní. Při každém spuštění je třeba poskytnout plnou cestu ke konfiguračnímu souborů, který se velmi pravděpodobně nebude často měnit.
    - Návrhy řešení:
        - přesunout konfiguraci na statické místo (např. /etc/archivationsystem/config), odkud si ji spouštěcí skripty budou načítat nebo
        - vložit konfiguraci přímo do spouštěcích skriptů.
        - V obou případech bude nutné zajistit odstranění duplicity (např. informace o TSA se využívají ve více spouštěcích skriptech).
1. **Opravit nekonzistenci mezi zapisováním a čtením dat z databáze archivačního systému.**
    - Při zapisování dat do FilePackages se ve funkci _get_formated_query_insert_file_packages nad PackageHashSha512 automaticky kóduje do base64, nicméně při čtení dat z databáze se ten samý atribut již nedekóduje a programátor na to musí myslet sám.

### Strukturální návrhy

1. **V modulu utils rozdělit funkce do tříd nebo sub-modulů kategoricky na základě jejich využití (například crypto_utils, file_utils, db_utils, atd.).**
1. **Vyhledat a přesunout duplicitní kód do modulu common.**
    - Například kontrola a načtení argumentů ve spouštěcích skriptech.
    - Například funkce _get_expiration_date,_create_new_timestamp, _parse_message_body,_store_used_cert_files.
1. **Přesunout ConnectionMaker do samostatného modulu, tj. oddělit od TaskConsumer.**
    - Nebo přinejmenším přejmenovat celý modul tak, aby byl jeho název společný pro obě třídy.
1. **Vyhledat a opravit nekonzistence v názvosloví funkcí.**
    - Některé funkce ve svém kódu volají další funkce. Jména takových funkcí pak plně neodráží, co přesně funkce dělá. Například funkce _create_new_timestamp v sobě nejenže vytváří časové razítko, ale zároveň jej i ukládá do souboru a také volá další lokální funkci_store_used_cert_files.
    - Dále také přejmenovat funkce tak, aby z názvu bylo možné poznat, jakou hodnotu vrací. Například is_XXX pro funkce, které vrací logické hodnoty True/False.
1. **Odstranit statické definování SQL dotazů.**
    - Funkce _get_formated_XXX v modulu database.db_library jsou redundantní a je možné tyto dotazy definovat rovnou v místech, kde se nyní využívají.
    - V opačném případě je třeba promyslet, v jakých případech by statická definice dotazů byla výhodná.

### Bezpečnostní návrhy

1. **Prozkoumat bezpečnostní slabinu ve formátování řetězců pro archivační systém.**
    - Formátování řetězců v jazyce Python přes "".format() umožňuje získat informace z globálních proměnných např. s pomocí následujícího kódu: {person.__init__.__globals__[CONFIG][API_KEY]}".format(person) [24].
1. **Prozkoumat bezpečnostní slabinu ve využití relativních importů modulů.**
    - Při využití relativních importů hrozí nahrazení daného modulu škodlivým modulem. Nicméně k tomuto kroku by útočník potřeboval přístup do souborového systému.
    - Bude třeba najít a zdokumentovat případnou dodatečnou hrozbu nahrazení modulu v případě, kdy útočník již získal přístup do systému.
1. **Upravit možnosti zadávání hesla pro autentizaci uživatele k RabbitMQ serveru a k databázi archivačního systému.**
    - Momentálně jsou hesla uložená v konfiguračním souborech v otevřeném formátu.
    - Bude vhodné implementovat bezpečnější formu autentizace, například s využitím interní knihovny getpass.

### Další návrhy

1. **Na konci všech úprav dokončit dokumentaci projektu v docs adresáři.**
1. **Redefinovat manuální validaci s výsledkem poslaným na emailové účty.**
    - Aktuálně je výběr souborů k validaci založen na základě znalosti jména souboru, jména vlastníka nebo samotného ID v databázi.
        - Bylo by vhodné přidat možnost „validace posledních X souborů“ nebo „validace všech doposud nevalidovaných souborů“ (nebo jimi existující možnosti validace kompletně nahradit).
        - Dále by bylo vhodné celý proces zautomatizovat (validace by se sama spustila např. jednou za měsíc).
    - Dalším nedostatkem je posílání mnoho zpráv na RabbitMQ pro každý FileID. Tato operace je redundantní, protože v každé zprávě je příjemce zprávy stejný. Je možné tedy operaci nahradit posláním jedné zprávy s příjemcem, ve které bude seznam FileID.
1. **Zvážit využití jiného framework na předávání zpráv namísto RabbitMQ.**
    - Architektura a aktuální implementace frameworku RabbitMQ se zdá být příliš zbytečně složitá:
        - Základní komponenta frameworku je tzv. Exchange, která zajišťuje správné směrování zpráv od odesílatele zpráv do jednotlivých front pro vícero příjemců zpráv na základě atributů ve zprávě.
        - V aktuální implementaci se využívá vždy jeden Producent (odesílatel, generuje zprávy do příslušné fronty) a k němu příslušný Consumer (příjemce, přijímá zprávy z příslušné fronty).
        - Exchange tedy není potřeba, protože vždy maximálně jeden odesílatel posílá zprávy maximálně jednomu příjemci.
        - Nicméně tato komponenta je v RabbitMQ vyžadována vždy, proto se nyní v implementaci používá tzv. default/nameless Exchange, která pouze přesměrovává bez jakýchkoliv pravidel zprávy od odesílatele k příjemci. Toto je obecně považováno jako určité obcházení pravidel a tzv. „bad practice“.
        - Tato neefektivní architektura je využívána pro každou operaci archivačního systému zvlášť.
        - Návrhy řešení:
            - Redefinovat strukturu RabbitMQ serveru, tj. vytvořit jednu Exchange, která na základě nových atributů ve zprávě je bude směrovat do různých front pro dané operace archivačního systému nebo
            - využít jiný framework pro předávání zpráv.
    - Další nevýhodou RabbitMQ služby je její poměrně složitě strukturovaná a málo informativní dokumentace, ve které se relativně špatně orientuje. Dále také poměrně omezená komunita.
    - Jeden z nahrazujících kandidátů je framework Twisted, který obsahuje:
        - echo server,
        - webový server, Consument
        - publish/subscribe servery a klienty (funkcionálně nahrazuje RabbitMQ)
        - poštovního klienta (možné využít na posílání výsledků z validace archivovaných souborů) a
        - SSH klienta (možné využít v případě nutnosti vzdáleného archivačního systému).

## OLD

### Funkční/logické změny

1. **opravit logování a docstrings, aby to bylo trochu více přehledné**
1. **všechny operace dát do jednoho DB contextu a zajistit revertibilitu v případě chyby**
    - asi bude třeba nějaká větší re-strukturalizace projektu
1. **po provedení archivace pravděpodobně budeme chtít původní soubory smazat (s tím souvisí i další bod: šifrování)**
1. **je třeba vyřešit nějak šifrování - momentálně se ukládá soubor zašifrovaný nextcloudem, co klíče?**
1. **archivationsystem databáze:**
    - db_library neposkytuje možnost záznamy z tabulky mazat - to je možná dobře? minimálně pro údržbu by to chtělo vytvořit nějaký admin_db_handler?
    - v ArchivedFile se na kombinaci FileName+Owner nahlíží jako na UNIQUE constraint -> to je možná až moc omezující, možná bych dal jen FilePath UNIQUE, pokud opravdu chceme zamezit znovu-archivování stejného souboru
1. **pro připojení k DB využít spíše framework SQLAlchemy nebo nějaký jiný, více podporovaný framework (namísto MySQLConnector)**
1. **rabbitmq umí u queues a messages nastavit durable=True, což znamená, že pád serveru neohrozí stav front**
    - tohle je už možná implementováno všude, ale bude fajn otestovat, jak ovlivnitelná je performance spojená s meziukládáním dat na disk při vyšším provozu
1. **každý vytvořený proces si vytváří svého (např.) vlastního Archivera**
    - ten však asi klidně může být jeden pro všechny procesy, nutné ověřit tento stav paralelismu
1. **na spoustě míst je logika workeru taková, že se na konci vrací "OK" nebo se vyvolá exception, která se ve wrapperu odchytí a return value se změní např. na "FAILED" nebo "KNOWN_ERROR"**
    - možná existuje jednodušší logická struktura operací, než vracení statického "OK" na konci funkce
    - nebo např. také metoda "_validate_initial_package", akorát tam se vrací na konci True, nikdy se nevrátí False, jenom exceptions
    - takové metody by tedy klidně nemusely vracet nic -> void
1. **celý systém konfigurace se mi moc nelíbí, při každém spuštění workera nebo jiné operace je třeba do argumentu vždy psát plnou cestu ke configu**
    - možná by bylo lepší config dát na statické místo, dokud si spouštěcí skripty budou data tahat bez nutnosti uživatele zadat místo configu
    - nebo dát config přímo do spouštěcích skriptů (uživatel si spouštěcí skript nakonfiguruje a spustí)
1. **v kódu existuje nekonzistence mezi vkládáním a taháním dat z DB**
    - při vkládání dat do FilePackages se nad PackageHashSha512 automaticky volá b64encode v "_get_formated_query_insert_file_packages", ale při tahání dat z DB se to už nedekóduje a programátor na to musí myslet sám

### Strukturální změny

1. **v utils rozdělit metody do tříd nebo modulů na základě jejich využití (crypto_utils, file_utils, db_utils atd.)**
1. **dát více duplicitního kódu do common**
    - např. parsování argumentů v start_X
    - "_get_expiration_date", "_create_new_timestamp",...
    - _parse_message_body
1. **ConnectionMaker dát do samotného modulu, oddělit od TaskConsumera**
    - nebo přinejmenším přejmenovat celý modul na něco společného pro obě třídy (ale osobně jsem spíše pro rozdělení)
1. **některé funkce v sobě volají další funkce, jméno první funkce pak úplně neodráží, co funkce dělá**
    - např. funkce "_create_new_timestamp" v sobě nejen vytváří timestamp, ale zároveň i tento timestamp ukládá do souboru a také volá další lokální metodu "_store_used_cert_files" (která je btw duplicitní)
    - tohle by chtělo asi nějak přeuspořádat/přejmenovat
1. **na konci možná dát config files do /etc/archivationsystem/config?**
    - \+ zajistit, aby se odtud nastavení načítalo? asi to závisí na tom, jestli a jak se konfigurační systém předělá či nikoliv
1. **database.db_library: _get_formated_XXX jsou možná zbytečné a je možné tyto queries použít rovnou v metodách**
    - v opačném případě je třeba vymyslet, v jakých use cases by se nám hodilo to mít jako konstantu, kterou by třeba v budoucnu mělo být výhodné takhle měnit na jednom místě
1. **metody, které vrací True/False by se mohly jmenovat jako is_XXX a naznačovat tím, co vrací**

### Bezpečnostní změny

1. **`"".format()` údajně umožňuje dostat se ke globals např. přes `"{person.__init__.__globals__[CONFIG][API_KEY]}".format(person)`**
    - je tohle bezpečnostní slabina v tomhle projektu?
1. **odebrat relativní importy (někdo si tam může dosadit vlastní package)**
    - nicméně k tomu by potřeboval přístup do systému a tím pádem by i tak byl schopen upravit existující package?
1. **hesla k autentizaci u rabbimq serveru jsou uložena v plaintextu v configu**
    - tohle by šlo udělat přes *getpass* při spouštění skriptů:

    ```python
    from getpass import getpass
    password = getpass()
    ```

### Dokumentace

1. **dokumentaci udělat jako poslední vzhledem k předpokládaným častým změnám**

### Návrhy

1. **některé configy jsou duplicitní a vždy budou stejné**
    - např. TSA se využívá u archivation i retimestamping, bude to někdy potřeba rozdílné?
1. **u manuální validace s výsledkem do mailu:**
    - výběr je založen na základě znalost jména souboru, jména vlastníka nebo pokud člověk dokonce zná ID v DB
    - asi by bylo fajn ještě přidat možnost např. "zvaliduj posledních X souborů"
    - ještě to pak třeba zautomatizovat (aby se validace např jednou za měsíc spustila)
    - navíc se zbytečně posílá několik tasku pro každý FileID - jeho recipients budou vždy stejní
1. **možná z rabbitmq přejít na Twisted?, vypadá to jednoduššeji (nebo také nějaké jiné tools?)**
    - má v sobě dohromady:
        - echo server
        - web server
        - publish/subscribe servery+klienty (tohle by mohlo nahradit rabbitmq)
        - mail client (na posílání reportu z validation)
        - SSH client (pokud by archivační systém běžel na jiném stroji?)
    - Twisted nakonec nebude nejlepší volba - jedná se spíše o toolkit pro tvorbu internetové aplikace, předávání zpráv na localhostu není ideální
    - vypadá to, že rabbitMQ nakonec bude nejlepší možnost z kategorie *open-source message brokerů*
1. **obecně mi rabbitmq připadá až moc zbytečně složitý**
    - hlavně jeho architektura, ale i implementace v pythonu
    - v podstatě je *v tomto projektu využit hlavně určitý workaround*, jak nepoužívat exchanges
        - protože pro jednoho producera máme vždy jednoho consumera, tudíž mezi nimi stačí jedna konkrétní fronta (a exchange není tedy potřeba)
        - jenže *exchange je v rabbitmq zásadní komponenta*, která je třeba i když nám stačí jedna jediná fronta
            - proto se nyní využívá workaround s nameless=default exchange, která je přeposílá zprávy 1 ku 1
    - nevíc dokumentace je docela omezená a má poměrně složitou strukturu/orientaci a odpovědi na stackoverflow také nejsou vždy k dohledání
    - příklad (osobní poznámka, to-be-deleted):
        - vůbec se v "Get Started" neřeší přihlašování k serveru, až někde v půlce dokumentace o autentizaci jsem našel, že default je guest/guest
        - že prý jde pak v configu nastavit, kteří uživatelé se mohou k serveru připojit remote a kteří jen z localhostu
        - jenže když přejdu na stránku o configu (abych se dozvěděl, kde ho najdu), tak tam čtu, že v logu najdu jeho lokaci
        - na stránce o logování informace o tom, kde se log nachází, není a odkazují mě na *File and Directory Locations*
        - tam je však jen tuna environment variables, které jsou ale po instalaci v systému prázdné
        - nakonec jsem logovací soubor našel - jenže v logu je strašně moc nerelevantních záznamů a v něm musím hledat lokaci configu, tak jak to bylo napsané v dokumentaci
        - jakmile jsem to našel, zjistím, že lokace configu je tam nastavená na (none), takže po dalším googlení jsem zjistil, že vlastně config k serveru  defaultně ani neexistuje a já si ho musím kdyžtak sám vytvořit
        - to, že config vlastně neexistuje a musí se vytvořit manuálně, mi přijde dost nestandardní a aspoň v dokumentaci to mohli zmínit hned ze začátku
