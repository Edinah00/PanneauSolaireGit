from __future__ import annotations

from typing import Iterable

from modeles import Appareil, ParametresTranches, ResultatCalcul


MINUTES_PAR_HEURE = 60
MINUTES_PAR_JOUR = 24 * MINUTES_PAR_HEURE


def convertir_heure_en_minutes(heure: float) -> int:
    return int(round(heure * MINUTES_PAR_HEURE))


def convertir_minutes_en_heures(minutes: float) -> float:
    return minutes / MINUTES_PAR_HEURE


def normaliser_intervalle(heure_debut: float, heure_fin: float) -> list[tuple[int, int]]:
    debut = convertir_heure_en_minutes(heure_debut) % MINUTES_PAR_JOUR
    fin = convertir_heure_en_minutes(heure_fin) % MINUTES_PAR_JOUR

    if debut == fin:
        return [(0, MINUTES_PAR_JOUR)]

    if debut < fin:
        return [(debut, fin)]

    return [(debut, MINUTES_PAR_JOUR), (0, fin)]


def intervalle_tranche(nom_tranche: str, parametres: ParametresTranches) -> list[tuple[int, int]]:
    if nom_tranche == "matin":
        return normaliser_intervalle(parametres.matin_debut, parametres.matin_fin)
    if nom_tranche == "soiree":
        return normaliser_intervalle(parametres.soiree_debut, parametres.soiree_fin)
    if nom_tranche == "nuit":
        return normaliser_intervalle(parametres.nuit_debut, parametres.nuit_fin)
    raise ValueError(f"Tranche inconnue: {nom_tranche}")


def duree_intervalles_heures(intervalles: Iterable[tuple[int, int]]) -> float:
    total_minutes = sum(fin - debut for debut, fin in intervalles)
    return convertir_minutes_en_heures(total_minutes)


def duree_chevauchement_minutes(
    intervalles_a: Iterable[tuple[int, int]],
    intervalles_b: Iterable[tuple[int, int]],
) -> int:
    total = 0
    for debut_a, fin_a in intervalles_a:
        for debut_b, fin_b in intervalles_b:
            debut = max(debut_a, debut_b)
            fin = min(fin_a, fin_b)
            if debut < fin:
                total += fin - debut
    return total


def duree_dans_tranche_heures(
    appareil: Appareil,
    nom_tranche: str,
    parametres: ParametresTranches,
) -> float:
    intervalles_appareil = normaliser_intervalle(appareil.heure_debut, appareil.heure_fin)
    intervalles_tranche = intervalle_tranche(nom_tranche, parametres)
    minutes = duree_chevauchement_minutes(intervalles_appareil, intervalles_tranche)
    return convertir_minutes_en_heures(minutes)


def puissance_maximale_concurrente(
    appareils: list[Appareil],
    nom_tranche: str,
    parametres: ParametresTranches,
) -> float:
    evenements: list[tuple[int, float]] = []
    intervalles_tranche = intervalle_tranche(nom_tranche, parametres)

    for appareil in appareils:
        intervalles_appareil = normaliser_intervalle(appareil.heure_debut, appareil.heure_fin)
        for debut_appareil, fin_appareil in intervalles_appareil:
            for debut_tranche, fin_tranche in intervalles_tranche:
                debut = max(debut_appareil, debut_tranche)
                fin = min(fin_appareil, fin_tranche)
                if debut < fin:
                    evenements.append((debut, appareil.puissance_watts))
                    evenements.append((fin, -appareil.puissance_watts))

    if not evenements:
        return 0.0

    evenements.sort(key=lambda element: (element[0], -element[1]))
    puissance_courante = 0.0
    puissance_max = 0.0

    for _, variation in evenements:
        puissance_courante += variation
        puissance_max = max(puissance_max, puissance_courante)

    return puissance_max


