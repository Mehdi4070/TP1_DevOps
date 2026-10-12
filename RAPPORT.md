# Compte rendu — TP Conteneurisation et orchestration micro-services

**Étudiant :** NOM Prénom  
**Classe :** …  
**Date :** …

## 1. Objectif et architecture

Visit-Counter est composé d'une application Flask, d'une base Redis persistante
et, pour le déploiement à plusieurs réplicas, d'un reverse proxy Nginx.

```text
Navigateur ── port 80 ──> Nginx
                              ├──> web-1:5000 ──┐
                              ├──> web-2:5000 ──┼──> db-service:6379
                              └──> web-3:5000 ──┘         │
                                                   volume redis-data
```

## 2. Dockerfile commenté et choix de l'image

```dockerfile
# Alpine est retenue car elle fournit un environnement Python de petite taille.
FROM python:3.13-alpine

# Pas de bytecode et affichage immédiat des logs dans `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Création d'un utilisateur non-root pour réduire les privilèges du processus.
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Cette couche ne sera reconstruite que si requirements.txt change.
COPY requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=appuser:appgroup app.py ./
USER appuser
EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--access-logfile", "-", "app:app"]
```

Alpine a été choisie plutôt que l'image Python complète afin de limiter la taille
à télécharger et la surface d'attaque. Les dépendances du projet sont en Python
pur, donc les particularités de compilation liées à Alpine ne pénalisent pas ce
projet. `--no-cache-dir` évite de conserver le cache `pip` dans l'image finale.

### Capture 1 — taille de l'image

Commande : `docker images counter-app:1.0`

> Insérer ici `screenshots/01-docker-images.png` et commenter la taille obtenue.

## 3. Réseau et persistance

Le réseau bridge `app-network` fournit la résolution DNS interne : le nom
`db-service` est directement utilisable par Flask. Le volume nommé `redis-data`
est monté sur `/data`. Redis utilise l'Append Only File, ce qui conserve le
compteur même lorsque son conteneur est supprimé puis recréé.

### Capture 2 — inspection du réseau

Commande : `docker network inspect app-network`

> Insérer ici `screenshots/02-network-inspect.png`. La section `Containers` doit
> montrer Redis et l'application connectés.

### Capture 3 — application dans le navigateur

> Insérer ici `screenshots/03-application.png`. La barre d'adresse, le compteur et
> l'identifiant du conteneur doivent être visibles.

### Test de robustesse

Valeur avant suppression : **…**  
Valeur après recréation de Redis : **…**  
Conclusion : **…**

## 4. Fichier Docker Compose final

Le fichier final est `docker-compose.yml`. Il définit `db-service`, `web` et
`load-balancer`, ainsi que le réseau et le volume nommés. Le port publié est lu
depuis `.env` et n'est donc pas écrit en dur dans le YAML.

> Coller ici la version finale de `docker-compose.yml`, ou l'ajouter en annexe.

Commande de lancement :

```bash
docker compose up -d --build --scale web=3
```

## 5. Analyse du scaling et load balancing

Les trois conteneurs web peuvent tous écouter sur le port 5000 **dans leurs
propres espaces réseau**. En revanche, ils ne peuvent pas tous publier ce port sur
le même port 80 de l'hôte, car une seule liaison peut réserver une combinaison
adresse/port hôte donnée.

La solution retenue est Nginx. Lui seul publie le port 80. Sur le réseau interne,
le nom DNS Compose `web` représente les réplicas et Nginx distribue les requêtes.
L'identifiant affiché permet d'observer cette distribution.

## 6. Différence entre RUN et CMD

`RUN` exécute une commande **pendant la construction** de l'image et crée une
couche, par exemple l'installation des dépendances. Le résultat fait partie de
l'image.

`CMD` définit la commande **par défaut au démarrage** d'un conteneur. Elle ne
s'exécute pas pendant le build et peut être remplacée par une commande fournie à
`docker run`. Un Dockerfile peut contenir plusieurs `RUN`, mais seul le dernier
`CMD` est effectif.

## 7. Pipeline Jenkins

À chaque push sur `main`, le webhook déclenche Jenkins. La pipeline :

1. récupère le dépôt ;
2. installe les dépendances et lance `pytest` ;
3. construit l'image Docker ;
4. s'authentifie avec une credential Jenkins puis publie les tags du build et
   `latest` sur Docker Hub.

> Ajouter ici une capture d'une pipeline Jenkins réussie.

## 8. Publication Docker Hub

Lien public : `https://hub.docker.com/r/VOTRE_COMPTE/counter-app`

> Remplacer `VOTRE_COMPTE` et ajouter une capture du dépôt/tag publié.

## 9. Conclusion

> Résumer les résultats, les difficultés rencontrées et les solutions appliquées.
