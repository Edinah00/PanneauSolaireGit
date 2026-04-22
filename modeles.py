from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Appareil:
    nom: str
    puissance_watts: float
    tranche: str
    heure_debut: float
    heure_fin: float


@dataclass(slots=True)
class PanneauSolaire:
    nom: str
    pourcentage: float  # Pourcentage de rendement (ex: 0.4 pour 40%)
    energie_unitaire_wh: float  # Energie unitaire en Wh
    prix_unitaire: float  # Prix unitaire


@dataclass(slots=True)
class ParametresTranches:
    matin_debut: float = 6.0
    matin_fin: float = 17.0
    soiree_debut: float = 17.0
    soiree_fin: float = 19.0
    nuit_debut: float = 19.0
    nuit_fin: float = 6.0
    coefficient_soiree: float = 0.5
    marge_batterie: float = 0.5
    rendement_panneau_haut: float = 0.4
    rendement_panneau_bas: float = 0.3
    prix_vente_jour_ouvrable_ar_wh: float = 0.0
    prix_vente_weekend_ar_wh: float = 0.0


@dataclass(slots=True)
class ResultatCalcul:
    energie_matin_wh: float
    energie_soiree_wh: float
    energie_nuit_wh: float
    batterie_theorique_wh: float
    batterie_pratique_wh: float
    puissance_charge_batterie_w: float
    puissance_appareils_matin_w: float
    puissance_appareils_soiree_w: float
    puissance_panneau_theorique_w: float
    puissance_panneau_rendement_haut_w: float
    puissance_panneau_rendement_bas_w: float
    puissance_convertisseur_w: float
    details: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ResultatVente:
    nom_panneau: str
    puissance_panneau_theorique_w: float
    energie_non_utilisee_wh: float
    prix_vente_jour_ouvrable_ar_wh: float
    prix_vente_weekend_ar_wh: float
    revenu_jour_ouvrable_ar: float
    revenu_weekend_ar: float
    details: dict[str, float] = field(default_factory=dict)
