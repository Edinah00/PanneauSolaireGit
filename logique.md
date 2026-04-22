Je veux creer une application web avec ce customtkinter , et sql server 
ça parle de Proposition de panneau solaire et de batterie qu'une ménage doit acheter d'apès leurs consommations regulières 
il y aura une fenetre dans laquelle unn client va inserer ses materiaux et la maniere dont il l'utilise  avec un bouton valider 
et apres une autre fenetre output : dans laquelle s'affichera les propositions : batterie et panneau solaire qui arrive à subvenir ses consomations 

Dans input :
  il y aura input :
        -Appareil 
        -Tronche :
                -Matin (entre 6 - 17 h)(configurable Base) 
                -Soirée (entre 17 - 19h)
                -nuit (ebtre 19h - 6h)
            
        -Intervalle de temps d'utilisation (ex :12 - 14h)
        -Puissance (Watt)
        - un bouton ajouter appareil
   il y aura une liste des appareils ajoutés et un bouton valider pour passer à la calcul  et on va se diriger dans output 

Dans Output :
   Il y aura l'affichage de la proposion d'apres les calculs 
    Le matin (6-17) 100% de puissance panneau solaire va être utiliser tandis que pendant la soirée , ce sera x% (configurable) de la PS va etre utilisée
    Mais pendant la nuit , ce sera la batterie qui va être utilisée 

        -Batterie avec de l'energie ?? (Wh)
            -theorique 
                Voici comment le calcul va se derouler :
                    A partir des données d'utilisations des appareils pendant la nuit , on va calculer l'Energie nécessaire pour pouvoir le subvenir  tout les consommations de la nuit
            -pratique 
                Voici comment le calcul va se derouler :
                    On sait très bien qu on ne peut pas laisser une batterie totalement applat ; ducoup Batterie pratique = batterie theorique  + 50%(batterie theorique)

        -Panneau solaire avec de puissance ??
            -theorique 
                Voici comment le calcul va se derouler :
                   Puisque la batterie va être utilisé la nuit , elle va être applat la matinée , ducoup on doit la charger avec notre panneau solaire . La batterie va se charger tant que il y aura de soleil pour le panneau (matin et soiré ) de maniere constante le matin avec le 100% de puissance de PS et de maniere constante le soirée avec le x% de puissance de ps . 
                   Puissance dans la quelle on va charger la batterie , Energie Batt = YWh 
                   YW-> 1h 
                   ?w-> nb heure de matinée ou de soir 
                   Ce sera le puissance constante de notre batterie  

                   On a deja notre puissance de batterie constante , On a besoinde notre donéé d'utilisation maintenant , On a une boucle pour tout les appareils , on regarde l intervalle d'heure , on prends pour notre puissance de panneau solaire le puissance de notre premier appareil , on passe à la deuxieme appareil , on regarde d'abord si il ya une chevauchement de temps (même 1 minute ) , si oui on ajoute le puissance des deux appareils car sinon le ps ne va pas pouvoir le subvenir , si il n y a pas de chevauchement , on regarde le puissance de deuxieme appareil , si petit que puissance 1 , le panneau peut le subvenir parfaitement , si plus grand  , on le prends comme nouveau puissance , et ainsi de suite on prends en compte le chargement du batterie avec tout ça 
                   Pour le soirée , le puissance de ps / X (cas de 50% de puissance : puissance de ps / 2 ) dois subvenir le besoin pour les appareils de soiree qd on preocede avec les regles suivant , mais sinon , , on prend le puissance trouvée durant soirée et on multiplie par 2 cas de 50% de puissance   , et se sera notre nouvelle puissance 
            -pratique 
                Voici comment le calcul va se derouler :
                  le puissance theorique n'est que le 40% du pratique , 
                  Calculons le pratique 
                  40%-> ptheorique 
                  100%-> ?? ce sera le puissance pratique de notre panneau 
        

Maintenant , on aura plusieurs type de panneau solaire , le pourcentage de panneau solaire n'est pas figées (40% dans notre cas)  
dans la page resultat  ,  ajouter une formulaire qui sert à l'insertion de Panneau solaire (creer une table panneau solaire : nom , pourcentage , Energie unitaire et prix unitaire ) ;
apres avoir inserer le pourcentage du panneau , Il s'affichera  le puissance theorique et pratique de cette panneau , et maintenant il s'affichera le prix du panneau à partir de l'Energie Unitaire , 
On peut inserer plusieurs panneaux , mais quand on clique sur une bouton valider : il s'affichera la proposition du meilleurs choix ( plus petit prix et qui peut subvenir au besoin du menage )
Nouveau modèle PanneauSolaire (nom, pourcentage, energie_unitaire_wh, prix_unitaire)
Table SQL dbo.PanneauxSolaires liée à une session
Logique métier : pour chaque panneau, calculer nb de panneaux nécessaires → prix total → meilleur choix
UI : formulaire d'ajout de panneaux dans l'onglet Résultats, affichage dynamique, bouton "Meilleur choix" 

Assure que tout marche , ajoute une crud appareil et separe la page qui insere les confiqurations 
Fait en sorte qu'on insere bien dans la base  , 



Je veux enlever les rendements dans config , , dans resultat , on va inserer les panneau ,si c seulement un panneau qu on a trouver , ce sera ces resultats qu on va afficher , et sinon  on trouvera le meilleur comme tout à l'heure 

Je veux ajouter une nouvelle fonctionnalité :  
Les energies qu'on n'utilise pas( juste Pour le panneau solaire ) vont être vendu ,le prix de vente de jour ouvrable doit être different de ceux des week--kend , je veux une page qui affiche ces resultats : on doit avoir dans la base le prix de vente de l'nergie en Ar/Wh et different pour jour ouvrable et week-end 
Le calcul global se fera comme suit :pour un panneau de puissance 500w si entre 6 à 8h : on a utilisé 200w ,notre puissance non utilisé = 300w ducoup Energie non utiliser = 600wh . dans l intervalle d'heure ou on utilise rien on aura (500w *(heuredeb-heurefin))  . On somme ces energies et on fait le règle de 3 comme suit :
1wh->prix de vente 
notre somme-> ? 



REVENTE AVEC CHOIX
à propos de revente ,  si on a  fait valider et trouver meilleeur  on va calculer le prix de vente   à partir de ça ,  en prenant compte l'arrodissement , dans notre cas  , nb panneau = 10 mais en vrai c'est 9.86 . on prendra le 9.86  pour le calcul et pour obtenir le surplus 
 on doit  recalculer le puissance theorique à partir du nombre réel du paneau (sans arrondissement) et c'est à partir de ça qu'on cherchera le  surplus .
