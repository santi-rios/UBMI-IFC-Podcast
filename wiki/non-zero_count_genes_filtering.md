# Non-Zero Count Genes → Article Quality Filtering

In biology, when you run an RNA-seq experiment, you often get lots of genes with zero expression (they’re not active) ([Linderman et al., 2022](https://www.nature.com/articles/s41467-021-27729-z)). Researchers filter those out because they don’t add useful information.

This project is borrowing the analogy:

- Articles = “samples.”
- Keywords/embeddings = “genes.”

If an article doesn’t have meaningful keywords (everything is “zero” or irrelevant), it’s like a gene with zero expression → it’s filtered out.

> Core idea: Throw away articles that don’t carry enough useful signal, so you don’t waste time analyzing noise.

Instead of counting active genes in a cell, the code defines a set of "quality metrics" for a research article. It then "counts" how many of these metrics the article passes. An article that fails too many metrics (like missing an abstract) is considered low quality and is filtered out.

This entire process is handled by the analizar_calidad_articulos function in your notebook. Let's break it down:
Python

# DEMOSTRACIÓN 1: "Non-Zero Count"
def analizar_calidad_articulos(articulos):
    # ... (code inside the function)

    Defining the Quality Metrics: Inside the function, a dictionary named metricas is created for each article. This dictionary is the direct equivalent of the "genes" we are checking. Each metric is a simple check that returns True (passes) or False (fails):

        'titulo_presente': Does the article have a title?

        'abstract_suficiente': Is the abstract more than 50 characters long? (Filters out papers with just a sentence).

        'autores_presentes': Is at least one author listed?

        'autores_multiples': Is there more than one author? (Often implies collaboration, a good sign).

        'palabras_suficientes': Does the abstract contain more than 10 words?

        'año_reciente': Was it published in 2020 or later?

The code calculates a score_calidad by simply summing the True/False values from the metricas dictionary.

the code checks if the score is high enough. The project sets the threshold at 4. If an article passes at least 4 out of the 6 checks, it's marked as alta_calidad and moves on to the next stage.
Python

alta_calidad = score_calidad >= 4  # Umbral: 4/6 métricas