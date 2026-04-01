# 🔒 DocShield

**Protection de documents par code-barres Code 128 signé HMAC-SHA256.**

DocShield est une application web Flask qui estampille vos documents (PDF, DOCX, images) avec un code-barres d'authenticité signé cryptographiquement. Chaque document reçoit un identifiant unique et une signature HMAC-SHA256 permettant de vérifier son authenticité.

---

## ✨ Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| **Formats supportés** | PDF, DOCX, PNG, JPG, JPEG, WEBP |
| **Algorithme de signature** | HMAC-SHA256 avec clé secrète serveur |
| **Type de code-barres** | Code 128 (128 caractères ASCII, haute densité) |
| **Estampillage PDF** | Via ReportLab (overlay) + PyPDF (fusion) |
| **Estampillage DOCX** | Via python-docx (image inline) |
| **Estampillage Images** | Via Pillow (composite) |
| **Interface** | Drag & drop, responsive |
| **Déploiement** | Render, Heroku, VPS, local |

---

## 🚀 Démarrage rapide (local)

### 1. Cloner le dépôt
```bash
git clone https://github.com/VOTRE-USERNAME/docshield.git
cd docshield
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement
```bash
cp .env.example .env
# Éditer .env et changer DOCSHIELD_SECRET par une valeur forte
```

### 4. Lancer l'application
```bash
python app.py
```

Ouvrir → [http://localhost:5000](http://localhost:5000)

---

## 📡 Déploiement sur Render

### Option A – Déploiement automatique (recommandé)

1. **Pusher** ce dépôt sur GitHub
2. Aller sur [render.com](https://render.com) → **New Web Service**
3. Connecter votre dépôt GitHub
4. Render détecte automatiquement `render.yaml`
5. Cliquer **Deploy** — Render génère automatiquement `DOCSHIELD_SECRET`

### Option B – Manuel

Dans les paramètres du service Render :

| Paramètre | Valeur |
|---|---|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| **Environment** | `DOCSHIELD_SECRET` = une valeur forte aléatoire |

---

## 🔌 API REST

### `POST /api/protect`
Protège un document avec un code-barres signé.

**Request** (multipart/form-data) :
- `file` — Le fichier à protéger
- `position` — `"bottom"` (défaut) ou `"top"`

**Response** (JSON) :
```json
{
  "success": true,
  "doc_id": "A3F8B2C1D4E5F6A7",
  "timestamp": "20250115T143022Z",
  "signature": "9A3F2B8C1D4E5F6A",
  "barcode": "DS-A3F8B2C1D4E5F6A7-9A3F2B8C1D4E5F6A",
  "filename": "rapport_docshield_A3F8B2C1.pdf",
  "mime": "application/pdf",
  "size": 124588,
  "data": "<base64 du fichier>"
}
```

### `POST /api/verify`
Vérifie un code-barres DocShield.

**Request** (JSON) :
```json
{ "barcode": "DS-A3F8B2C1D4E5F6A7-9A3F2B8C1D4E5F6A" }
```

**Response** :
```json
{ "valid": true, "doc_id": "A3F8B2C1D4E5F6A7", "signature": "9A3F2B8C1D4E5F6A" }
```

### `POST /api/preview-barcode`
Génère un aperçu PNG du code-barres (sans traiter de document).

### `GET /health`
Vérification de l'état du service.

---

## 🔐 Sécurité

- La clé `DOCSHIELD_SECRET` ne doit jamais être committée dans Git
- En production, utiliser une valeur d'au moins 32 caractères aléatoires
- Sur Render, utiliser `generateValue: true` dans `render.yaml` pour une clé auto-générée
- La vérification complète (full-verify) nécessite un stockage des métadonnées en base de données

---

## 🏗️ Structure du projet

```
docshield/
├── app.py                   # Application Flask principale
├── utils/
│   ├── barcode_gen.py       # HMAC-SHA256 + génération Code 128
│   ├── pdf_processor.py     # Estampillage PDF (reportlab + pypdf)
│   ├── docx_processor.py    # Estampillage DOCX (python-docx)
│   └── image_processor.py   # Estampillage images (Pillow)
├── templates/
│   └── index.html           # Interface drag & drop
├── requirements.txt
├── Procfile                 # Pour Render/Heroku
├── render.yaml              # Déploiement Render
├── .env.example
├── .gitignore
└── README.md
```

---

## 📦 Dépendances principales

| Package | Rôle |
|---|---|
| Flask | Framework web |
| python-barcode | Génération Code 128 |
| Pillow | Traitement images |
| pypdf | Lecture/fusion PDF |
| reportlab | Création overlay PDF |
| python-docx | Manipulation DOCX |
| gunicorn | Serveur WSGI production |

---

## 📝 Licence

MIT — Libre d'utilisation, modification et distribution.
