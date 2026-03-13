# RBAC terrain simplifie (pret validation metier)

Date: 2026-02-26
Source: `services/api/app/auth/roles_config.py` + routage actuel Web/Mobile
Principe: reutiliser les roles existants, sans creation de role technique avant arbitrage metier.

## Tableau de validation metier (terrain)

| Profil UI cible | Role technique actuel | Permissions actuelles | Ecrans autorises (cible) | Ecrans a masquer | Regles de blocage metier |
|---|---|---|---|---|---|
| Orpailleur | `orpailleur` | `[]` | Tableau de bord terrain, mes lots OR, ventes locales OR, ma carte Karabola (lecture) | Export, administration, COM/GUE, compliance, dashboards nationaux | Carte Karabola obligatoire et valide pour operations OR; pas d'export direct |
| Collecteur local | `collecteur` | `card_collector_manage` | Dashboard terrain, achats OR locaux, consolidation lots, ventes vers comptoir/bijoutier, gestion carte collecteur | Ecrans institutionnels, export avance, modules audit/parametrage | Pas d'achat si carte collecteur invalide/expiree; pas de vente hors chaine legale |
| Petit exploitant OR | `orpailleur` | `[]` | Meme parcours qu'Orpailleur, libelle UI "Petit exploitant (OR)" | Idem Orpailleur | Idem Orpailleur |
| Petit exploitant PIERRE | `pierre_exploitant` | `pierre_declare_lot`, `pierre_trade` | Declaration lot pierre, transactions locales pierre, suivi de ses lots | Ecrans OR/BOIS non pertinents, export institutionnel | Pas d'export direct; controles filiere pierre uniquement |
| Petit exploitant BOIS | `bois_exploitant` | `bois_declare_lot`, `bois_trade` | Declaration lot bois, transactions locales bois, suivi conformite de base | Ecrans OR/PIERRE non pertinents, export institutionnel | Pas d'export direct; blocage si statut legal du lot interdit |

## Liste minimale des roles a masquer pour ces profils

`admin`, `dirigeant`, `com`, `com_admin`, `com_agent`, `gue`, `gue_or_agent`, `analyse_certification`, `comptoir_operator`, `comptoir_compliance`, `comptoir_director`, `douanes_agent`, `mines_region_agent`, `lab_bgglm`, `tresor`, `mef`, `bcmm`, `bianco`, `police`, `gendarmerie`.

## Decision metier attendue (go/no-go)

1. Valider que le libelle UI unique "Petit exploitant" est bien mappe dynamiquement a `orpailleur` / `pierre_exploitant` / `bois_exploitant` selon filiere choisie a l'inscription.
2. Valider que `orpailleur` reste sans permissions explicites catalogue (controle par workflow) ou decider un set minimal explicite.
3. Valider la liste definitive des roles masques en parcours terrain Web/Mobile.
4. Valider les blocages carte (Karabola / collecteur) comme prerequis de transaction.
