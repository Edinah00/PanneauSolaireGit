from __future__ import annotations

import re
from math import ceil

from calcul_metier import (
    calculer_energie_non_utilisee_wh,
    calculer_resultats,
    duree_dans_tranche_heures,
)
from db import DepotSimulationSQLServer
from modeles import (
    Appareil,
    ParametresTranches,
    PanneauSolaire,
    ResultatCalcul,
    ResultatVente,
)


def convertir_nombre(valeur: str, nom_champ: str) -> float:
    texte = valeur.strip().lower().replace(",", ".")
    correspondance = re.search(r"-?\d+(?:\.\d+)?", texte)
    try:
        if correspondance is None:
            raise ValueError
        return float(correspondance.group())
    except ValueError as error:
        raise ValueError(f"Le champ '{nom_champ}' doit etre numerique.") from error


class ControleurApplication:
    def __init__(self) -> None:
        self.appareils: list[Appareil] = []
        self.panneaux: list[PanneauSolaire] = []
        self.depot = DepotSimulationSQLServer()
        self._session_id: int | None = None

    def charger_derniere_session(self) -> ParametresTranches | None:
        """Charge depuis la base la session la plus récente avec ses données."""
        self.depot.initialiser_schema()
        session_id = self.depot.recuperer_derniere_session_id()
        if session_id is None:
            self._session_id = None
            self.appareils = []
            self.panneaux = []
            return None

        self._session_id = session_id
        self.appareils = self.depot.recuperer_appareils(session_id)
        try:
            self.panneaux = self.depot.recuperer_panneaux(session_id)
        except Exception:
            self.panneaux = []

        return self.depot.recuperer_parametres_session(session_id)

    def modifier_configuration(
        self,
        parametres: ParametresTranches,
    ) -> int:
        """Enregistre les paramètres dans la session courante ou en crée une nouvelle."""
        if self._session_id is None:
            self._session_id = self.depot.creer_session_vide(parametres)
            if self.appareils:
                self.depot.synchroniser_appareils(self._session_id, self.appareils)
            if self.panneaux:
                self.depot.synchroniser_panneaux(self._session_id, self.panneaux)
            return self._session_id

        self.depot.mettre_a_jour_parametres_session(self._session_id, parametres)
        return self._session_id

    def _obtenir_ou_creer_session(self, parametres: ParametresTranches) -> int:
        if self._session_id is None:
            self._session_id = self.depot.creer_session_vide(parametres)
        return self._session_id

    def _creer_appareil_depuis_formulaire(
        self,
        nom: str,
        puissance: str,
        tranche: str,
        heure_debut: str,
        heure_fin: str,
        parametres: ParametresTranches,
    ) -> Appareil:
        nom_propre = nom.strip()
        if not nom_propre:
            raise ValueError("Le nom de l'appareil est obligatoire.")

        puissance_watts = convertir_nombre(puissance, "Puissance")
        heure_debut_float = convertir_nombre(heure_debut, "Heure debut")
        heure_fin_float = convertir_nombre(heure_fin, "Heure fin")

        if puissance_watts <= 0:
            raise ValueError("La puissance doit etre strictement positive.")
        if not (0 <= heure_debut_float <= 24 and 0 <= heure_fin_float <= 24):
            raise ValueError("Les heures doivent etre comprises entre 0 et 24.")
        if tranche not in {"matin", "soiree", "nuit"}:
            raise ValueError("La tranche doit etre matin, soiree ou nuit.")

        appareil = Appareil(
            nom=nom_propre,
            puissance_watts=puissance_watts,
            tranche=tranche,
            heure_debut=heure_debut_float,
            heure_fin=heure_fin_float,
        )

        duree_tranche = duree_dans_tranche_heures(appareil, tranche, parametres)
        if duree_tranche <= 0:
            raise ValueError(
                "L'intervalle saisi ne correspond pas a la tranche choisie."
            )

        return appareil

    def ajouter_appareil(
        self,
        nom: str,
        puissance: str,
        tranche: str,
        heure_debut: str,
        heure_fin: str,
        parametres: ParametresTranches,
    ) -> Appareil:
        appareil = self._creer_appareil_depuis_formulaire(
            nom, puissance, tranche, heure_debut, heure_fin, parametres
        )
        self.appareils.append(appareil)
        self._synchroniser_appareils(parametres)
        return appareil

    def modifier_appareil(
        self,
        index: int,
        nom: str,
        puissance: str,
        tranche: str,
        heure_debut: str,
        heure_fin: str,
        parametres: ParametresTranches,
    ) -> Appareil:
        appareil = self._creer_appareil_depuis_formulaire(
            nom, puissance, tranche, heure_debut, heure_fin, parametres
        )
        self.appareils[index] = appareil
        self._synchroniser_appareils(parametres)
        return appareil

    def supprimer_appareil(self, index: int) -> None:
        del self.appareils[index]
        if self._session_id is not None:
            self.depot.synchroniser_appareils(self._session_id, self.appareils)

    def supprimer_panneau(self, index: int) -> None:
        del self.panneaux[index]
        if self._session_id is not None:
            self.depot.synchroniser_panneaux(self._session_id, self.panneaux)

    def creer_parametres(
        self,
        matin_debut: str,
        matin_fin: str,
        soiree_debut: str,
        soiree_fin: str,
        nuit_debut: str,
        nuit_fin: str,
        coefficient_soiree_pourcent: str,
        marge_batterie_pourcent: str,
        rendement_panneau_haut_pourcent: str,
        rendement_panneau_bas_pourcent: str,
        prix_vente_jour_ouvrable_ar_wh: str,
        prix_vente_weekend_ar_wh: str,
    ) -> ParametresTranches:
        parametres = ParametresTranches(
            matin_debut=convertir_nombre(matin_debut, "Matin debut"),
            matin_fin=convertir_nombre(matin_fin, "Matin fin"),
            soiree_debut=convertir_nombre(soiree_debut, "Soiree debut"),
            soiree_fin=convertir_nombre(soiree_fin, "Soiree fin"),
            nuit_debut=convertir_nombre(nuit_debut, "Nuit debut"),
            nuit_fin=convertir_nombre(nuit_fin, "Nuit fin"),
            coefficient_soiree=convertir_nombre(
                coefficient_soiree_pourcent, "Coefficient soiree"
            )
            / 100,
            marge_batterie=convertir_nombre(
                marge_batterie_pourcent, "Marge batterie"
            )
            / 100,
            rendement_panneau_haut=convertir_nombre(
                rendement_panneau_haut_pourcent, "Rendement panneau haut"
            )
            / 100,
            rendement_panneau_bas=convertir_nombre(
                rendement_panneau_bas_pourcent, "Rendement panneau bas"
            )
            / 100,
            prix_vente_jour_ouvrable_ar_wh=convertir_nombre(
                prix_vente_jour_ouvrable_ar_wh, "Prix vente jour ouvrable"
            ),
            prix_vente_weekend_ar_wh=convertir_nombre(
                prix_vente_weekend_ar_wh, "Prix vente week-end"
            ),
        )

        if parametres.coefficient_soiree <= 0 or parametres.coefficient_soiree > 1:
            raise ValueError("Le pourcentage de soiree doit etre entre 1 et 100.")
        if parametres.marge_batterie < 0:
            raise ValueError("La marge batterie doit etre positive ou nulle.")
        if (
            parametres.rendement_panneau_haut <= 0
            or parametres.rendement_panneau_haut > 1
        ):
            raise ValueError("Le rendement panneau haut doit etre entre 1 et 100.")
        if (
            parametres.rendement_panneau_bas <= 0
            or parametres.rendement_panneau_bas > 1
        ):
            raise ValueError("Le rendement panneau bas doit etre entre 1 et 100.")
        if parametres.prix_vente_jour_ouvrable_ar_wh < 0:
            raise ValueError("Le prix de vente jour ouvrable doit etre positif.")
        if parametres.prix_vente_weekend_ar_wh < 0:
            raise ValueError("Le prix de vente week-end doit etre positif.")
        return parametres

    def lancer_calcul(self, parametres: ParametresTranches) -> tuple[ResultatCalcul, str]:
        if not self.appareils:
            raise ValueError("Ajoute au moins un appareil avant de valider.")

        resultat = calculer_resultats(self.appareils, parametres)
        return resultat, "Calcul effectue avec les donnees courantes."

    def ajouter_panneau(
        self,
        nom: str,
        pourcentage: str,
        energie_unitaire: str,
        prix_unitaire: str,
        parametres: ParametresTranches | None = None,
    ) -> PanneauSolaire:
        nom_propre = nom.strip()
        if not nom_propre:
            raise ValueError("Le nom du panneau est obligatoire.")

        pourcentage_float = convertir_nombre(pourcentage, "Pourcentage") / 100
        energie_unitaire_float = convertir_nombre(energie_unitaire, "Energie unitaire")
        prix_unitaire_float = convertir_nombre(prix_unitaire, "Prix unitaire")

        if not (0 < pourcentage_float <= 1):
            raise ValueError("Le pourcentage doit être entre 1 et 100.")
        if energie_unitaire_float <= 0:
            raise ValueError("L'énergie unitaire doit être positive.")
        if prix_unitaire_float <= 0:
            raise ValueError("Le prix unitaire doit être positif.")

        panneau = PanneauSolaire(
            nom=nom_propre,
            pourcentage=pourcentage_float,
            energie_unitaire_wh=energie_unitaire_float,
            prix_unitaire=prix_unitaire_float,
        )

        self.panneaux.append(panneau)
        if parametres is not None:
            self._obtenir_ou_creer_session(parametres)
        self._synchroniser_panneaux()

        return panneau

    def recuperer_panneaux(self) -> list[PanneauSolaire]:
        if self._session_id is not None:
            try:
                return self.depot.recuperer_panneaux(self._session_id)
            except Exception:
                pass
        return list(self.panneaux)

    def calculer_puissance_panneau(
        self,
        panneau: PanneauSolaire,
        puissance_requise: float,
        parametres: ParametresTranches,
    ) -> tuple[float, float, float, int]:
        """Calcule la puissance theorique, pratique, le prix et le nombre de panneaux (arrondi).

        La puissance theorique correspond au besoin issu du calcul global.
        La puissance pratique applique ensuite le rendement du panneau choisi.
        """
        if panneau.pourcentage <= 0:
            raise ValueError("Le pourcentage du panneau doit etre strictement positif.")
        if parametres.rendement_panneau_haut <= 0:
            raise ValueError("Le rendement panneau haut doit etre strictement positif.")

        puissance_theorique = puissance_requise
        puissance_pratique = puissance_theorique / panneau.pourcentage
        nombre_panneaux = 0
        prix_total = 0.0
        if panneau.energie_unitaire_wh > 0:
            nombre_panneaux = max(
                0,
                ceil(puissance_pratique / panneau.energie_unitaire_wh),
            )
            if puissance_requise > 0:
                nombre_panneaux = max(nombre_panneaux, 1)
            prix_total = nombre_panneaux * panneau.prix_unitaire

        return puissance_theorique, puissance_pratique, prix_total, nombre_panneaux

    def calculer_nombre_panneaux_reel(
        self,
        panneau: PanneauSolaire,
        puissance_requise: float,
    ) -> float:
        """Retourne le nombre réel de panneaux (sans arrondi) nécessaires.

        Formule : nb_reel = (puissance_requise / pourcentage) / energie_unitaire_wh
        Ex: puissance_requise=2960W, pourcentage=0.4, energie_unitaire=300Wh
            -> pratique = 2960/0.4 = 7400W
            -> nb_reel  = 7400/300  = 24.67  (on garde 24.67, pas 25)
        """
        if panneau.energie_unitaire_wh <= 0 or panneau.pourcentage <= 0:
            return 0.0
        puissance_pratique = puissance_requise / panneau.pourcentage
        return puissance_pratique / panneau.energie_unitaire_wh

    def trouver_meilleur_panneau(
        self,
        panneaux: list[PanneauSolaire],
        puissance_requise: float,
        parametres: ParametresTranches,
    ) -> PanneauSolaire | None:
        """Trouve le panneau avec le prix le plus bas qui peut subvenir aux besoins."""
        if not panneaux:
            return None

        choix: list[tuple[PanneauSolaire, float]] = []
        for panneau in panneaux:
            _, _, prix_total, nombre_panneaux = self.calculer_puissance_panneau(
                panneau, puissance_requise, parametres
            )
            if nombre_panneaux > 0:
                choix.append((panneau, prix_total))

        if not choix:
            return None

        return min(choix, key=lambda item: item[1])[0]

    def calculer_revente_surplus(
        self,
        panneau: PanneauSolaire,
        puissance_requise: float,
        parametres: ParametresTranches,
    ) -> ResultatVente:
        """Calcule la revente en utilisant le nombre ARRONDI de panneaux achetés.

        Exemple : nb réel = 9,86 → on achète 10 panneaux (arrondi).
        La puissance installée est donc celle de 10 panneaux, pas 9,86.
        Le surplus vient du fait que 10 panneaux produisent plus que nécessaire.

        Puissance pratique installée  = nb_arrondi × energie_unitaire_wh
        Puissance théorique installée = puissance_pratique_installee × pourcentage
        C'est cette puissance théorique installée qui génère le surplus.
        """
        resultat_dimensionnement = calculer_resultats(self.appareils, parametres)

        # Nombre réel (float) et arrondi (int, ce qu'on achète vraiment)
        nombre_reel = self.calculer_nombre_panneaux_reel(panneau, puissance_requise)
        nombre_arrondi = ceil(nombre_reel) if nombre_reel > 0 else 0
        if nombre_arrondi < 1 and puissance_requise > 0:
            nombre_arrondi = 1

        # Puissance réellement installée = celle des panneaux achetés (arrondi)
        puissance_pratique_installee = nombre_arrondi * panneau.energie_unitaire_wh
        puissance_theorique_installee = puissance_pratique_installee * panneau.pourcentage

        energie_non_utilisee_wh = calculer_energie_non_utilisee_wh(
            self.appareils,
            puissance_theorique_installee,
            parametres,
            resultat_dimensionnement.puissance_charge_batterie_w,
        )
        revenu_jour_ouvrable = (
            energie_non_utilisee_wh * parametres.prix_vente_jour_ouvrable_ar_wh
        )
        revenu_weekend = (
            energie_non_utilisee_wh * parametres.prix_vente_weekend_ar_wh
        )
        return ResultatVente(
            nom_panneau=panneau.nom,
            puissance_panneau_theorique_w=puissance_theorique_installee,
            energie_non_utilisee_wh=energie_non_utilisee_wh,
            prix_vente_jour_ouvrable_ar_wh=parametres.prix_vente_jour_ouvrable_ar_wh,
            prix_vente_weekend_ar_wh=parametres.prix_vente_weekend_ar_wh,
            revenu_jour_ouvrable_ar=revenu_jour_ouvrable,
            revenu_weekend_ar=revenu_weekend,
            details={
                "puissance_requise_w": puissance_requise,
                "nombre_panneaux_reel": nombre_reel,
                "nombre_panneaux_arrondi": nombre_arrondi,
                "puissance_panneau_pratique_installee_w": puissance_pratique_installee,
                "puissance_panneau_theorique_requise_w": puissance_requise,
            },
        )

    def calculer_revente_surplus_selon_rendement(
        self,
        puissance_requise: float,
        rendement_pourcent: str,
        parametres: ParametresTranches,
    ) -> ResultatVente:
        """Calcule la revente selon un rendement saisi manuellement (onglet Revente).

        Ici, pas de panneau sélectionné : on utilise la puissance requise telle quelle.
        """
        resultat_dimensionnement = calculer_resultats(self.appareils, parametres)
        rendement = convertir_nombre(rendement_pourcent, "Rendement panneau") / 100
        if rendement <= 0:
            raise ValueError("Le rendement du panneau doit etre strictement positif.")

        puissance_panneau_pratique = puissance_requise / rendement
        energie_non_utilisee_wh = calculer_energie_non_utilisee_wh(
            self.appareils,
            puissance_requise,
            parametres,
            resultat_dimensionnement.puissance_charge_batterie_w,
        )
        revenu_jour_ouvrable = (
            energie_non_utilisee_wh * parametres.prix_vente_jour_ouvrable_ar_wh
        )
        revenu_weekend = (
            energie_non_utilisee_wh * parametres.prix_vente_weekend_ar_wh
        )
        return ResultatVente(
            nom_panneau=f"Panneau {rendement * 100:.0f} %",
            puissance_panneau_theorique_w=puissance_requise,
            energie_non_utilisee_wh=energie_non_utilisee_wh,
            prix_vente_jour_ouvrable_ar_wh=parametres.prix_vente_jour_ouvrable_ar_wh,
            prix_vente_weekend_ar_wh=parametres.prix_vente_weekend_ar_wh,
            revenu_jour_ouvrable_ar=revenu_jour_ouvrable,
            revenu_weekend_ar=revenu_weekend,
            details={
                "puissance_requise_w": puissance_requise,
                "rendement_panneau": rendement,
                "puissance_panneau_pratique_w": puissance_panneau_pratique,
            },
        )

    def tester_base(self) -> str:
        return self.depot.tester_connexion()

    def _synchroniser_appareils(self, parametres: ParametresTranches) -> None:
        session_id = self._obtenir_ou_creer_session(parametres)
        self.depot.synchroniser_appareils(session_id, self.appareils)

    def _synchroniser_panneaux(self) -> None:
        if self._session_id is None:
            return
        self.depot.synchroniser_panneaux(self._session_id, self.panneaux)