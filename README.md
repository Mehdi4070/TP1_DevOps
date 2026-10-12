# TP DevOps — Visit-Counter

Application Flask conteneurisée qui incrémente dans Redis un compteur persistant.
Le projet comprend une exécution Docker manuelle, une orchestration Compose avec
trois réplicas et Nginx, des tests unitaires et une pipeline Jenkins.

## Prérequis et Partie 0

```bash
docker version
docker compose version
docker login
```

Le démon Docker doit être démarré. Sous Linux, si l'utilisateur n'a pas accès au
socket Docker, l'ajouter au groupe `docker`, puis rouvrir sa session :

```bash
sudo usermod -aG docker "$USER"
```

## Tests unitaires

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
pytest -q
```

Les tests utilisent un client Redis simulé : aucun serveur Redis n'est nécessaire.

## Partie 1 — construire l'image

```bash
docker build -t counter-app:1.0 .
docker images counter-app:1.0
```

L'image `python:3.13-alpine` est compacte. Le fichier des dépendances est copié
avant le code afin de réutiliser le cache Docker. L'application s'exécute avec
`appuser`, et non avec `root`.

## Partie 2 — réseau et volume, sans Compose

Créer les ressources et démarrer Redis :

```bash
docker network create app-network
docker volume create redis-data
docker run -d \
  --name db-service \
  --network app-network \
  --mount source=redis-data,target=/data \
  redis:7.4-alpine \
  redis-server --appendonly yes --appendfsync always
```

Démarrer l'application :

```bash
docker run -d \
  --name counter-web \
  --network app-network \
  -e REDIS_HOST=db-service \
  -p 80:5000 \
  counter-app:1.0
```

Tester avec le navigateur sur `http://localhost` ou avec :

```bash
curl http://localhost
docker network inspect app-network
```

Test de persistance : noter la valeur, supprimer uniquement Redis, le recréer avec
le même volume, puis actualiser la page.

```bash
docker rm -f db-service
docker run -d \
  --name db-service \
  --network app-network \
  --mount source=redis-data,target=/data \
  redis:7.4-alpine \
  redis-server --appendonly yes --appendfsync always
```

La valeur est conservée dans `redis-data`. Le mode AOF avec synchronisation
immédiate évite de perdre la dernière incrémentation lors du `docker rm -f`.

Avant de passer à Compose, supprimer les conteneurs et ressources manuels pour
éviter les conflits de noms :

```bash
docker rm -f counter-web db-service
docker network rm app-network
docker volume rm redis-data
```

## Partie 3 — Docker Compose et scaling

Le port hôte est défini dans `.env`. Pour utiliser le port 8080, remplacer
`APP_PORT=80` par `APP_PORT=8080`.

```bash
docker compose config
docker compose up -d --build --scale web=3
docker compose ps
```

Ouvrir `http://localhost`, puis actualiser. L'identifiant du conteneur doit changer
car Nginx répartit les requêtes entre les trois instances.

Une publication telle que `ports: ["80:5000"]` sur `web` échoue au deuxième
réplica : un port hôte donné ne peut être réservé que par un seul conteneur. Ici,
les réplicas exposent uniquement le port 5000 sur `app-network`; Nginx est l'unique
service qui publie le port 80 et joue le rôle de load balancer.

Commandes de diagnostic :

```bash
docker compose logs -f
docker compose exec web sh
docker inspect visit-counter-db-service-1
docker network inspect app-network
```

## Partie 4 — Docker Hub et nettoyage

Remplacer `VOTRE_COMPTE` par le nom du compte Docker Hub :

```bash
docker tag counter-app:1.0 VOTRE_COMPTE/counter-app:1.0
docker push VOTRE_COMPTE/counter-app:1.0
```

Nettoyage ciblé de ce projet, y compris son volume et ses images locales :

```bash
docker compose down --volumes --rmi local --remove-orphans
```

La commande globale suivante supprime en plus **toutes** les ressources Docker
inutilisées de la machine, pas seulement celles du TP :

```bash
docker system prune -a --volumes
```

## Partie C — Jenkins

Le `Jenkinsfile` réalise les tests, construit l'image sur `main`, puis publie deux
tags : le numéro du build et `latest`.

Configuration Jenkins nécessaire :

1. Créer un *Multibranch Pipeline* relié au dépôt Git et conserver la branche
   `main`.
2. Installer/configurer les plugins Pipeline, GitHub et JUnit.
3. Créer une credential de type *Username with password*, identifiant
   `dockerhub-credentials`. Utiliser le nom Docker Hub comme username et un
   **access token Docker Hub** comme password.
4. Donner à l'agent Jenkins l'accès à Python 3 et au démon Docker.
5. Ajouter dans GitHub un webhook vers
   `https://ADRESSE_JENKINS/github-webhook/` avec l'événement *push*.
6. Faire un commit sur `main`, puis vérifier les quatre stages dans Jenkins.

Ne jamais placer le mot de passe ou le token Docker Hub dans le dépôt ou dans
`.env`.

## Compte rendu

Compléter [RAPPORT.md](RAPPORT.md), ajouter les captures dans `screenshots/`, puis
exporter le document en PDF. Les emplacements exacts des preuves attendues y sont
indiqués.
