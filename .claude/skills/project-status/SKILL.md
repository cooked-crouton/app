---
name: project-status
description: Analyse l'état d'un projet de développement (code, git, tests, dépendances, dette technique, avancement) et produit un rapport synthétique. À utiliser quand on demande "état du projet", "où en est-on", "audit rapide", "bilan" ou "project status".
---

# Analyse de l'état d'un projet

Objectif : donner une vision claire et honnête de l'état du projet, avec des actions concrètes. Lecture seule : ne modifie aucun fichier du projet (sauf le rapport final si demandé).

## Étape 1 — Cartographier le projet

- Lire `README`, `CONTRIBUTING`, `docs/`, `CHANGELOG` s'ils existent.
- Identifier le langage, le framework, le gestionnaire de paquets et le système de build (`package.json`, `pom.xml`, `pyproject.toml`, `*.csproj`, `Cargo.toml`, `ProjectSettings/` pour Unity, etc.).
- Lister la structure des dossiers (2 niveaux) et repérer les points d'entrée.

## Étape 2 — Historique et activité Git

Commandes utiles :

```bash
git status --short
git branch -a --sort=-committerdate | head -15
git log --oneline -20
git log --since="30 days ago" --format='%an' | sort | uniq -c | sort -rn
git diff --stat HEAD~10 2>/dev/null | tail -5
```

Relever : branche courante, changements non commités, branches obsolètes, rythme des commits, contributeurs actifs, derniers gros changements.

## Étape 3 — Santé technique

- **Build** : lancer la commande de build du projet et noter erreurs/warnings.
- **Tests** : lancer la suite de tests, noter réussis/échoués/ignorés. Estimer la couverture si un outil est configuré.
- **Lint / formatage** : lancer le linter s'il existe.
- **Dépendances** : repérer les paquets obsolètes et les vulnérabilités connues (`npm outdated` / `npm audit`, `pip list --outdated`, `mvn versions:display-dependency-updates`, etc.).
- **Secrets** : chercher des clés/mots de passe en clair (`grep -rniE "(api[_-]?key|secret|password|token)\s*[:=]"`), sans afficher les valeurs dans le rapport.

## Étape 4 — Dette technique et avancement

- Chercher `TODO`, `FIXME`, `HACK`, `XXX` et les compter par dossier.
- Repérer les fichiers très longs, le code dupliqué évident, le code mort, les modules sans tests.
- Si présent : lire le backlog (issues, `TODO.md`, tableau de bord) et comparer avec le code réel pour estimer l'avancement.

## Étape 5 — Rapport

Produire un rapport court dans ce format (pas de remplissage, des faits vérifiés) :

```
# État du projet — <nom> (<date>)

## Résumé (3-5 lignes)
Statut global : 🟢 sain / 🟠 à surveiller / 🔴 critique — et pourquoi.

## Chiffres clés
- Stack : ...
- Build : OK / KO
- Tests : X réussis / Y échoués (couverture : Z %)
- Dépendances obsolètes / vulnérables : N
- TODO/FIXME : N
- Activité (30 j) : N commits, N contributeurs

## Points forts
- ...

## Risques et problèmes (par priorité)
1. [Critique] ...
2. [Important] ...
3. [Mineur] ...

## Actions recommandées
1. Action concrète (effort estimé : S/M/L)
2. ...

## Ce que je n'ai pas pu vérifier
- ...
```

## Règles

- Ne rien inventer : si une commande échoue ou qu'une info manque, l'écrire dans "Ce que je n'ai pas pu vérifier".
- Citer les fichiers et chemins concernés pour chaque problème.
- Rester concis : le rapport doit tenir en une page.
- Proposer de corriger les points trouvés, mais ne rien modifier sans accord.