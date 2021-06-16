# Funkční/logické změny
- u logování upravit pojmy v hranatých závorkách tak, aby to odráželo, z jaké třídy nebo z jakého modulu se to volá
- všechny operace dát do jednoho DB contextu a zajistit revertibilitu v případě chyby
- po provedení archivace pravděpodobně budeme chtít původní soubory smazat (s tím souvisí i další bod šifrování)
- je třeba vyřešit nějak šifrování - momentálně se ukládá soubor zašifrovaný nextcloudem, co klíče?
- archivationsystem databáze:
    - db_library neposkytuje možnost záznamy z tabulky mazat - to je možná dobře? pro údržbu je to možná špatně
    - v DB.ArchivedFile se na kombinaci FileName+Owner nahlíží jako na UNIQUE constraint - to je možná až moc omezující, možná bych dal jen FilePath UNIQUE, pokud opravdu chceme zamezit znovu-archivování stejného souboru
# Strukturální změny
- možná třeba spojit soubory do nějakých X_helper.py nebo naopak rozdělit do více modulů
- dát více duplicitních věcí do common
    - např. parsování argumentů v start_X?
- ConnectionMaker dát do samotného modulu
    - oddělit od TaskConsumera
- projet variables v celém projektu a trochu je upravit tak, aby lépe odrážely to, co v sobě mají uložené
    - ne všechny, ale u některých je to potřeba
- na konci možná dát configs do /etc/archivationsystem/config?
- database.db_library: _get_formated_XXX jsou možná zbytečné

# Bezpečnostní změny
- `"".format()` údajně umožňuje se dostat ke globals např. přes `"{person.__init__.__globals__[CONFIG][API_KEY]}".format(person)`
- odebrat relativní importy (někdo si tam může dosadit vlastní package)
    - nicméně k tomu by potřeboval přístup do systému a tím pádem by i tak byl schopen upravit existující package?

# Dokumentace
- přesunout sqlscripts do docs a odkázat se na ně v README
- dopsat do README instalaci archivationsystem balíku

# Návrhy
- některé configy jsou duplicitní a vždy budou stejné
    - např. TSA se využívá u archivation i retimestamping, bude to někdy potřeba rozdílné? 
- u té manuální validace s výsledkem do mailu:
    - výběr je založen na základě znalost jména souboru, jména vlastníka nebo pokud člověk dokonce zná ID v DB
    - asi by bylo fajn ještě přidat např. "zvaliduj posledních X souborů"
    - ještě to pak třeba zautomatizovat
- možná z rabbitmq přejít na Twisted, vypadá to jednoduššeji
    - má v sobě dohromady:
        - echo server
        - web server
        - publish/subscribe servery+klienty (tohle by mohlo nahradit rabbitmq)
        - mail client (na posílání reportu z validation)
        - SSH client (pokud by archivační systém běžel na jiném stroji?)