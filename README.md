# **Video Transcoding**

Ce projet met en œuvre une **Lambda Function en Python** intégrée dans une **image Docker** pour permettre la livraison par les éditeurs des **"Spot Adressés"** (ci-après nommés "Creatives"). Ce système s'inscrit dans le cadre du lancement du service de **TV Segmentée (Adressable)** proposé par **Bouygues Telecom**.

## **Objectifs du projet**
L’objectif principal est de fournir une solution automatisée et fiable pour le transcodage des vidéos publicitaires (Creatives) destinées au service de TV Segmentée. Le processus inclut :
- Le **transcodage vidéo** selon des formats compatibles avec le service.
- Le **provisionnement des contenus** via AWS Lambda et S3.
- Une intégration complète avec les workflows des éditeurs.

Ce projet repose sur une **infrastructure basée sur AWS** et une **architecture conteneurisée** pour assurer modularité, évolutivité et fiabilité.

---

## **Caractéristiques principales**
- **Python Lambda Function** : Gestion du traitement via une fonction AWS Lambda.
- **Docker** : Image Docker pour encapsuler l’environnement Python et les dépendances.
- **AWS Services** : Intégration avec AWS Lambda, S3, ECR et DynamoDB.
- **Provisioning** : Création et gestion d’une base de données externe pour suivre les contenus provisionnés.

---

## **Pré-requis**
### Installation ou mise à jour de l’AWS CLI
Consultez la documentation officielle pour installer l’AWS CLI :  
👉 [Guide AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

Pour un environnement Windows, utilisez la commande suivante dans un terminal CMD :
```bash
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

---

## **Étapes de déploiement**

### 1. **Construction et exécution de l’image Docker**
```bash
docker build -t video-transcoding .
docker run -d -p 9000:8080 --name mh video-transcoding
```

### 2. **Authentification auprès d’AWS ECR**
Récupérez un token d'authentification et connectez votre client Docker au registre AWS ECR :
```bash
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 893201506378.dkr.ecr.eu-west-1.amazonaws.com
```
**Remarque :** Assurez-vous d'avoir la dernière version de l’AWS CLI et de Docker.

### 3. **Création et balisage de l’image Docker**
Construisez et balisez votre image Docker pour qu’elle puisse être transférée dans le registre AWS :
```bash
docker build -t video-transcoding .
docker tag video-transcoding:latest 893201506378.dkr.ecr.eu-west-1.amazonaws.com/video-transcoding:latest
```

### 4. **Pousser l’image Docker vers AWS ECR**
Transférez votre image vers le registre AWS :
```bash
docker push 893201506378.dkr.ecr.eu-west-1.amazonaws.com/video-transcoding:latest
```

### 5. **Mettre à jour la Lambda Function**
Mettez à jour la configuration et le code de votre fonction Lambda avec l’image Docker déployée :
```bash
aws lambda update-function-configuration --function-name video_transcoding --package-type Image
aws lambda update-function-code --function-name video_transcoding --image-uri 893201506378.dkr.ecr.eu-west-1.amazonaws.com/video-transcoding:latest
aws lambda update-function-configuration --function-name video_transcoding --image-config '{"EntryPoint": ["python", "app.py"], "Command": [], "WorkingDirectory": "/var/task"}'
```

---

## **Création et gestion de la base de données**
Voici un exemple de requêtes SQL pour créer et gérer une table externe utilisée pour le provisioning :
```sql
CREATE DATABASE provisioning;

CREATE EXTERNAL TABLE provisioning.btvs_ids(
    content_id string,
    pub_id string,
    add_at timestamp
)
PARTITIONED BY (id int)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
LOCATION 's3://rmcbfmads-creatives/provisioning/btvs_ids'
TBLPROPERTIES ('parquet.enable.dictionary'='true');

INSERT INTO provisioning.btvs_ids (id, content_id, pub_id, add_at)
VALUES (10, null, null, current_timestamp);

SELECT * FROM provisioning.btvs_ids;
```

---

## **Dépendances**
Voici les principales dépendances et outils nécessaires pour le projet :
- **Python 3.9** : Pour exécuter le code.
- **AWS CLI** : Pour interagir avec les services AWS.
- **Docker** : Pour construire et exécuter l’image.
- **Parquet SerDe** : Pour le stockage des métadonnées dans S3.
- **Boto3** : SDK Python pour AWS.

---

## **Liens utiles**
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS ECR Documentation](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
- [Docker Documentation](https://docs.docker.com/get-started/)

