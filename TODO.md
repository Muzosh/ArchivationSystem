# Funkční/logické změny
- ! opravit logování a docstrings, aby bylo trochu více přehledné
- všechny operace dát do jednoho DB contextu a zajistit revertibilitu v případě chyby
- po provedení archivace pravděpodobně budeme chtít původní soubory smazat (s tím souvisí i další bod šifrování)
- je třeba vyřešit nějak šifrování - momentálně se ukládá soubor zašifrovaný nextcloudem, co klíče?
- archivationsystem databáze:
    - db_library neposkytuje možnost záznamy z tabulky mazat - to je možná dobře? pro údržbu je to spíš špatně
    - v DB.ArchivedFile se na kombinaci FileName+Owner nahlíží jako na UNIQUE constraint - to je možná až moc omezující, možná bych dal jen FilePath UNIQUE, pokud opravdu chceme zamezit znovu-archivování stejného souboru
- rabbitmq umí u queues a messages nastavit durable=True, což znamená, že pád serveru neohrozí stav serveru
- každý vytvořený proces si vytváří svého (např.) vlastního Archivera (ten však asi může být jeden pro všechny procesy)

# Strukturální změny
- možná třeba spojit soubory do nějakých X_helper.py nebo naopak rozdělit do více modulů
- v utils rozdělit metody do tříd nebo modulů
- dát více duplicitních věcí do common
    - např. parsování argumentů v start_X?
- ConnectionMaker dát do samotného modulu
    - oddělit od TaskConsumera
    - nebo spíše přejmenovat celý modul
- ! projet variables v celém projektu a trochu je upravit tak, aby lépe odrážely to, co v sobě mají uložené
    - ne všechny, ale u některých je to potřeba
- na konci možná dát configs do /etc/archivationsystem/config?
- database.db_library: _get_formated_XXX jsou možná zbytečné

# Bezpečnostní změny
- `"".format()` údajně umožňuje se dostat ke globals např. přes `"{person.__init__.__globals__[CONFIG][API_KEY]}".format(person)`
- odebrat relativní importy (někdo si tam může dosadit vlastní package)
    - nicméně k tomu by potřeboval přístup do systému a tím pádem by i tak byl schopen upravit existující package?
- hesla k autentizaci u rabbimq serveru jsou uložena v plaintextu v configu

# Dokumentace
- ! přesunout sqlscripts do docs a odkázat se na ně v README

# Návrhy
- některé configy jsou duplicitní a vždy budou stejné
    - např. TSA se využívá u archivation i retimestamping, bude to někdy potřeba rozdílné? 
- u té manuální validace s výsledkem do mailu:
    - výběr je založen na základě znalost jména souboru, jména vlastníka nebo pokud člověk dokonce zná ID v DB
    - asi by bylo fajn ještě přidat např. "zvaliduj posledních X souborů"
    - ještě to pak třeba zautomatizovat
    - navíc se zbytečně posílá několik tasku pro každý FileID - jeho recipients budou vždy stejní
- možná z rabbitmq přejít na Twisted, vypadá to jednoduššeji (nebo také nějaké jiné tools?)
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
            - proto se nyní využívá ten workaround s nameless/default exchange, která je přeposílá zprávy 1 ku 1
    - nevíc jeho dokumentace je docela omezená a odpovědi na stackoverflow také nic moc
    - struktura a orientaci v dokumentaci je pain
        - vůbec se v "Get Started" neřeší přihlašování k serveru, někde v půlce dokumentace o autentizaci najdu, že default je guest/guest
        - že prý jde pak v configu nastavit, kteří uživatelé se mohou k serveru připojit remote a kteří jen z localhostu
        - jenže když přejde na stránku o configu, tak najdu, že v logu najdu jeho lokaci
        - na stránce o logování informace o tom, kde log je, není a odkazují mě na File and Directory Locations
        - tam je však jen tuna environment variables, ty jsou však po instalaci v systému prázdné
        - nakonec log najdu - jenže v logu je strašně moc nerelevantní záznamů a ja v něm musím hledat lokaci configu, tak jak to bylo napsané v dokumentaci
        - jakmile to najdu, zjistim, že lokace configu je tam nastavená na (none), takže po googlení jsem zjistil, že vlastně config k serveru vlastně defaultně ani neexistuje a já si ho musím kdyžtak sám vytvořit - WHY?