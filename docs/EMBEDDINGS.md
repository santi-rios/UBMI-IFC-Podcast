# Embeddings: teoría y práctica en este proyecto

Este documento explica qué son los embeddings, por qué los usamos, cómo se construye la base vectorial para recuperar artículos, y qué decisiones prácticas conllevan.

## 1) ¿Qué es un embedding?

- Un embedding es una representación numérica (un vector de dimensión d) de un objeto textual (palabra, frase, párrafo o documento).
- La idea: textos con significado similar quedan cerca en el espacio vectorial; textos distintos quedan lejos.
- “Cerca/lejos” se mide con una métrica, típicamente similitud coseno.

En notación simple, un texto T → vector v ∈ R^d. Si dos textos T1 y T2 hablan de lo mismo, sus vectores v1 y v2 tienen alto coseno(v1, v2).

## 2) ¿Embeddings son palabras clave? ¿frases? ¿párrafos?

- No son listas de palabras clave con pesos manuales como TF‑IDF; son vectores densos aprendidos por un modelo.
- Pueden generarse a diferentes granularidades:
  - Palabra (word embeddings)
  - Frase/oración (sentence embeddings)
  - Párrafo/documento (document embeddings)
- En este proyecto usamos embeddings de “frase/párrafo” tomando título + resumen (abstract) de cada artículo del IFC. Así capturamos el contexto del trabajo, no solo palabras sueltas.

## 3) ¿De dónde salen los números del vector? (la “ponderación”)

- Los valores de cada dimensión los produce un modelo preentrenado (p. ej., Sentence Transformers) que aprendió a mapear textos semánticamente similares a vectores cercanos.
- No asignamos pesos a mano. El “peso semántico” está distribuido en cientos de dimensiones y lo determina el modelo.
- Opcionalmente normalizamos el vector (norma L2 = 1) para que la similitud coseno sea más estable.

## 4) ¿Por qué embeddings en este proyecto?

Queremos:

- Crear una “base de conocimiento” del IFC (2021–2025) que capte temas y contenido.
- Hacer búsquedas semánticas (no solo por palabra exacta) para conectar:
  - Publicaciones del IFC
  - Artículos recientes de PubMed relevantes para los temas del IFC
- Alimentar un LLM con los artículos más afines para generar guiones de podcast.

Embeddings permiten recuperar por significado (p. ej., “estrés metabólico cardiaco”) aunque el texto no comparta exactamente las mismas palabras.

## 5) Flujo de trabajo con embeddings (en este repo)

1. Scraping IFC → obtenemos (título, autores, journal, año, DOI, abstract).
2. “Texto de embedding” = título + abstract (si hay).
3. Modelo de embeddings (configurable) → vector por artículo.
4. Guardamos: matriz de vectores + metadatos del artículo.
5. Consulta/Matching:
   - Convertimos una consulta (o un artículo nuevo) a vector.
   - Buscamos vecinos más cercanos (k‑NN) por similitud coseno.
6. Con los k artículos más similares:
   - Clustering/temas (K‑Means) para entender áreas del instituto.
   - Selección de artículos para LLM y generación de guión.

Todo esto está orquestado en `EmbeddingsManager` (`src/embeddings/manager.py`).

## 6) Métrica: similitud coseno (cómo funciona)

- coseno(v, w) = (v·w) / (||v||·||w||) en [−1, 1]; mientras mayor, más similares.
- En la práctica normalizamos (||v||≈1), así el coseno ≈ producto punto.
- Recuperación: computamos coseno con todos los artículos y tomamos el top‑k.

## 7) Elección del modelo y multilingüe

- El proyecto usa Sentence Transformers (modelo configurable en `config.yaml`).
- Recomendaciones generales:
  - Inglés predominante: `all-MiniLM-L6-v2` (rápido, 384 dims) o `all-mpnet-base-v2` (mejor calidad, 768 dims).
  - Multilingüe (es/en): `distiluse-base-multilingual-cased-v2` o `paraphrase-multilingual-MiniLM-L12-v2`.
