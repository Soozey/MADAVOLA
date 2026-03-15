# MADAVOLA - Correctifs conformité OR (15/03/2026)

## Références prises en compte
- `250423_ 2 Procédure obtention Carte Collecteur Or.docx` (droit carte collecteur = 500 000 Ar)
- `270423-1' Procédure obtention agrément comptoir Schéma.docx` (instruction + agrément, délai, logique COM/ANOR)
- `D2024-1691-VF- Statu de la centrale de l'or de madagascar COM.pdf` (rôle COM sur instruction agréments/cartes)
- `Code-Minier-VM-2023.pdf` (contexte Code minier)
- Cahier des charges MADAVOLA transmis dans le brief (chaîne OR, blocages, auditabilité)

## Correctifs appliqués dans ce patch
1. Verrouillage chaîne OR dans `/trades`
- Ajout d’un contrôle de chaîne légale OR sur la création et la confirmation de transaction:
  - orpailleur -> collecteur uniquement
  - collecteur -> comptoir (agréé actif) ou bijoutier
- Blocage explicite si agrément comptoir absent/invalide ou accès SIG-OC suspendu.

2. Cartes collecteur: conformité documentaire renforcée
- Une carte collecteur ne peut plus être validée tant que les pièces obligatoires ne sont pas **vérifiées**.
- Le simple état `uploaded` n’est plus suffisant pour l’approbation.

3. Cartes collecteur: éligibilité minimale renforcée
- Création de carte bloquée si acteur inexistant/inactif.
- Création de carte bloquée si l’acteur n’a ni rôle `collecteur` ni rôle `bijoutier`.

4. Affiliation collecteur: cohérence juridique
- Soumission d’affiliation autorisée seulement pour une carte collecteur validée/active.
- Contrôle type d’affiliation vs rôle réel de l’acteur cible:
  - `comptoir` -> rôle comptoir requis
  - `bijouterie` -> rôle bijoutier requis

5. Paramétrage tarifaire par défaut
- Tarif par défaut de la carte collecteur ajusté à `500 000 Ar` (au lieu de `10 000 Ar`).

6. Agrément comptoir: garde-fous supplémentaires
- Création d’agrément bloquée si acteur inexistant/inactif.
- Création d’agrément bloquée si acteur non personne morale.
- Création d’agrément bloquée si acteur sans rôle comptoir.
- Validité fixée à 2 ans (`730 jours`) sur l’agrément créé.

## Points encore à traiter (prochaine itération)
- Workflow complet d’agrément comptoir en deux paiements (3M instruction + 17M octroi) avec statuts dédiés.
- Paramétrage documentaire détaillé par base légale (checklists versionnées COM/Code minier).
- Contrôles de nationalité/résidence au niveau modèle acteur (actuellement partiels via cartes).
- Alignement avancé export OR (GUE, contrôle douane, rapatriement devises) sur tous les endpoints métiers.
