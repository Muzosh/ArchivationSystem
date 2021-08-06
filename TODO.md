# Návrhy na vylepšení

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
1. **Opravit funkci `src/archivationsystem/validation/validator._extract_tar_to_temp_dir()`**
    - na jednom místě se volá se špatným počtem argumentů

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
    - Twisted asi nakonec ne, je to spíše pro tvorbu aplikací, které potřebují internet stack