def calculer_resultats(
    appareils: list[Appareil],
    parametres: ParametresTranches,
) -> ResultatCalcul:
    energie_matin_wh = 0.0
    energie_soiree_wh = 0.0
    energie_nuit_wh = 0.0

    for appareil in appareils:
        energie_matin_wh += appareil.puissance_watts * duree_dans_tranche_heures(
            appareil, "matin", parametres
        )
        energie_soiree_wh += appareil.puissance_watts * duree_dans_tranche_heures(
            appareil, "soiree", parametres
        )
        energie_nuit_wh += appareil.puissance_watts * duree_dans_tranche_heures(
            appareil, "nuit", parametres
        )

    batterie_theorique_wh = energie_nuit_wh
    batterie_pratique_wh = batterie_theorique_wh * (1 + parametres.marge_batterie)

    duree_matin = duree_intervalles_heures(intervalle_tranche("matin", parametres))
    duree_soiree = duree_intervalles_heures(intervalle_tranche("soiree", parametres))
    capacite_charge_equivalente_h = duree_matin + (
        duree_soiree * parametres.coefficient_soiree
    )
    # La batterie doit etre dimensionnee sur l'energie pratique exploitable,
    # pas seulement sur la valeur theorique de base.
    puissance_charge_batterie_w = (
        batterie_pratique_wh / capacite_charge_equivalente_h
        if capacite_charge_equivalente_h > 0
        else 0.0
    )

    puissance_appareils_matin_w = puissance_maximale_concurrente(
        appareils, "matin", parametres
    )
    puissance_appareils_soiree_w = puissance_maximale_concurrente(
        appareils, "soiree", parametres
    )

    puissance_requise_matin = puissance_appareils_matin_w + puissance_charge_batterie_w
    if parametres.coefficient_soiree <= 0:
        raise ValueError("Le coefficient de soiree doit etre strictement positif.")

    puissance_requise_soiree = (
        puissance_appareils_soiree_w / parametres.coefficient_soiree
    ) + puissance_charge_batterie_w
    puissance_panneau_theorique_w = max(
        puissance_requise_matin, puissance_requise_soiree
    )
    if parametres.rendement_panneau_haut <= 0:
        raise ValueError("Le rendement panneau haut doit etre strictement positif.")
    if parametres.rendement_panneau_bas <= 0:
        raise ValueError("Le rendement panneau bas doit etre strictement positif.")

    puissance_panneau_rendement_haut_w = (
        puissance_panneau_theorique_w / parametres.rendement_panneau_haut
    )
    puissance_panneau_rendement_bas_w = (
        puissance_panneau_theorique_w / parametres.rendement_panneau_bas
    )
    puissance_convertisseur_w = (
        2 * max(puissance_appareils_matin_w, puissance_appareils_soiree_w)
    )

    details = {
        "duree_matin_h": duree_matin,
        "duree_soiree_h": duree_soiree,
        "coefficient_soiree": parametres.coefficient_soiree,
        "marge_batterie": parametres.marge_batterie,
        "rendement_panneau_haut": parametres.rendement_panneau_haut,
        "rendement_panneau_bas": parametres.rendement_panneau_bas,
        "energie_recharge_batterie_wh": batterie_pratique_wh,
        "energie_recharge_batterie_theorique_wh": batterie_theorique_wh,
        "puissance_requise_matin_w": puissance_requise_matin,
        "puissance_requise_soiree_w": puissance_requise_soiree,
    }

    return ResultatCalcul(
        energie_matin_wh=energie_matin_wh,
        energie_soiree_wh=energie_soiree_wh,
        energie_nuit_wh=energie_nuit_wh,
        batterie_theorique_wh=batterie_theorique_wh,
        batterie_pratique_wh=batterie_pratique_wh,
        puissance_charge_batterie_w=puissance_charge_batterie_w,
        puissance_appareils_matin_w=puissance_appareils_matin_w,
        puissance_appareils_soiree_w=puissance_appareils_soiree_w,
        puissance_panneau_theorique_w=puissance_panneau_theorique_w,
        puissance_panneau_rendement_haut_w=puissance_panneau_rendement_haut_w,
        puissance_panneau_rendement_bas_w=puissance_panneau_rendement_bas_w,
        puissance_convertisseur_w=puissance_convertisseur_w,
        details=details,
    )


def calculer_energie_non_utilisee_wh(
    appareils: list[Appareil],
    puissance_panneau_w: float,
    parametres: ParametresTranches,
    puissance_charge_batterie_w: float = 0.0,
) -> float:
    """Calcule le surplus solaire vendu pendant les plages de production.

    La production solaire est pleine le matin et pondérée par le coefficient
    du soir pendant la plage de soirée. La batterie pratique est soustraite
    progressivement sur chaque intervalle solaire.
    """
    if puissance_panneau_w <= 0:
        return 0.0

    intervalles_solaire: list[tuple[list[tuple[int, int]], float]] = [
        (intervalle_tranche("matin", parametres), 1.0),
        (intervalle_tranche("soiree", parametres), parametres.coefficient_soiree),
    ]
    if not any(intervalles for intervalles, _ in intervalles_solaire):
        return 0.0

    evenements_appareils: dict[int, float] = {}
    for appareil in appareils:
        for debut, fin in normaliser_intervalle(appareil.heure_debut, appareil.heure_fin):
            evenements_appareils[debut] = evenements_appareils.get(debut, 0.0) + appareil.puissance_watts
            evenements_appareils[fin] = evenements_appareils.get(fin, 0.0) - appareil.puissance_watts

    evenements_solaire: dict[int, float] = {}
    for intervalles, facteur in intervalles_solaire:
        for debut, fin in intervalles:
            evenements_solaire[debut] = evenements_solaire.get(debut, 0.0) + facteur
            evenements_solaire[fin] = evenements_solaire.get(fin, 0.0) - facteur

    current_load = 0.0
    for appareil in appareils:
        for debut, fin in normaliser_intervalle(appareil.heure_debut, appareil.heure_fin):
            if debut <= 0 < fin:
                current_load += appareil.puissance_watts
                break

    current_solar_factor = 0.0
    for intervalles, facteur in intervalles_solaire:
        for debut, fin in intervalles:
            if debut <= 0 < fin:
                current_solar_factor += facteur

    temps = {0, MINUTES_PAR_JOUR}
    temps.update(instant for instant in evenements_appareils.keys() if instant > 0)
    temps.update(instant for instant in evenements_solaire.keys() if instant > 0)
    temps_tries = sorted(temps)

    energie_non_utilisee_wh = 0.0
    precedent = temps_tries[0]
    for instant in temps_tries[1:]:
        if current_solar_factor > 0:
            duree_heures = convertir_minutes_en_heures(instant - precedent)
            puissance_disponible = (
                puissance_panneau_w * current_solar_factor
                - current_load
                - puissance_charge_batterie_w * current_solar_factor
            )
            if puissance_disponible > 0:
                energie_non_utilisee_wh += puissance_disponible * duree_heures

        current_load += evenements_appareils.get(instant, 0.0)
        current_solar_factor += evenements_solaire.get(instant, 0.0)
        precedent = instant

    return energie_non_utilisee_wh
