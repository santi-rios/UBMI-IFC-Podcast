# 🔒 Guía de Seguridad - API Keys y Configuración

## ⚠️ IMPORTANTE: Protección de API Keys

Este proyecto requiere varias API keys para funcionar correctamente. **NUNCA** subas tus keys reales a un repositorio público.

## 🚀 Configuración Rápida

### Paso 1: Copiar archivos de configuración
```bash
cp config/config.template.yaml config/config.yaml
cp .env.template .env
```

### Paso 2: Obtener API Keys

#### OpenAI (Para generación de guiones)
1. Ve a https://platform.openai.com/api-keys
2. Crea una nueva API key
3. Cópiala en `config/config.yaml` o `.env`

#### Anthropic Claude (Alternativa a OpenAI)
1. Ve a https://console.anthropic.com/
2. Crea una cuenta y genera API key
3. Cópiala en `config/config.yaml` o `.env`

#### ElevenLabs (Para síntesis de voz)
1. Ve a https://elevenlabs.io/
2. Registrate y ve a Profile → API Keys
3. Cópiala en `config/config.yaml` o `.env`

#### PubMed (Opcional, para búsquedas más rápidas)
1. Ve a https://www.ncbi.nlm.nih.gov/account/
2. Crea cuenta y solicita API key
3. Cópiala en `config/config.yaml` o `.env`

### Paso 3: Editar archivos de configuración

En `config/config.yaml`:
```yaml
api_keys:
  openai: "sk-..."
  anthropic: "sk-ant-..."
  elevenlabs: "..."

pubmed:
  email: "tu_email@ejemplo.com"
  api_key: "tu_pubmed_key"
```

En `.env`:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
PUBMED_API_KEY=...
PUBMED_EMAIL=tu_email@ejemplo.com
```

## 🔐 Verificación de Seguridad

Antes de hacer `git push`, verifica:

```bash
# Verificar que los archivos sensibles NO están en git
git status
# Deberías ver que config/config.yaml y .env NO aparecen

# Verificar .gitignore
cat .gitignore | grep -E "(config\.yaml|\.env)"
```

## 🚨 ¿Qué hacer si accidentalmente subes una API key?

1. **Inmediatamente** cambia/revoca la API key en el proveedor
2. Borra el archivo del historial de git:
```bash
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch config/config.yaml' --prune-empty --tag-name-filter cat -- --all
git push origin --force --all
```

## 📁 Archivos Seguros para Repositorio Público

✅ **SEGUROS**:
- `config.template.yaml`
- `.env.template`
- Todo el código fuente
- Notebooks (sin API keys)
- README.md

❌ **NUNCA SUBIR**:
- `config/config.yaml` (con keys reales)
- `.env` (con keys reales)  
- Cualquier archivo con `*secret*` o `*key*` en el nombre

## 🤝 Para Colaboradores

Si alguien más va a trabajar en el proyecto:
1. Clona el repositorio
2. Sigue los pasos de "Configuración Rápida"
3. Obtén sus propias API keys
4. **NUNCA** compartas API keys por email/chat/etc.