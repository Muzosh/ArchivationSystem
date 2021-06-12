# Funkční/logické změny
- u logování upravit pojmy v hranatých závorkách tak, aby to odráželo, z jaké třídy nebo z jakého modulu se to volá
- u té manuální validace s výsledkem do mailu:
    - výběr je založen na základě znalost jména souboru, jména vlastníka nebo pokud člověk dokonce zná ID v DB
    - asi by bylo fajn ještě přidat např. "zvaliduj posledních X souborů!
    - ještě lépe to pak zautomatizovat

# Strukturální změny
- možná třeba spojit soubory do nějakých X_helper.py nebo naopak rozdělit do více modulů
- dát více duplicitních věcí do common
    - např. parsování argumentů v start_X?
- ConnectionMaker dát do samotného modulu
    - oddělit od TaskConsumera
- projet variables v celém projektu a trochu je upravit tak, aby odrážely to, co v sobě mají uložené
    - ne všechny, ale u některých je to potřeba

# Dokumentace
- přesunout sqlscripts do docs a odkázat se na ně v README
- dopsat do README instalaci archivationsystem balíku

# Návrhy
- některé configy jsou duplicitní a vždy budou stejné
    - např. TSA se využívá u archivation i retimestamping, bude to někdy potřeba rozdílné? 






