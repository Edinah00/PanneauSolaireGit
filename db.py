from __future__ import annotations

import os
from datetime import datetime

from modeles import Appareil, ParametresTranches, ResultatCalcul, PanneauSolaire

try:
    import pyodbc
except ImportError:
    pyodbc = None


def obtenir_connexion():
    if pyodbc is None:
        raise RuntimeError(
            "Le module pyodbc n'est pas installe. Lance: ./venv/bin/pip install pyodbc"
        )

    serveur = os.getenv("DB_SERVER", "localhost,1433")
    base = os.getenv("DB_NAME", "PanneauSolaire")
    utilisateur = os.getenv("DB_USER", "sa")
    mot_de_passe = os.getenv("DB_PASSWORD", "'MonMotDePasseFort2026'")  # Changez ce mot de passe par défaut en production
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    chaine_connexion = (
        f"DRIVER={{{driver}}};"
        f"SERVER={serveur};"
        f"DATABASE={base};"
        f"UID={utilisateur};"
        f"PWD={mot_de_passe};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(chaine_connexion, timeout=5)


class DepotSimulationSQLServer:
    def tester_connexion(self) -> str:
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute("SELECT DB_NAME()")
            ligne = curseur.fetchone()
            return ligne[0] if ligne else "Connexion reussie"

    def initialiser_schema(self) -> None:
        requete = """
        IF OBJECT_ID('dbo.Sessions', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.Sessions (
                id INT IDENTITY(1,1) PRIMARY KEY,
                date_creation DATETIME2 NOT NULL,
                matin_debut FLOAT NOT NULL,
                matin_fin FLOAT NOT NULL,
                soiree_debut FLOAT NOT NULL,
                soiree_fin FLOAT NOT NULL,
                nuit_debut FLOAT NOT NULL,
                nuit_fin FLOAT NOT NULL,
                coefficient_soiree FLOAT NOT NULL,
                marge_batterie FLOAT NOT NULL DEFAULT 0.5,
                rendement_panneau_haut FLOAT NOT NULL DEFAULT 0.4,
                rendement_panneau_bas FLOAT NOT NULL DEFAULT 0.3,
                prix_vente_jour_ouvrable_ar_wh FLOAT NOT NULL DEFAULT 0,
                prix_vente_weekend_ar_wh FLOAT NOT NULL DEFAULT 0
            );
        END;

        IF COL_LENGTH('dbo.Sessions', 'marge_batterie') IS NULL
            ALTER TABLE dbo.Sessions ADD marge_batterie FLOAT NOT NULL DEFAULT 0.5;
        IF COL_LENGTH('dbo.Sessions', 'rendement_panneau_haut') IS NULL
            ALTER TABLE dbo.Sessions ADD rendement_panneau_haut FLOAT NOT NULL DEFAULT 0.4;
        IF COL_LENGTH('dbo.Sessions', 'rendement_panneau_bas') IS NULL
            ALTER TABLE dbo.Sessions ADD rendement_panneau_bas FLOAT NOT NULL DEFAULT 0.3;
        IF COL_LENGTH('dbo.Sessions', 'prix_vente_jour_ouvrable_ar_wh') IS NULL
            ALTER TABLE dbo.Sessions ADD prix_vente_jour_ouvrable_ar_wh FLOAT NOT NULL DEFAULT 0;
        IF COL_LENGTH('dbo.Sessions', 'prix_vente_weekend_ar_wh') IS NULL
            ALTER TABLE dbo.Sessions ADD prix_vente_weekend_ar_wh FLOAT NOT NULL DEFAULT 0;

        IF OBJECT_ID('dbo.Appareils', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.Appareils (
                id INT IDENTITY(1,1) PRIMARY KEY,
                session_id INT NOT NULL FOREIGN KEY REFERENCES dbo.Sessions(id),
                nom NVARCHAR(120) NOT NULL,
                puissance_watts FLOAT NOT NULL,
                tranche NVARCHAR(30) NOT NULL,
                heure_debut FLOAT NOT NULL,
                heure_fin FLOAT NOT NULL
            );
        END;

        IF OBJECT_ID('dbo.Resultats', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.Resultats (
                id INT IDENTITY(1,1) PRIMARY KEY,
                session_id INT NOT NULL FOREIGN KEY REFERENCES dbo.Sessions(id),
                energie_matin_wh FLOAT NOT NULL,
                energie_soiree_wh FLOAT NOT NULL,
                energie_nuit_wh FLOAT NOT NULL,
                batterie_theorique_wh FLOAT NOT NULL,
                batterie_pratique_wh FLOAT NOT NULL,
                puissance_panneau_theorique_w FLOAT NOT NULL,
                puissance_panneau_rendement_haut_w FLOAT NOT NULL,
                puissance_panneau_rendement_bas_w FLOAT NOT NULL,
                puissance_convertisseur_w FLOAT NOT NULL
            );
        END;

        IF OBJECT_ID('dbo.PanneauxSolaires', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.PanneauxSolaires (
                id INT IDENTITY(1,1) PRIMARY KEY,
                session_id INT NOT NULL FOREIGN KEY REFERENCES dbo.Sessions(id),
                nom NVARCHAR(120) NOT NULL,
                pourcentage FLOAT NOT NULL,
                energie_unitaire_wh FLOAT NOT NULL,
                prix_unitaire FLOAT NOT NULL
            );
        END;

        IF COL_LENGTH('dbo.Resultats', 'puissance_panneau_rendement_haut_w') IS NULL
            ALTER TABLE dbo.Resultats ADD puissance_panneau_rendement_haut_w FLOAT NOT NULL DEFAULT 0;
        IF COL_LENGTH('dbo.Resultats', 'puissance_panneau_rendement_bas_w') IS NULL
            ALTER TABLE dbo.Resultats ADD puissance_panneau_rendement_bas_w FLOAT NOT NULL DEFAULT 0;
        IF COL_LENGTH('dbo.Resultats', 'puissance_convertisseur_w') IS NULL
            ALTER TABLE dbo.Resultats ADD puissance_convertisseur_w FLOAT NOT NULL DEFAULT 0;
        """

        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(requete)
            connexion.commit()

    def enregistrer_appareil_seul(
        self,
        appareil: Appareil,
        session_id: int,
    ) -> None:
        """Insère un appareil dans une session existante."""
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                INSERT INTO dbo.Appareils (
                    session_id,
                    nom,
                    puissance_watts,
                    tranche,
                    heure_debut,
                    heure_fin
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                session_id,
                appareil.nom,
                appareil.puissance_watts,
                appareil.tranche,
                appareil.heure_debut,
                appareil.heure_fin,
            )
            connexion.commit()

    def synchroniser_appareils(
        self,
        session_id: int,
        appareils: list[Appareil],
    ) -> None:
        """Remplace les appareils d'une session par l'état courant en mémoire."""
        self.initialiser_schema()
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                "DELETE FROM dbo.Appareils WHERE session_id = ?",
                session_id,
            )
            for appareil in appareils:
                curseur.execute(
                    """
                    INSERT INTO dbo.Appareils (
                        session_id,
                        nom,
                        puissance_watts,
                        tranche,
                        heure_debut,
                        heure_fin
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    session_id,
                    appareil.nom,
                    appareil.puissance_watts,
                    appareil.tranche,
                    appareil.heure_debut,
                    appareil.heure_fin,
                )
            connexion.commit()

    def creer_session_vide(self, parametres: ParametresTranches) -> int:
        """Crée une session sans appareils ni résultats et retourne son id."""
        self.initialiser_schema()
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                INSERT INTO dbo.Sessions (
                    date_creation,
                    matin_debut, matin_fin,
                    soiree_debut, soiree_fin,
                    nuit_debut, nuit_fin,
                    coefficient_soiree,
                    marge_batterie,
                    rendement_panneau_haut,
                    rendement_panneau_bas,
                    prix_vente_jour_ouvrable_ar_wh,
                    prix_vente_weekend_ar_wh
                )
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                __import__("datetime").datetime.now(),
                parametres.matin_debut, parametres.matin_fin,
                parametres.soiree_debut, parametres.soiree_fin,
                parametres.nuit_debut, parametres.nuit_fin,
                parametres.coefficient_soiree,
                parametres.marge_batterie,
                parametres.rendement_panneau_haut,
                parametres.rendement_panneau_bas,
                parametres.prix_vente_jour_ouvrable_ar_wh,
                parametres.prix_vente_weekend_ar_wh,
            )
            session_id = int(curseur.fetchone()[0])
            connexion.commit()
        return session_id

    def enregistrer_simulation(
        self,
        appareils: list[Appareil],
        parametres: ParametresTranches,
        resultat: ResultatCalcul,
    ) -> int:
        self.initialiser_schema()

        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                INSERT INTO dbo.Sessions (
                    date_creation,
                    matin_debut,
                    matin_fin,
                    soiree_debut,
                    soiree_fin,
                    nuit_debut,
                    nuit_fin,
                    coefficient_soiree,
                    marge_batterie,
                    rendement_panneau_haut,
                    rendement_panneau_bas,
                    prix_vente_jour_ouvrable_ar_wh,
                    prix_vente_weekend_ar_wh
                )
                OUTPUT INSERTEéD.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                datetime.now(),
                parametres.matin_debut,
                parametres.matin_fin,
                parametres.soiree_debut,
                parametres.soiree_fin,
                parametres.nuit_debut,
                parametres.nuit_fin,
                parametres.coefficient_soiree,
                parametres.marge_batterie,
                parametres.rendement_panneau_haut,
                parametres.rendement_panneau_bas,
                parametres.prix_vente_jour_ouvrable_ar_wh,
                parametres.prix_vente_weekend_ar_wh,
            )
            session_id = int(curseur.fetchone()[0])

            for appareil in appareils:
                curseur.execute(
                    """
                    INSERT INTO dbo.Appareils (
                        session_id,
                        nom,
                        puissance_watts,
                        tranche,
                        heure_debut,
                        heure_fin
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    session_id,
                    appareil.nom,
                    appareil.puissance_watts,
                    appareil.tranche,
                    appareil.heure_debut,
                    appareil.heure_fin,
                )

            curseur.execute(
                """
                INSERT INTO dbo.Resultats (
                    session_id,
                    energie_matin_wh,
                    energie_soiree_wh,
                    energie_nuit_wh,
                    batterie_theorique_wh,
                    batterie_pratique_wh,
                    puissance_panneau_theorique_w,
                    puissance_panneau_rendement_haut_w,
                    puissance_panneau_rendement_bas_w,
                    puissance_convertisseur_w
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                session_id,
                resultat.energie_matin_wh,
                resultat.energie_soiree_wh,
                resultat.energie_nuit_wh,
                resultat.batterie_theorique_wh,
                resultat.batterie_pratique_wh,
                resultat.puissance_panneau_theorique_w,
                resultat.puissance_panneau_rendement_haut_w,
                resultat.puissance_panneau_rendement_bas_w,
                resultat.puissance_convertisseur_w,
            )
            connexion.commit()

    def recuperer_derniere_session_id(self) -> int | None:
        """Retourne l'identifiant de la session la plus récente."""
        self.initialiser_schema()
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                SELECT TOP 1 id
                FROM dbo.Sessions
                ORDER BY date_creation DESC, id DESC
                """
            )
            ligne = curseur.fetchone()
            return int(ligne[0]) if ligne else None

    def recuperer_parametres_session(
        self,
        session_id: int,
    ) -> ParametresTranches | None:
        """Charge les paramètres d'une session existante."""
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                SELECT
                    matin_debut,
                    matin_fin,
                    soiree_debut,
                    soiree_fin,
                    nuit_debut,
                    nuit_fin,
                    coefficient_soiree,
                    marge_batterie,
                    rendement_panneau_haut,
                    rendement_panneau_bas,
                    prix_vente_jour_ouvrable_ar_wh,
                    prix_vente_weekend_ar_wh
                FROM dbo.Sessions
                WHERE id = ?
                """,
                session_id,
            )
            ligne = curseur.fetchone()
            if ligne is None:
                return None

            return ParametresTranches(
                matin_debut=ligne[0],
                matin_fin=ligne[1],
                soiree_debut=ligne[2],
                soiree_fin=ligne[3],
                nuit_debut=ligne[4],
                nuit_fin=ligne[5],
                coefficient_soiree=ligne[6],
                marge_batterie=ligne[7],
                rendement_panneau_haut=ligne[8],
                rendement_panneau_bas=ligne[9],
                prix_vente_jour_ouvrable_ar_wh=ligne[10],
                prix_vente_weekend_ar_wh=ligne[11],
            )

    def recuperer_appareils(self, session_id: int) -> list[Appareil]:
        """Récupère tous les appareils d'une session."""
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                SELECT nom, puissance_watts, tranche, heure_debut, heure_fin
                FROM dbo.Appareils
                WHERE session_id = ?
                ORDER BY id
                """,
                session_id,
            )
            appareils: list[Appareil] = []
            for ligne in curseur.fetchall():
                appareils.append(
                    Appareil(
                        nom=ligne[0],
                        puissance_watts=ligne[1],
                        tranche=ligne[2],
                        heure_debut=ligne[3],
                        heure_fin=ligne[4],
                    )
                )
            return appareils

    def mettre_a_jour_parametres_session(
        self,
        session_id: int,
        parametres: ParametresTranches,
    ) -> None:
        """Met à jour les paramètres d'une session existante."""
        self.initialiser_schema()
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                UPDATE dbo.Sessions
                SET
                    matin_debut = ?,
                    matin_fin = ?,
                    soiree_debut = ?,
                    soiree_fin = ?,
                    nuit_debut = ?,
                    nuit_fin = ?,
                    coefficient_soiree = ?,
                    marge_batterie = ?,
                    rendement_panneau_haut = ?,
                    rendement_panneau_bas = ?,
                    prix_vente_jour_ouvrable_ar_wh = ?,
                    prix_vente_weekend_ar_wh = ?
                WHERE id = ?
                """,
                parametres.matin_debut,
                parametres.matin_fin,
                parametres.soiree_debut,
                parametres.soiree_fin,
                parametres.nuit_debut,
                parametres.nuit_fin,
                parametres.coefficient_soiree,
                parametres.marge_batterie,
                parametres.rendement_panneau_haut,
                parametres.rendement_panneau_bas,
                parametres.prix_vente_jour_ouvrable_ar_wh,
                parametres.prix_vente_weekend_ar_wh,
                session_id,
            )
            connexion.commit()
            return session_id

    def enregistrer_resultat(self, session_id: int, resultat: ResultatCalcul) -> None:
        """Insère uniquement le résultat pour une session dont les appareils sont déjà en base."""
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                INSERT INTO dbo.Resultats (
                    session_id,
                    energie_matin_wh,
                    energie_soiree_wh,
                    energie_nuit_wh,
                    batterie_theorique_wh,
                    batterie_pratique_wh,
                    puissance_panneau_theorique_w,
                    puissance_panneau_rendement_haut_w,
                    puissance_panneau_rendement_bas_w,
                    puissance_convertisseur_w
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                session_id,
                resultat.energie_matin_wh,
                resultat.energie_soiree_wh,
                resultat.energie_nuit_wh,
                resultat.batterie_theorique_wh,
                resultat.batterie_pratique_wh,
                resultat.puissance_panneau_theorique_w,
                resultat.puissance_panneau_rendement_haut_w,
                resultat.puissance_panneau_rendement_bas_w,
                resultat.puissance_convertisseur_w,
            )
            connexion.commit()

    def enregistrer_panneau(self, panneau: PanneauSolaire, session_id: int) -> None:
        """Insère un panneau solaire dans une session existante."""
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                INSERT INTO dbo.PanneauxSolaires (
                    session_id,
                    nom,
                    pourcentage,
                    energie_unitaire_wh,
                    prix_unitaire
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                session_id,
                panneau.nom,
                panneau.pourcentage,
                panneau.energie_unitaire_wh,
                panneau.prix_unitaire,
            )
            connexion.commit()

    def synchroniser_panneaux(
        self,
        session_id: int,
        panneaux: list[PanneauSolaire],
    ) -> None:
        """Remplace les panneaux solaires d'une session par l'état courant en mémoire."""
        self.initialiser_schema()
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                "DELETE FROM dbo.PanneauxSolaires WHERE session_id = ?",
                session_id,
            )
            for panneau in panneaux:
                curseur.execute(
                    """
                    INSERT INTO dbo.PanneauxSolaires (
                        session_id,
                        nom,
                        pourcentage,
                        energie_unitaire_wh,
                        prix_unitaire
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    session_id,
                    panneau.nom,
                    panneau.pourcentage,
                    panneau.energie_unitaire_wh,
                    panneau.prix_unitaire,
                )
            connexion.commit()

    def recuperer_panneaux(self, session_id: int) -> list[PanneauSolaire]:
        """Récupère tous les panneaux solaires d'une session."""
        with obtenir_connexion() as connexion:
            curseur = connexion.cursor()
            curseur.execute(
                """
                SELECT nom, pourcentage, energie_unitaire_wh, prix_unitaire
                FROM dbo.PanneauxSolaires
                WHERE session_id = ?
                ORDER BY id
                """,
                session_id,
            )
            panneaux = []
            for ligne in curseur.fetchall():
                panneaux.append(PanneauSolaire(
                    nom=ligne[0],
                    pourcentage=ligne[1],
                    energie_unitaire_wh=ligne[2],
                    prix_unitaire=ligne[3],
                ))
            return panneaux
