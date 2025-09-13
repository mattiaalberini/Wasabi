## Portale per la vendita di piatti da asporto di un ristorante giapponese 
Realizzazione di un portale per la vendita di piatti da asporto di un ristorante giapponese che supporta le seguenti classi di utenti:
 - Utenti non registrati: hanno solamente la possibilità di guardare il menù. 
 - Utenti registrati come clienti: hanno la possibilità di ordinare i piatti. 
 - Utenti registrati come dipendenti: hanno la possibilità di aggiungere piatti al menù e controllare la lista degli ordini ricevuti. 
 - Utente admin: ha la possibilità di creare gli “utenti dipendenti”. 

### Piatti 
Ogni piatto presente nel menù viene catalogato secondo un “tipo di portata” (antipasto, 
primo, secondo, …) e in base agli ingredienti da cui è composto (carne, pesce, vegano, …). \
I clienti (utenti registrati e non) possono filtrare i piatti secondo queste caratteristiche. 

### Clienti non registrati
Possono solamente guardare il menù, per procedere all’acquisto dei piatti hanno bisogno di 
registrarsi come clienti. 

### Clienti registrati
Ogni cliente registrato può selezionare i piatti che desidera acquistare e successivamente 
procedere all’acquisto di essi, specificando l’orario in cui si presenterà al ristorante per 
ritirare l’ordine. \
Per ogni euro di spesa verranno aggiunti punti alla carta fedeltà del cliente. Al 
raggiungimento di un certo quantitativo di punti sarà possibile ricevere un buono sconto da 
utilizzare sul prossimo acquisto.

### Dipendenti
I dipendenti hanno la possibilità di aggiungere e rimuovere piatti dal menù, aggiungendo 
foto, specificando le categorie, il prezzo e aggiungendo una piccola descrizione del piatto. \
Hanno l’elenco degli ordini che sono stati effettuati e, una volta che l’ordine viene ritirato, 
devono contrassegnarlo come completato. \
Possono modificare la cifra di punti che il cliente deve raggiungere per ottenere il buono e 
specificare il valore di esso.

### Admin 
Utente che permette di creare i vari utenti per i dipendenti. Un dipendente non può crearsi 
l’utente da solo. 

## Esecuzione
1. `pipenv shell`
2. `python manage.py runserver`

Test