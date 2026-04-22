from __future__ import annotations

import customtkinter as ctk

from controleur import ControleurApplication
from modeles import (
    Appareil,
    ParametresTranches,
    PanneauSolaire,
    ResultatCalcul,
    ResultatVente,
)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def formater_nombre(valeur: float) -> str:
    return f"{valeur:,.2f}".replace(",", " ").replace(".", ",")


class ApplicationSolaire(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.controleur = ControleurApplication()
        self.title("ETU004280 - Dimensionnement solaire domestique")
        self.geometry("1220x760")
        self.minsize(1100, 700)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.message_var = ctk.StringVar(value="Pret pour un nouveau calcul.")
        self._appareil_en_edition_index: int | None = None
        self._dernier_parametres: ParametresTranches | None = None
        self._dernier_resultat_vente: ResultatVente | None = None
        self._derniere_puissance_requise: float = 0.0
        self.energie_dispo_var = ctk.StringVar(
            value="Energie dispo estimée: disponible apres un calcul."
        )
        self.revente_estimee_var = ctk.StringVar(
            value="Revente estimée: disponible apres un calcul."
        )
        self.resume_configuration_var = ctk.StringVar(
            value="Aucune configuration chargee pour le moment."
        )
        self.couleurs_resultats = {
            "accent": "#3b82f6",
            "accent_2": "#0ea5a4",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "surface": "#2c323b",
            "surface_alt": "#20242c",
            "text_dim": "#b8c1cc",
        }

        self._creer_entete_etudiant()
        self._creer_onglets()
        self._creer_onglet_configurations()
        self._creer_onglet_appareils()
        self._creer_onglet_resultats()
        self._creer_onglet_revente()
        self._charger_donnees_initiales()
        self.actualiser_liste_appareils()
        self.actualiser_liste_panneaux()
        self.mettre_a_jour_energie_dispo()

    def _creer_entete_etudiant(self) -> None:
        bandeau = ctk.CTkFrame(self, corner_radius=0)
        bandeau.grid(row=0, column=0, sticky="ew")
        bandeau.grid_columnconfigure(0, weight=1)

        titre = ctk.CTkLabel(
            bandeau,
            text="ETU004280 - Dimensionnement solaire domestique",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        titre.grid(row=0, column=0, sticky="w", padx=20, pady=(14, 2))

        sous_titre = ctk.CTkLabel(
            bandeau,
            text="Configurations, appareils, panneaux et meilleur choix dans une seule interface.",
            text_color=self.couleurs_resultats["text_dim"],
        )
        sous_titre.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 14))

    def _creer_onglets(self) -> None:
        self.onglets = ctk.CTkTabview(self, corner_radius=18)
        self.onglets.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        self.onglets.add("Configurations")
        self.onglets.add("Appareils")
        self.onglets.add("Resultats")
        self.onglets.add("Revente")

        self.onglet_configurations = self.onglets.tab("Configurations")
        self.onglet_appareils = self.onglets.tab("Appareils")
        self.onglet_resultats = self.onglets.tab("Resultats")
        self.onglet_revente = self.onglets.tab("Revente")
        self.onglet_configurations.grid_columnconfigure(0, weight=1)
        self.onglet_configurations.grid_rowconfigure(0, weight=1)
        self.onglet_appareils.grid_columnconfigure(0, weight=1)
        self.onglet_appareils.grid_rowconfigure(0, weight=1)
        self.onglet_resultats.grid_columnconfigure(0, weight=1)
        self.onglet_resultats.grid_rowconfigure(0, weight=1)
        self.onglet_revente.grid_columnconfigure(0, weight=1)
        self.onglet_revente.grid_rowconfigure(0, weight=1)

    def _creer_onglet_configurations(self) -> None:
        cadre = ctk.CTkFrame(self.onglet_configurations, corner_radius=18)
        cadre.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        cadre.grid_columnconfigure(1, weight=1)
        cadre.grid_rowconfigure(1, weight=0)

        titre = ctk.CTkLabel(
            cadre,
            text="Configurations de calcul",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        titre.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 10))

        self._creer_resume_configuration(cadre)

        self._creer_parametres(cadre, premiere_ligne=2)

    def _creer_resume_configuration(self, parent: ctk.CTkFrame) -> None:
        cadre_resume = ctk.CTkFrame(parent, corner_radius=14)
        cadre_resume.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 10))
        cadre_resume.grid_columnconfigure(0, weight=1)

        titre = ctk.CTkLabel(
            cadre_resume,
            text="Configuration actuelle",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        titre.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        etiquette = ctk.CTkLabel(
            cadre_resume,
            textvariable=self.resume_configuration_var,
            justify="left",
            anchor="w",
            wraplength=980,
            text_color=self.couleurs_resultats["text_dim"],
        )
        etiquette.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

    def _creer_parametres(self, parent: ctk.CTkFrame, premiere_ligne: int = 0) -> None:
        titre = ctk.CTkLabel(
            parent,
            text="Parametres de calcul",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        titre.grid(
            row=premiere_ligne,
            column=0,
            columnspan=2,
            sticky="w",
            padx=18,
            pady=(18, 10),
        )

        self.entree_matin_debut = self._creer_champ(parent, premiere_ligne + 1, "Matin debut", "6")
        self.entree_matin_fin = self._creer_champ(parent, premiere_ligne + 2, "Matin fin", "17")
        self.entree_soiree_debut = self._creer_champ(parent, premiere_ligne + 3, "Soiree debut", "17")
        self.entree_soiree_fin = self._creer_champ(parent, premiere_ligne + 4, "Soiree fin", "19")
        self.entree_nuit_debut = self._creer_champ(parent, premiere_ligne + 5, "Nuit debut", "19")
        self.entree_nuit_fin = self._creer_champ(parent, premiere_ligne + 6, "Nuit fin", "6")
        self.entree_coeff_soiree = self._creer_champ(
            parent, premiere_ligne + 7, "Puissance soiree (%)", "50"
        )
        self.entree_marge_batterie = self._creer_champ(
            parent, premiere_ligne + 8, "Marge batterie (%)", "50"
        )
        self.entree_rendement_haut = self._creer_champ(
            parent, premiere_ligne + 9, "Rendement panneau haut (%)", "40"
        )
        self.entree_rendement_bas = self._creer_champ(
            parent, premiere_ligne + 10, "Rendement panneau bas (%)", "30"
        )
        self.entree_prix_vente_jour_ouvrable = self._creer_champ(
            parent, premiere_ligne + 11, "Prix vente jour ouvrable (Ar/Wh)", "0"
        )
        self.entree_prix_vente_weekend = self._creer_champ(
            parent, premiere_ligne + 12, "Prix vente week-end (Ar/Wh)", "0"
        )

        self.bouton_modifier_configuration = ctk.CTkButton(
            parent,
            text="Modifier configuration",
            command=self.modifier_configuration,
        )
        self.bouton_modifier_configuration.grid(
            row=premiere_ligne + 13, column=0, columnspan=2, sticky="ew", padx=18, pady=(12, 18)
        )

    def _creer_onglet_appareils(self) -> None:
        cadre = ctk.CTkFrame(self.onglet_appareils, corner_radius=18)
        cadre.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        cadre.grid_columnconfigure(0, weight=1)
        cadre.grid_rowconfigure(1, weight=1)

        self._creer_formulaire_appareil(cadre)
        self._creer_liste_appareils(cadre)

    def _creer_formulaire_appareil(self, parent: ctk.CTkFrame) -> None:
        separateur = ctk.CTkLabel(
            parent,
            text="Nouvel appareil",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        separateur.grid(
            row=11, column=0, columnspan=2, sticky="w", padx=18, pady=(28, 10)
        )

        self.entree_nom = self._creer_champ(parent, 12, "Nom appareil", "Television")
        self.entree_puissance = self._creer_champ(parent, 13, "Puissance (W)", "120")

        etiquette_tranche = ctk.CTkLabel(parent, text="Tranche")
        etiquette_tranche.grid(row=14, column=0, sticky="w", padx=18, pady=8)
        self.selection_tranche = ctk.CTkOptionMenu(
            parent,
            values=["matin", "soiree", "nuit"],
        )
        self.selection_tranche.grid(row=14, column=1, sticky="ew", padx=18, pady=8)
        self.selection_tranche.set("matin")

        self.entree_heure_debut = self._creer_champ(parent, 15, "Heure debut", "8")
        self.entree_heure_fin = self._creer_champ(parent, 16, "Heure fin", "12")

        self.bouton_appareil_principal = ctk.CTkButton(
            parent,
            text="Ajouter appareil",
            command=self.ajouter_appareil,
        )
        self.bouton_appareil_principal.grid(
            row=17, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 8)
        )

        self.bouton_annuler_edition_appareil = ctk.CTkButton(
            parent,
            text="Annuler la modification",
            command=self.annuler_edition_appareil,
            fg_color="#64748b",
            hover_color="#475569",
        )
        self.bouton_annuler_edition_appareil.grid(
            row=18, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 8)
        )
        self.bouton_annuler_edition_appareil.grid_remove()

        bouton_calcul = ctk.CTkButton(
            parent,
            text="Valider et calculer",
            command=self.calculer_et_afficher,
            fg_color="#2e8b57",
            hover_color="#236b43",
        )
        bouton_calcul.grid(
            row=19, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 18)
        )

    def _creer_liste_appareils(self, parent: ctk.CTkFrame) -> None:
        entete_droite = ctk.CTkFrame(parent, fg_color="transparent")
        entete_droite.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        entete_droite.grid_columnconfigure(0, weight=1)

        titre = ctk.CTkLabel(
            entete_droite,
            text="Appareils ajoutes",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        titre.grid(row=0, column=0, sticky="w")

        bouton_db = ctk.CTkButton(
            entete_droite,
            text="Tester SQL Server",
            command=self.tester_connexion_base,
            width=160,
        )
        bouton_db.grid(row=0, column=1, padx=(12, 0))

        self.cadre_liste = ctk.CTkScrollableFrame(parent, corner_radius=12)
        self.cadre_liste.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        self.cadre_liste.grid_columnconfigure(0, weight=1)

        self.etiquette_message = ctk.CTkLabel(
            parent,
            textvariable=self.message_var,
            wraplength=480,
            justify="left",
        )
        self.etiquette_message.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))

    def _creer_onglet_resultats(self) -> None:
        bloc = ctk.CTkFrame(self.onglet_resultats, corner_radius=18)
        bloc.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        bloc.grid_columnconfigure(0, weight=1)
        bloc.grid_columnconfigure(1, weight=1)
        bloc.grid_rowconfigure(0, weight=1)

        # Section résultats
        cadre_resultats = ctk.CTkFrame(bloc, corner_radius=18)
        cadre_resultats.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
        cadre_resultats.grid_columnconfigure(0, weight=1)
        cadre_resultats.grid_rowconfigure(2, weight=1)

        titre_resultats = ctk.CTkLabel(
            cadre_resultats,
            text="Resultats du dimensionnement",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        titre_resultats.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.resume_resultats = ctk.CTkLabel(
            cadre_resultats,
            text="Les resultats apparaitront ici apres validation des donnees courantes.",
            text_color=self.couleurs_resultats["text_dim"],
            justify="left",
        )
        self.resume_resultats.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        self.zone_resultats = ctk.CTkScrollableFrame(
            cadre_resultats,
            corner_radius=16,
            fg_color=self.couleurs_resultats["surface_alt"],
        )
        self.zone_resultats.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.zone_resultats.grid_columnconfigure(0, weight=1)

        # Section panneaux solaires
        cadre_panneaux = ctk.CTkFrame(bloc, corner_radius=18)
        cadre_panneaux.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)
        cadre_panneaux.grid_columnconfigure(0, weight=1)
        cadre_panneaux.grid_rowconfigure(1, weight=1)

        titre_panneaux = ctk.CTkLabel(
            cadre_panneaux,
            text="Proposition de panneaux solaires",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        titre_panneaux.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.zone_panneaux = ctk.CTkScrollableFrame(
            cadre_panneaux,
            corner_radius=16,
            fg_color=self.couleurs_resultats["surface_alt"],
        )
        self.zone_panneaux.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.zone_panneaux.grid_columnconfigure(0, weight=1)

        self._creer_formulaire_panneau(cadre_panneaux)
        self._afficher_etat_resultats_vide()

    def _creer_onglet_revente(self) -> None:
        bloc = ctk.CTkFrame(self.onglet_revente, corner_radius=18)
        bloc.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        bloc.grid_columnconfigure(0, weight=1)
        bloc.grid_rowconfigure(1, weight=0)

        titre = ctk.CTkLabel(
            bloc,
            text="Revente du surplus solaire",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        titre.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.resume_revente = ctk.CTkLabel(
            bloc,
            text=(
                "Saisis seulement le rendement du panneau pour estimer le surplus "
                "et les revenus de revente."
            ),
            text_color=self.couleurs_resultats["text_dim"],
            justify="left",
        )
        self.resume_revente.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        cadre_form = ctk.CTkFrame(bloc, corner_radius=16, fg_color=self.couleurs_resultats["surface_alt"])
        cadre_form.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))
        cadre_form.grid_columnconfigure(1, weight=1)

        titre_form = ctk.CTkLabel(
            cadre_form,
            text="Revente du surplus",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        titre_form.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 10))

        self.entree_rendement_revente = self._creer_champ(
            cadre_form, 1, "Rendement panneau (%)", "40"
        )
        self.entree_rendement_revente.bind(
            "<KeyRelease>", lambda _event: self.mettre_a_jour_revente_estimee()
        )

        self.etiquette_revente_dispo = ctk.CTkLabel(
            cadre_form,
            textvariable=self.revente_estimee_var,
            text_color=self.couleurs_resultats["text_dim"],
            justify="left",
        )
        self.etiquette_revente_dispo.grid(
            row=2, column=0, columnspan=2, sticky="w", padx=18, pady=(6, 0)
        )

        bouton_calcul_revente = ctk.CTkButton(
            cadre_form,
            text="Calculer la revente",
            command=self.calculer_revente_sur_rendement,
            fg_color="#2e8b57",
            hover_color="#236b43",
        )
        bouton_calcul_revente.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(14, 18)
        )

        self.zone_revente = ctk.CTkFrame(
            bloc,
            corner_radius=16,
            fg_color=self.couleurs_resultats["surface_alt"],
        )
        self.zone_revente.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.zone_revente.grid_columnconfigure(0, weight=1)

        self._afficher_revente_vide()

    def _creer_formulaire_panneau(self, parent: ctk.CTkFrame) -> None:
        cadre_form = ctk.CTkFrame(parent, corner_radius=12)
        cadre_form.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))
        cadre_form.grid_columnconfigure(1, weight=1)

        titre_form = ctk.CTkLabel(
            cadre_form,
            text="Ajouter un panneau solaire",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        titre_form.grid(row=0, column=0, columnspan=2, sticky="w", padx=18, pady=(18, 10))

        self.entree_nom_panneau = self._creer_champ(cadre_form, 1, "Nom panneau", "Panneau Standard")
        self.entree_pourcentage_panneau = self._creer_champ(cadre_form, 2, "Pourcentage (%)", "40")
        self.entree_energie_panneau = self._creer_champ(cadre_form, 3, "Energie unitaire (Wh)", "300")
        self.entree_prix_panneau = self._creer_champ(cadre_form, 4, "Prix unitaire (€)", "250")
        self.entree_pourcentage_panneau.bind("<KeyRelease>", lambda _event: self.mettre_a_jour_energie_dispo())

        self.etiquette_energie_dispo = ctk.CTkLabel(
            cadre_form,
            textvariable=self.energie_dispo_var,
            text_color=self.couleurs_resultats["text_dim"],
            justify="left",
        )
        self.etiquette_energie_dispo.grid(
            row=5, column=0, columnspan=2, sticky="w", padx=18, pady=(8, 0)
        )

        bouton_ajouter_panneau = ctk.CTkButton(
            cadre_form,
            text="Ajouter panneau",
            command=self.ajouter_panneau,
        )
        bouton_ajouter_panneau.grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 8)
        )

        bouton_valider_panneaux = ctk.CTkButton(
            cadre_form,
            text="Valider et trouver le meilleur",
            command=self.valider_panneaux,
            fg_color="#2e8b57",
            hover_color="#236b43",
        )
        bouton_valider_panneaux.grid(
            row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(8, 18)
        )

    def _creer_champ(
        self,
        parent: ctk.CTkFrame,
        ligne: int,
        etiquette: str,
        valeur_par_defaut: str,
    ) -> ctk.CTkEntry:
        label = ctk.CTkLabel(parent, text=etiquette)
        label.grid(row=ligne, column=0, sticky="w", padx=18, pady=8)
        entree = ctk.CTkEntry(parent)
        entree.grid(row=ligne, column=1, sticky="ew", padx=18, pady=8)
        entree.insert(0, valeur_par_defaut)
        return entree

    def obtenir_parametres(self) -> ParametresTranches:
        parametres = self.controleur.creer_parametres(
            self.entree_matin_debut.get(),
            self.entree_matin_fin.get(),
            self.entree_soiree_debut.get(),
            self.entree_soiree_fin.get(),
            self.entree_nuit_debut.get(),
            self.entree_nuit_fin.get(),
            self.entree_coeff_soiree.get(),
            self.entree_marge_batterie.get(),
            self.entree_rendement_haut.get(),
            self.entree_rendement_bas.get(),
            self.entree_prix_vente_jour_ouvrable.get(),
            self.entree_prix_vente_weekend.get(),
        )
        self._dernier_parametres = parametres
        return parametres

    def _calculer_energie_dispo_estimee(self) -> str:
        if getattr(self, "_derniere_puissance_requise", 0.0) <= 0:
            return "Energie dispo estimée: disponible apres un calcul."

        try:
            pourcentage = convertir_nombre(
                self.entree_pourcentage_panneau.get(), "Pourcentage"
            ) / 100
        except Exception:
            return "Energie dispo estimée: pourcentage invalide."

        if pourcentage <= 0:
            return "Energie dispo estimée: pourcentage invalide."

        parametres = self._dernier_parametres
        if parametres is None:
            try:
                parametres = self.obtenir_parametres()
            except Exception:
                return "Energie dispo estimée: configuration invalide."

        puissance_theorique = self._derniere_puissance_requise / pourcentage
        puissance_pratique = puissance_theorique / parametres.rendement_panneau_haut

        return (
            "Energie dispo estimée: "
            f"{formater_nombre(puissance_pratique)} W "
            "(puissance pratique du panneau)"
        )

    def mettre_a_jour_energie_dispo(self) -> None:
        self.energie_dispo_var.set(self._calculer_energie_dispo_estimee())

    def _calculer_revente_estimee(self) -> str:
        if getattr(self, "_derniere_puissance_requise", 0.0) <= 0:
            return "Revente estimée: lance d'abord un calcul du dimensionnement."

        try:
            rendement = convertir_nombre(
                self.entree_rendement_revente.get(), "Rendement panneau"
            ) / 100
        except Exception:
            return "Revente estimée: rendement invalide."

        if rendement <= 0:
            return "Revente estimée: rendement invalide."

        puissance_pratique = self._derniere_puissance_requise / rendement
        return (
            "Revente estimée: "
            f"{formater_nombre(self._derniere_puissance_requise)} W de puissance théorique "
            f"et {formater_nombre(puissance_pratique)} W en pratique."
        )

    def mettre_a_jour_revente_estimee(self) -> None:
        self.revente_estimee_var.set(self._calculer_revente_estimee())

    def _mettre_a_jour_resume_configuration(
        self,
        parametres: ParametresTranches,
    ) -> None:
        texte = (
            "Configuration actuelle\n"
            f"Plages: matin {parametres.matin_debut}h -> {parametres.matin_fin}h, "
            f"soiree {parametres.soiree_debut}h -> {parametres.soiree_fin}h, "
            f"nuit {parametres.nuit_debut}h -> {parametres.nuit_fin}h\n"
            f"Coeff. soiree: {formater_nombre(parametres.coefficient_soiree * 100)} % | "
            f"Marge batterie: {formater_nombre(parametres.marge_batterie * 100)} %\n"
            f"Rendement haut/bas: {formater_nombre(parametres.rendement_panneau_haut * 100)} % / "
            f"{formater_nombre(parametres.rendement_panneau_bas * 100)} %\n"
            f"Prix vente: jour ouvrable {formater_nombre(parametres.prix_vente_jour_ouvrable_ar_wh)} Ar/Wh, "
            f"week-end {formater_nombre(parametres.prix_vente_weekend_ar_wh)} Ar/Wh"
        )
        self.resume_configuration_var.set(texte)

    def modifier_configuration(self) -> None:
        try:
            parametres = self.obtenir_parametres()
            self.controleur.modifier_configuration(parametres)
            self._dernier_parametres = parametres
            self._mettre_a_jour_resume_configuration(parametres)
        except Exception as erreur:
            self.message_var.set(str(erreur))
            return

        self.message_var.set("Configuration modifiee et enregistree dans la base.")
        self.actualiser_liste_panneaux()
        self._dernier_resultat_vente = None
        self._afficher_revente_vide()

    def _appliquer_parametres_dans_formulaire(
        self, parametres: ParametresTranches
    ) -> None:
        champs = [
            (self.entree_matin_debut, parametres.matin_debut),
            (self.entree_matin_fin, parametres.matin_fin),
            (self.entree_soiree_debut, parametres.soiree_debut),
            (self.entree_soiree_fin, parametres.soiree_fin),
            (self.entree_nuit_debut, parametres.nuit_debut),
            (self.entree_nuit_fin, parametres.nuit_fin),
            (self.entree_coeff_soiree, parametres.coefficient_soiree * 100),
            (self.entree_marge_batterie, parametres.marge_batterie * 100),
            (self.entree_rendement_haut, parametres.rendement_panneau_haut * 100),
            (self.entree_rendement_bas, parametres.rendement_panneau_bas * 100),
            (
                self.entree_prix_vente_jour_ouvrable,
                parametres.prix_vente_jour_ouvrable_ar_wh,
            ),
            (
                self.entree_prix_vente_weekend,
                parametres.prix_vente_weekend_ar_wh,
            ),
        ]

        for champ, valeur in champs:
            champ.delete(0, "end")
            champ.insert(0, str(valeur))

    def _charger_donnees_initiales(self) -> None:
        parametres = self.controleur.charger_derniere_session()
        if parametres is None:
            self._dernier_parametres = None
            self.resume_configuration_var.set(
                "Aucune configuration chargee pour le moment."
            )
            return

        self._appliquer_parametres_dans_formulaire(parametres)
        self._dernier_parametres = parametres
        self._mettre_a_jour_resume_configuration(parametres)
        self.message_var.set("Configuration courante chargee depuis la base.")
        self.mettre_a_jour_revente_estimee()

    def ajouter_appareil(self) -> None:
        try:
            parametres = self.obtenir_parametres()
            if self._appareil_en_edition_index is None:
                self.controleur.ajouter_appareil(
                    self.entree_nom.get(),
                    self.entree_puissance.get(),
                    self.selection_tranche.get(),
                    self.entree_heure_debut.get(),
                    self.entree_heure_fin.get(),
                    parametres,
                )
                self.message_var.set("Appareil ajoute avec succes.")
            else:
                self.controleur.modifier_appareil(
                    self._appareil_en_edition_index,
                    self.entree_nom.get(),
                    self.entree_puissance.get(),
                    self.selection_tranche.get(),
                    self.entree_heure_debut.get(),
                    self.entree_heure_fin.get(),
                    parametres,
                )
                self.message_var.set("Appareil modifie avec succes.")
                self.annuler_edition_appareil()
        except Exception as erreur:
            self.message_var.set(str(erreur))
            return

        self.entree_nom.delete(0, "end")
        self.entree_puissance.delete(0, "end")
        self.entree_heure_debut.delete(0, "end")
        self.entree_heure_fin.delete(0, "end")
        self.actualiser_liste_appareils()
        self._dernier_resultat_vente = None
        self._afficher_revente_vide()
        self._dernier_resultat_vente = None
        self._afficher_revente_vide()

    def demarrer_edition_appareil(self, index: int) -> None:
        appareil = self.controleur.appareils[index]
        self._appareil_en_edition_index = index
        self.entree_nom.delete(0, "end")
        self.entree_nom.insert(0, appareil.nom)
        self.entree_puissance.delete(0, "end")
        self.entree_puissance.insert(0, str(appareil.puissance_watts))
        self.selection_tranche.set(appareil.tranche)
        self.entree_heure_debut.delete(0, "end")
        self.entree_heure_debut.insert(0, str(appareil.heure_debut))
        self.entree_heure_fin.delete(0, "end")
        self.entree_heure_fin.insert(0, str(appareil.heure_fin))
        self.bouton_appareil_principal.configure(text="Mettre a jour l'appareil")
        self.bouton_annuler_edition_appareil.grid()
        self.message_var.set("Mode modification active pour cet appareil.")

    def annuler_edition_appareil(self) -> None:
        self._appareil_en_edition_index = None
        self.bouton_appareil_principal.configure(text="Ajouter appareil")
        self.bouton_annuler_edition_appareil.grid_remove()

    def actualiser_liste_appareils(self) -> None:
        for widget in self.cadre_liste.winfo_children():
            widget.destroy()

        if not self.controleur.appareils:
            vide = ctk.CTkLabel(
                self.cadre_liste,
                text="Aucun appareil ajoute pour le moment.",
                justify="left",
            )
            vide.grid(row=0, column=0, sticky="w", padx=8, pady=12)
            return

        for index, appareil in enumerate(self.controleur.appareils):
            self._afficher_ligne_appareil(index, appareil)

    def _afficher_ligne_appareil(self, index: int, appareil: Appareil) -> None:
        cadre = ctk.CTkFrame(self.cadre_liste, corner_radius=12)
        cadre.grid(row=index, column=0, sticky="ew", padx=8, pady=8)
        cadre.grid_columnconfigure(0, weight=1)

        description = (
            f"{appareil.nom} | {formater_nombre(appareil.puissance_watts)} W | "
            f"{appareil.tranche} | {appareil.heure_debut}h -> {appareil.heure_fin}h"
        )
        etiquette = ctk.CTkLabel(cadre, text=description, justify="left")
        etiquette.grid(row=0, column=0, sticky="w", padx=12, pady=12)

        bouton_modifier = ctk.CTkButton(
            cadre,
            text="Modifier",
            width=110,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=lambda idx=index: self.demarrer_edition_appareil(idx),
        )
        bouton_modifier.grid(row=0, column=1, padx=(12, 6), pady=12)

        bouton_supprimer = ctk.CTkButton(
            cadre,
            text="Supprimer",
            width=110,
            fg_color="#8b3a3a",
            hover_color="#6f2d2d",
            command=lambda idx=index: self.supprimer_appareil(idx),
        )
        bouton_supprimer.grid(row=0, column=2, padx=(6, 12), pady=12)

    def supprimer_appareil(self, index: int) -> None:
        try:
            if self._appareil_en_edition_index is not None:
                self.annuler_edition_appareil()
            self.controleur.supprimer_appareil(index)
        except Exception as erreur:
            self.message_var.set(str(erreur))
            return

        self.message_var.set("Appareil supprime.")
        self.actualiser_liste_appareils()
        self._dernier_resultat_vente = None
        self._afficher_revente_vide()

    def supprimer_panneau(self, index: int) -> None:
        try:
            self.controleur.supprimer_panneau(index)
        except Exception as erreur:
            self.message_var.set(str(erreur))
            return

        self.message_var.set("Panneau supprime.")
        self.actualiser_liste_panneaux()
        self._dernier_resultat_vente = None
        self._afficher_revente_vide()

    def ajouter_panneau(self) -> None:
        try:
            parametres = self.obtenir_parametres()
            self.controleur.ajouter_panneau(
                self.entree_nom_panneau.get(),
                self.entree_pourcentage_panneau.get(),
                self.entree_energie_panneau.get(),
                self.entree_prix_panneau.get(),
                parametres,
            )
        except Exception as erreur:
            self.message_var.set(str(erreur))
            return

        self.entree_nom_panneau.delete(0, "end")
        self.entree_pourcentage_panneau.delete(0, "end")
        self.entree_energie_panneau.delete(0, "end")
        self.entree_prix_panneau.delete(0, "end")
        self.message_var.set("Panneau ajoute avec succes.")
        self.actualiser_liste_panneaux()
        self.mettre_a_jour_energie_dispo()
        self._dernier_resultat_vente = None
        self._afficher_revente_vide()

    def valider_panneaux(self) -> None:
        try:
            panneaux = self.controleur.recuperer_panneaux()
            if not panneaux:
                self.message_var.set("Aucun panneau ajoute. Veuillez ajouter au moins un panneau.")
                return

            parametres_calcul = self.obtenir_parametres()
            puissance_requise = getattr(self, '_derniere_puissance_requise', 0)
            if puissance_requise == 0:
                try:
                    resultat, message = self.controleur.lancer_calcul(parametres_calcul)
                    self._derniere_puissance_requise = resultat.puissance_panneau_theorique_w
                    self._dernier_parametres = parametres_calcul
                    self._afficher_resultats(resultat, parametres_calcul, message)
                    self.actualiser_liste_panneaux()
                except Exception as calcul_erreur:
                    self.message_var.set(str(calcul_erreur))
                    return

            if len(panneaux) == 1:
                meilleur_panneau = panneaux[0]
            else:
                meilleur_panneau = self.controleur.trouver_meilleur_panneau(
                    panneaux, self._derniere_puissance_requise, parametres_calcul
                )

            if meilleur_panneau:
                (
                    puissance_theorique,
                    puissance_pratique,
                    prix_total,
                    nombre_panneaux,
                ) = self.controleur.calculer_puissance_panneau(
                    meilleur_panneau,
                    self._derniere_puissance_requise,
                    parametres_calcul,
                )
                self._afficher_meilleur_panneau(
                    meilleur_panneau,
                    puissance_theorique,
                    puissance_pratique,
                    prix_total,
                    nombre_panneaux,
                )
                resultat_vente = self.controleur.calculer_revente_surplus(
                    meilleur_panneau,
                    self._derniere_puissance_requise,
                    parametres_calcul,
                )
                self._dernier_resultat_vente = resultat_vente
                self._afficher_revente(resultat_vente)
                self.mettre_a_jour_energie_dispo()
                if len(panneaux) == 1:
                    self.message_var.set(f"Panneau trouve: {meilleur_panneau.nom}")
                else:
                    self.message_var.set(f"Meilleur panneau trouve: {meilleur_panneau.nom}")
                self.onglets.set("Revente")
            else:
                self.message_var.set("Aucun panneau ne peut subvenir aux besoins energetiques.")
        except Exception as erreur:
            self.message_var.set(str(erreur))

    def calculer_revente_sur_rendement(self) -> None:
        try:
            parametres = self.obtenir_parametres()
            if getattr(self, "_derniere_puissance_requise", 0.0) <= 0:
                resultat, message = self.controleur.lancer_calcul(parametres)
                self._derniere_puissance_requise = resultat.puissance_panneau_theorique_w
                self._dernier_parametres = parametres
                self._afficher_resultats(resultat, parametres, message)
            resultat_vente = self.controleur.calculer_revente_surplus_selon_rendement(
                self._derniere_puissance_requise,
                self.entree_rendement_revente.get(),
                parametres,
            )
            self._dernier_resultat_vente = resultat_vente
            self._afficher_revente(resultat_vente)
            self.mettre_a_jour_revente_estimee()
            self.message_var.set("Revente estimee calculee avec le rendement du panneau.")
            self.onglets.set("Revente")
        except Exception as erreur:
            self.message_var.set(str(erreur))

    def actualiser_liste_panneaux(self) -> None:
        for widget in self.zone_panneaux.winfo_children():
            widget.destroy()

        panneaux = self.controleur.recuperer_panneaux()
        if not panneaux:
            vide = ctk.CTkLabel(
                self.zone_panneaux,
                text="Aucun panneau ajoute pour le moment.",
                justify="left",
            )
            vide.grid(row=0, column=0, sticky="w", padx=8, pady=12)
            return

        for index, panneau in enumerate(panneaux):
            self._afficher_ligne_panneau(index, panneau)

    def _afficher_ligne_panneau(self, index: int, panneau: PanneauSolaire) -> None:
        cadre = ctk.CTkFrame(self.zone_panneaux, corner_radius=12)
        cadre.grid(row=index, column=0, sticky="ew", padx=8, pady=8)
        cadre.grid_columnconfigure(0, weight=1)

        description = (
            f"{panneau.nom} | {formater_nombre(panneau.pourcentage * 100)}% | "
            f"{formater_nombre(panneau.energie_unitaire_wh)} Wh | {formater_nombre(panneau.prix_unitaire)} €"
        )
        etiquette = ctk.CTkLabel(cadre, text=description, justify="left")
        etiquette.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        bouton_supprimer = ctk.CTkButton(
            cadre,
            text="Supprimer",
            width=110,
            fg_color="#8b3a3a",
            hover_color="#6f2d2d",
            command=lambda idx=index: self.supprimer_panneau(idx),
        )
        bouton_supprimer.grid(row=0, column=1, padx=12, pady=12)

        # Afficher les calculs si la puissance requise est disponible
        parametres = self._dernier_parametres
        if parametres is None:
            try:
                parametres = self.obtenir_parametres()
            except Exception:
                parametres = None
        if (
            parametres is not None
            and hasattr(self, "_derniere_puissance_requise")
            and self._derniere_puissance_requise > 0
        ):
            (
                puissance_theorique,
                puissance_pratique,
                prix_total,
                nombre_panneaux,
            ) = self.controleur.calculer_puissance_panneau(
                panneau,
                self._derniere_puissance_requise,
                parametres,
            )
            calculs = (
                f"P. theorique: {formater_nombre(puissance_theorique)} W | "
                f"P. pratique: {formater_nombre(puissance_pratique)} W | "
                f"Nb de panneaux: {nombre_panneaux} | "
                f"Prix: {formater_nombre(prix_total)} €"
            )
            etiquette_calculs = ctk.CTkLabel(
                cadre,
                text=calculs,
                justify="left",
                text_color=self.couleurs_resultats["text_dim"],
                font=ctk.CTkFont(size=12),
            )
            etiquette_calculs.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 12))

    def _afficher_meilleur_panneau(
        self,
        panneau: PanneauSolaire,
        puissance_theorique: float,
        puissance_pratique: float,
        prix_total: float,
        nombre_panneaux: int,
    ) -> None:
        if hasattr(self, '_cadre_meilleur_panneau'):
            self._cadre_meilleur_panneau.destroy()

        cadre_meilleur = ctk.CTkFrame(
            self.zone_panneaux,
            corner_radius=12,
            fg_color="#22c55e",
        )
        cadre_meilleur.grid(row=100, column=0, sticky="ew", padx=8, pady=8)
        cadre_meilleur.grid_columnconfigure(0, weight=1)
        self._cadre_meilleur_panneau = cadre_meilleur

        titre = ctk.CTkLabel(
            cadre_meilleur,
            text="🏆 Meilleur panneau recommande",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        titre.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 8))

        details = (
            f"Nom: {panneau.nom}\n"
            f"Puissance theorique: {formater_nombre(puissance_theorique)} W\n"
            f"Puissance pratique: {formater_nombre(puissance_pratique)} W\n"
            f"Nombre de panneaux: {nombre_panneaux}\n"
            f"Prix total: {formater_nombre(prix_total)} €"
        )
        etiquette_details = ctk.CTkLabel(
            cadre_meilleur,
            text=details,
            justify="left",
        )
        etiquette_details.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 12))

    def calculer_et_afficher(self) -> None:
        try:
            parametres = self.obtenir_parametres()
            resultat, message = self.controleur.lancer_calcul(parametres)
        except Exception as erreur:
            self.message_var.set(str(erreur))
            return

        self._derniere_puissance_requise = resultat.puissance_panneau_theorique_w
        self._dernier_parametres = parametres
        self._afficher_resultats(resultat, parametres, message)
        self.actualiser_liste_panneaux()
        self.mettre_a_jour_energie_dispo()
        self._dernier_resultat_vente = None
        self._afficher_revente_vide()
        self.message_var.set(message)
        self.onglets.set("Resultats")

    def _afficher_resultats(
        self,
        resultat: ResultatCalcul,
        parametres: ParametresTranches,
        message: str,
    ) -> None:
        # Stocker la puissance requise pour les panneaux
        self._derniere_puissance_requise = resultat.puissance_panneau_theorique_w

        self.resume_resultats.configure(
            text=(
                "Calcul termine. Les indicateurs essentiels sont regroupes ci-dessous."
            ),
            text_color="white",
        )

        for widget in self.zone_resultats.winfo_children():
            widget.destroy()

        tableau = ctk.CTkFrame(self.zone_resultats, corner_radius=12, fg_color="transparent")
        tableau.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        tableau.grid_columnconfigure(0, weight=1, uniform="resultats")
        tableau.grid_columnconfigure(1, weight=1, uniform="resultats")

        self._creer_tuile_resultat_compacte(
            tableau,
            0,
            0,
            "Batterie theorique",
            f"{formater_nombre(resultat.batterie_theorique_wh)} Wh",
            self.couleurs_resultats["success"],
        )
        self._creer_tuile_resultat_compacte(
            tableau,
            0,
            1,
            "Batterie pratique",
            f"{formater_nombre(resultat.batterie_pratique_wh)} Wh",
            "#14532d",
        )
        self._creer_tuile_resultat_compacte(
            tableau,
            1,
            0,
            "Panneau theorique",
            f"{formater_nombre(resultat.puissance_panneau_theorique_w)} W",
            self.couleurs_resultats["warning"],
        )
        self._creer_tuile_resultat_compacte(
            tableau,
            1,
            1,
            "Panneau rendement haut",
            f"{formater_nombre(resultat.puissance_panneau_rendement_haut_w)} W",
            self.couleurs_resultats["accent"],
        )
        self._creer_tuile_resultat_compacte(
            tableau,
            2,
            0,
            "Convertisseur",
            f"{formater_nombre(resultat.puissance_convertisseur_w)} W",
            "#7c3aed",
        )
        self._creer_tuile_resultat_compacte(
            tableau,
            2,
            1,
            "SQL / Etat",
            message,
            "#64748b",
            petite_valeur=True,
        )

        cartes = ctk.CTkFrame(self.zone_resultats, corner_radius=12, fg_color="transparent")
        cartes.grid(row=1, column=0, sticky="ew", padx=4, pady=(4, 4))
        cartes.grid_columnconfigure(0, weight=1, uniform="cartes")
        cartes.grid_columnconfigure(1, weight=1, uniform="cartes")

        self._creer_carte_resultat(
            cartes,
            0,
            "Energie par tranche",
            self.couleurs_resultats["accent_2"],
            [
                ("Matin", f"{formater_nombre(resultat.energie_matin_wh)} Wh"),
                ("Soiree", f"{formater_nombre(resultat.energie_soiree_wh)} Wh"),
                ("Nuit", f"{formater_nombre(resultat.energie_nuit_wh)} Wh"),
            ],
        )
        self._creer_carte_resultat(
            cartes,
            1,
            "Batterie / Pointe",
            self.couleurs_resultats["success"],
            [
                ("Charge batterie", f"{formater_nombre(resultat.puissance_charge_batterie_w)} W"),
                ("Pic journee", f"{formater_nombre(resultat.puissance_appareils_matin_w)} W"),
                ("Pic soiree", f"{formater_nombre(resultat.puissance_appareils_soiree_w)} W"),
            ],
        )

        infos = ctk.CTkFrame(self.zone_resultats, corner_radius=12, fg_color="transparent")
        infos.grid(row=2, column=0, sticky="ew", padx=4, pady=(4, 4))
        infos.grid_columnconfigure(0, weight=1, uniform="infos")
        infos.grid_columnconfigure(1, weight=1, uniform="infos")

        self._creer_carte_resultat(
            infos,
            0,
            "Parametres utilises",
            "#8b5cf6",
            [
                ("Matin", f"{parametres.matin_debut}h -> {parametres.matin_fin}h"),
                ("Soiree", f"{parametres.soiree_debut}h -> {parametres.soiree_fin}h"),
                ("Nuit", f"{parametres.nuit_debut}h -> {parametres.nuit_fin}h"),
            ],
        )
        self._creer_carte_resultat(
            infos,
            1,
            "Lecture rapide",
            "#0f766e",
            [
                ("1", "La batterie de nuit fixe le besoin principal."),
                ("2", "Le panneau couvre les usages et la recharge."),
                ("3", "Le convertisseur prend le plus fort pic."),
            ],
        )

    def _afficher_etat_resultats_vide(self) -> None:
        for widget in self.zone_resultats.winfo_children():
            widget.destroy()

        carte_vide = ctk.CTkFrame(
            self.zone_resultats,
            corner_radius=18,
            fg_color=self.couleurs_resultats["surface"],
        )
        carte_vide.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        carte_vide.grid_columnconfigure(0, weight=1)

        titre = ctk.CTkLabel(
            carte_vide,
            text="Pret pour le calcul",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        titre.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 8))

        description = ctk.CTkLabel(
            carte_vide,
            text=(
                "Ajoutez vos appareils, puis cliquez sur 'Valider et calculer' pour "
                "obtenir un resume plus visuel du panneau solaire et de la batterie."
            ),
            justify="left",
            wraplength=760,
            text_color=self.couleurs_resultats["text_dim"],
        )
        description.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 18))

    def _afficher_revente_vide(self) -> None:
        for widget in self.zone_revente.winfo_children():
            widget.destroy()

        carte_vide = ctk.CTkFrame(
            self.zone_revente,
            corner_radius=18,
            fg_color=self.couleurs_resultats["surface"],
        )
        carte_vide.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        carte_vide.grid_columnconfigure(0, weight=1)

        titre = ctk.CTkLabel(
            carte_vide,
            text="Revente journalière du surplus",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        titre.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 8))

        description = ctk.CTkLabel(
            carte_vide,
            text="Le tarif Ar/Wh et le montant vendu pour une journée s'afficheront ici pour jour ouvrable et week-end.",
            justify="left",
            wraplength=760,
            text_color=self.couleurs_resultats["text_dim"],
        )
        description.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 18))

    def _afficher_revente(self, resultat: ResultatVente) -> None:
        for widget in self.zone_revente.winfo_children():
            widget.destroy()

        carte = ctk.CTkFrame(
            self.zone_revente,
            corner_radius=18,
            fg_color=self.couleurs_resultats["surface"],
        )
        carte.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        carte.grid_columnconfigure(0, weight=1)

        resume = ctk.CTkLabel(
            carte,
            text=(
                f"Panneau retenu: {resultat.nom_panneau}\n"
                f"Puissance théorique: {formater_nombre(resultat.puissance_panneau_theorique_w)} W\n"
                f"Energie non utilisée: {formater_nombre(resultat.energie_non_utilisee_wh)} Wh"
            ),
            justify="left",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        resume.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        grille = ctk.CTkFrame(carte, corner_radius=12, fg_color="transparent")
        grille.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        grille.grid_columnconfigure(0, weight=1, uniform="rev")
        grille.grid_columnconfigure(1, weight=1, uniform="rev")

        elements = [
            (
                "Prix jour ouvrable",
                f"{formater_nombre(resultat.prix_vente_jour_ouvrable_ar_wh)} Ar/Wh",
                self.couleurs_resultats["accent_2"],
            ),
            (
                "Prix week-end",
                f"{formater_nombre(resultat.prix_vente_weekend_ar_wh)} Ar/Wh",
                self.couleurs_resultats["accent_2"],
            ),
            (
                "Montant jour ouvrable",
                f"{formater_nombre(resultat.revenu_jour_ouvrable_ar)} Ar / jour",
                self.couleurs_resultats["success"],
            ),
            (
                "Montant week-end",
                f"{formater_nombre(resultat.revenu_weekend_ar)} Ar / jour",
                self.couleurs_resultats["success"],
            ),
        ]

        for index, (titre, valeur, couleur) in enumerate(elements):
            ligne = index // 2
            colonne = index % 2
            self._creer_tuile_resultat_compacte(
                grille,
                ligne,
                colonne,
                titre,
                valeur,
                couleur,
                petite_valeur=True,
            )

    def _creer_bandeau_resultat(
        self,
        ligne: int,
        titre: str,
        valeur: str,
        description: str,
        couleur: str,
    ) -> None:
        cadre = ctk.CTkFrame(
            self.zone_resultats,
            corner_radius=18,
            fg_color=couleur,
        )
        cadre.grid(row=ligne, column=0, sticky="ew", padx=4, pady=(4, 10))
        cadre.grid_columnconfigure(0, weight=1)

        etiquette_titre = ctk.CTkLabel(
            cadre,
            text=titre,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        etiquette_titre.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))

        etiquette_valeur = ctk.CTkLabel(
            cadre,
            text=valeur,
            font=ctk.CTkFont(size=30, weight="bold"),
        )
        etiquette_valeur.grid(row=1, column=0, sticky="w", padx=18, pady=4)

        etiquette_desc = ctk.CTkLabel(
            cadre,
            text=description,
            justify="left",
        )
        etiquette_desc.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 16))

    def _creer_tuile_resultat_compacte(
        self,
        parent: ctk.CTkFrame,
        ligne: int,
        colonne: int,
        titre: str,
        valeur: str,
        couleur: str,
        petite_valeur: bool = False,
    ) -> None:
        cadre = ctk.CTkFrame(parent, corner_radius=14, fg_color=couleur)
        cadre.grid(row=ligne, column=colonne, sticky="ew", padx=6, pady=6)
        cadre.grid_columnconfigure(0, weight=1)

        etiquette_titre = ctk.CTkLabel(
            cadre,
            text=titre,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        etiquette_titre.grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))

        etiquette_valeur = ctk.CTkLabel(
            cadre,
            text=valeur,
            font=ctk.CTkFont(size=22 if not petite_valeur else 14, weight="bold"),
            wraplength=360,
            justify="left",
        )
        etiquette_valeur.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

    def _creer_carte_resultat(
        self,
        parent: ctk.CTkFrame,
        colonne: int,
        titre: str,
        couleur: str,
        lignes: list[tuple[str, str]],
    ) -> None:
        carte = ctk.CTkFrame(
            parent,
            corner_radius=18,
            fg_color=self.couleurs_resultats["surface"],
        )
        carte.grid(row=0, column=colonne, sticky="ew", padx=6, pady=6)
        carte.grid_columnconfigure(0, weight=1)

        entete = ctk.CTkFrame(carte, corner_radius=14, fg_color=couleur)
        entete.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        entete.grid_columnconfigure(0, weight=1)

        titre_carte = ctk.CTkLabel(
            entete,
            text=titre,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        titre_carte.grid(row=0, column=0, sticky="w", padx=12, pady=8)

        for index, (libelle, valeur) in enumerate(lignes, start=1):
            ligne_cadre = ctk.CTkFrame(
                carte,
                corner_radius=12,
                fg_color=self.couleurs_resultats["surface_alt"],
            )
            ligne_cadre.grid(row=index, column=0, sticky="ew", padx=12, pady=4)
            ligne_cadre.grid_columnconfigure(0, weight=1)

            etiquette_libelle = ctk.CTkLabel(
                ligne_cadre,
                text=libelle,
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            etiquette_libelle.grid(row=0, column=0, sticky="w", padx=12, pady=8)

            etiquette_valeur = ctk.CTkLabel(
                ligne_cadre,
                text=valeur,
                justify="right",
                wraplength=300,
                text_color=self.couleurs_resultats["text_dim"],
                font=ctk.CTkFont(size=13),
            )
            etiquette_valeur.grid(row=0, column=1, sticky="e", padx=12, pady=8)

    def _creer_carte_resultat_surplus(
        self,
        parent: ctk.CTkFrame,
        ligne: int,
        titre: str,
        couleur: str,
        lignes: list[tuple[str, str]],
    ) -> None:
        carte = ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=self.couleurs_resultats["surface_alt"],
        )
        carte.grid(row=ligne, column=0, sticky="ew", padx=12, pady=5)
        carte.grid_columnconfigure(0, weight=1)

        entete = ctk.CTkFrame(carte, corner_radius=14, fg_color=couleur)
        entete.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        entete.grid_columnconfigure(0, weight=1)

        titre_carte = ctk.CTkLabel(
            entete,
            text=titre,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        titre_carte.grid(row=0, column=0, sticky="w", padx=12, pady=8)

        for index, (libelle, valeur) in enumerate(lignes, start=1):
            ligne_cadre = ctk.CTkFrame(
                carte,
                corner_radius=12,
                fg_color=self.couleurs_resultats["surface_alt"],
            )
            ligne_cadre.grid(row=index, column=0, sticky="ew", padx=12, pady=4)
            ligne_cadre.grid_columnconfigure(0, weight=1)

            etiquette_libelle = ctk.CTkLabel(
                ligne_cadre,
                text=libelle,
                font=ctk.CTkFont(size=13, weight="bold"),
            )
            etiquette_libelle.grid(row=0, column=0, sticky="w", padx=12, pady=8)

            etiquette_valeur = ctk.CTkLabel(
                ligne_cadre,
                text=valeur,
                justify="right",
                wraplength=300,
                text_color=self.couleurs_resultats["text_dim"],
                font=ctk.CTkFont(size=13),
            )
            etiquette_valeur.grid(row=0, column=1, sticky="e", padx=12, pady=8)

    def tester_connexion_base(self) -> None:
        try:
            base = self.controleur.tester_base()
            self.message_var.set(f"Connexion SQL Server reussie sur la base: {base}")
        except Exception as erreur:
            self.message_var.set(f"Connexion SQL Server impossible: {erreur}")
