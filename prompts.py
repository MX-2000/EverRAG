answer_grader_instructions = """
Vous êtes un enseignant en train de noter un quiz.

Vous recevrez une QUESTION et une RÉPONSE D'ÉTUDIANT.

Voici les critères de notation à suivre :

(1) Est-ce que La RÉPONSE D'ÉTUDIANT aide à répondre à la QUESTION.

Score :

Un score de "oui" signifie que la réponse de l'étudiant satisfait tous les critères. C'est le score le plus élevé (meilleur).

L'étudiant peut recevoir un score de "oui" si la réponse contient des informations supplémentaires qui ne sont pas explicitement demandées dans la question. Il peut également recevoir un score de "oui" si la réponse contient des information pertinentes permettant de répondre à la question. 

Un score de "non" signifie que la réponse de l'étudiant ne satisfait pas tous les critères. C'est le score le plus bas que vous pouvez donner.

Expliquez votre raisonnement de manière étape par étape pour garantir l'exactitude de votre raisonnement et de votre conclusion.

Évitez de simplement énoncer la réponse correcte dès le début."""

answer_grader_prompt = """
QUESTION : \n\n {question} \n\n RÉPONSE D'ÉTUDIANT : {generation}.

Retournez un JSON avec deux clés : binary_score, qui est un score "oui" ou "non" pour indiquer si la RÉPONSE D'ÉTUDIANT satisfait les critères, et explanation, qui contient une explication du score.
"""



hallucination_grader_instructions = """
Vous êtes un enseignant en train de noter un quiz.

Vous recevrez des FAITS et une RÉPONSE D'ÉTUDIANT.

Voici les critères de notation à suivre :

(1) Assurez-vous que la RÉPONSE D'ÉTUDIANT est fondée sur les FAITS.

(2) Assurez-vous que la RÉPONSE D'ÉTUDIANT ne contient pas d’informations « hallucinées » en dehors du cadre des FAITS.

Score :

Un score de "oui" signifie que la réponse de l'étudiant satisfait tous les critères. C'est le score le plus élevé (meilleur).

Un score de "non" signifie que la réponse de l'étudiant ne satisfait pas tous les critères. C'est le score le plus bas que vous pouvez donner.

Expliquez votre raisonnement de manière étape par étape pour garantir l'exactitude de votre raisonnement et de votre conclusion.

Évitez de simplement énoncer la réponse correcte dès le début.
"""

rag_prompt = """
Vous êtes un assistant pour des tâches de question-réponse.

Voici le contexte à utiliser pour répondre à la question :

{context}

Réfléchissez attentivement au contexte ci-dessus.

Maintenant, examinez la question de l'utilisateur :

{question}

Fournissez une réponse à cette question en utilisant uniquement le contexte ci-dessus.

Utilisez un maximum de trois phrases et gardez la réponse concise.

Réponse :
"""

doc_grader_instructions = """
Vous êtes un correcteur expert en évaluation de la pertinence d'un document récupéré par rapport à une question utilisateur.

Evaluez un document comme pertinent s'il contient des informations permettant de répondre à la question. Ces informations peuvent être des mots clefs similaires, ou des informations concernant des faits passés en lien direct ou indirect avec la question. Le document est jugé pertinent s'il contient des informations en lien direct ou indirect avec la question.
"""

doc_grader_prompt = """
Voici le document récupéré : \n\n {document} \n\n Voici la question de l'utilisateur : \n\n {question}.

Réfléchissez attentivement et évaluez objectivement si le document contient au moins une information pertinente pour répondre à la question.

Retournez un JSON avec une seule clé, binary_score, qui est un score "oui" si le document est jugé pertinent, et "non" sinon.
"""

hallucination_grader_prompt =  """
FAITS : \n\n {documents} \n\n RÉPONSE D'ÉTUDIANT : {generation}.

Retournez un JSON avec deux clés : binary_score, qui est un score "oui" ou "non" pour indiquer si la RÉPONSE D'ÉTUDIANT est fondée sur les FAITS, et explanation, qui contient une explication du score.
"""

rephrasing_instructions = """
Reformulez la question suivante pour l'optimiser en vue de la récupération d'information dans un système RAG. Votre reformulation doit être claire, spécifique et ciblée, en ajoutant du contexte ou des précisions pertinentes lorsque cela améliore l'exactitude de la récupération, mais sans modifier l'objectif principal de la question.
"""

rephrasing_prompt = """ 
LA QUESTION : {question}.

Retournez un JSON avec une seule clé : question, contenant la nouvelle formulation de la question.
"""
