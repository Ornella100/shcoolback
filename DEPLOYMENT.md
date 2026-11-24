# SchoolConnect : démarrer les services de production

Les campagnes immédiates utilisent Celery. Les campagnes programmées ont aussi
besoin de Celery Beat : le backend seul et le worker ne déclenchent pas l'horloge.

Depuis `backend/SchoolConnect`, en production, avec les variables d'environnement
et PostgreSQL/Redis déjà configurés :

```sh
python manage.py migrate
python manage.py collectstatic --no-input
gunicorn SchoolConnect.wsgi:application
```

Démarrer en parallèle deux processus persistants :

```sh
celery -A SchoolConnect worker --loglevel=INFO
celery -A SchoolConnect beat --loglevel=INFO
```

Le processus Beat examine les messages programmés toutes les 30 secondes et les
met dans Redis pour le worker. Redis doit être accessible aux trois processus.
Sur une plateforme avec plusieurs instances Beat, garder une seule instance pour
éviter des dispatchs répétés. Le worker protège le traitement d'un message par son
statut en base.

## Notifications push

Les notifications navigateur nécessitent HTTPS et une paire de clés VAPID, ainsi
qu'un email de contact. Ajouter `WEB_PUSH_VAPID_PUBLIC_KEY`,
`WEB_PUSH_VAPID_PRIVATE_KEY` et `WEB_PUSH_VAPID_CLAIMS_EMAIL` aux variables
d'environnement du backend. Installer les dépendances de `requirements.txt`, puis
exécuter `python manage.py migrate`. Les utilisateurs peuvent activer les alertes
depuis **Mon profil** ; les campagnes terminées envoient alors une notification
sur leurs appareils enregistrés. Garder la clé privée uniquement côté backend.