- IFC tiene publicaciones/temas bilingües; un modelo multilingüe puede ayudar a alinear español/inglés.

## 8) Granularidad: ¿documento completo o “chunks”?

- Resúmenes largos o textos completos pueden exceder el contexto óptimo del modelo.
- Estrategia habitual: dividir en “chunks” de ~200–400 palabras con solapamiento y generar un embedding por chunk.
- Recuperación por chunk ofrece grano fino (útil para pasajes concretos). Luego se reagrega por artículo para presentar resultados.
- En este proyecto, empezamos con título+abstract (documento corto). Para textos más largos, añadir “chunking” es un upgrade natural.

## 9) Indexado y rendimiento

- Para pocas decenas/miles de artículos, k‑NN exacto con NumPy/Scikit es suficiente.
- Para decenas de miles o más, conviene un índice aproximado (ANN): FAISS, HNSW (p. ej. en ChromaDB, Milvus, Qdrant). Este repo ya incluye `chromadb` como opción futura.
- Persistencia: guardar
  - Matriz de embeddings (n × d)
  - Metadatos (ID, título, DOI, año, etc.)
  - Nombre del modelo y versión (para reproducibilidad)

## 10) Clustering de temas (visión global)

- Con K‑Means sobre embeddings del IFC obtenemos grupos (temas latentes).
- Ayuda a:
  - Entender áreas de investigación del instituto.
  - Seleccionar términos/consultas para PubMed.
  - Guiar la narrativa del podcast (secciones por tema).

## 11) Limitaciones y buenas prácticas

- Dominio: modelos genéricos pueden no capturar matices muy especializados.
- Deriva temporal: nuevos artículos pueden desplazar “centros” temáticos; conviene re‑entrenar índices periódicamente.
- Multilingüe: si mezclamos es/en, usar modelo multilingüe.
- Longitud: para textos largos, usar “chunking”.
- Evaluación:
  - Inspección cualitativa de vecinos recuperados.
  - Coherencia de clusters.
  - Métricas internas (silhouette) si procede.

## 12) Cómo se conecta con el resto de la app

- Scraper IFC → base vectorial del IFC.
- PubMed → buscamos artículos recientes; opcionalmente también generamos embeddings para comparar con el “perfil IFC”.
- Recuperación: dado un tema/consulta, traemos k artículos del IFC y k de PubMed más cercanos.
- LLM: se le pasan resúmenes estructurados de esos artículos para generar el guion.
- Audio: el guion pasa a TTS.

## 13) Parámetros prácticos a decidir

- Modelo de embeddings (calidad vs velocidad, multilingüe o no).
- d (dimensión) viene dado por el modelo.
- Normalización L2 (recomendado para coseno).
- k (número de vecinos) para recuperación (p. ej., 5–20).
- Umbral de similitud (opcional) para filtrar resultados débiles.
- Chunk size/overlap (si se usa chunking).

## 14) FAQ rápida

- ¿Son palabras clave? → No. Son vectores densos aprendidos por un modelo; no mantenemos listas de keywords ni pesos manuales.
- ¿Qué “unidad” embebemos? → En este proyecto, título+abstract (frase/párrafo). Se puede extender a chunks de documento.
- ¿Cómo se calcula la similitud? → Principalmente coseno del ángulo entre vectores.
- ¿Por qué no solo búsqueda por palabras? → Embeddings permiten recuperar semánticamente (sin coincidencia exacta de términos) y combinan señales contextuales.

## 15) Próximos pasos sugeridos

- Cambiar a un modelo multilingüe si mezclamos español/inglés.
- Evaluar chunking para artículos largos.
- Añadir un índice ANN (Chroma/FAISS) si crece el corpus.
- Guardar versiones de modelo y artefactos para reproducibilidad.

---

Referencias útiles:

- Sentence-Transformers: <https://www.sbert.net/>
- FAISS (ANN): <https://github.com/facebookresearch/faiss>
- ChromaDB: <https://www.trychroma.com/>
