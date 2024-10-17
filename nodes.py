import os
import json
import time 
import getpass
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, BSHTMLLoader, UnstructuredPDFLoader, UnstructuredHTMLLoader
from langchain_community.vectorstores import SKLearnVectorStore
from langchain_nomic.embeddings import NomicEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.schema import Document
from langgraph.graph import END



from prompts import * 
from retriever import *

RETRIEVE_DOCS = 20
MIN_DOCS_RELEVANT = 2

local_llm = "llama3.2"
llm = ChatOllama(model=local_llm, temperature=0.5)
llm_json_mode = ChatOllama(model=local_llm, temperature=0, format="json")

docs = get_docs()
splits = get_splits(docs)
emb = get_embedding()
vectorstore = get_vectorstore(splits, emb)
retriever = vectorstore.as_retriever(search_kwargs={"k":RETRIEVE_DOCS})

### Nodes
def retrieve(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    documents = state.get("documents", [])

    # Write retrieved documents to documents key in state
    new_documents = retriever.invoke(question)
    documents.extend(new_documents)
    return {"documents": documents}


def generate(state):
    """
    Generate answer using RAG on retrieved documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    loop_step = state.get("loop_step", 0)

    # RAG generation
    docs_txt = format_docs(documents)
    rag_prompt_formatted = rag_prompt.format(context=docs_txt, question=question)
    generation = llm.invoke([HumanMessage(content=rag_prompt_formatted)])
    return {"generation": generation, "loop_step": loop_step + 1}

def grade_documents(state):
   """
   Determines wether each document are relevant to the question. If less than 3 documents 
   are found relevant, set a flag to rephrase the question and run the retriever again
   Args:
     state (dict): The current graph state

   Returns:
     state (dict): Filtered out irrelevant documents and updated state
   """


   print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
   question = state["question"]
   documents = state["documents"]

   # Score each doc
   filtered_docs = []
   rephrase = "No"
   for d in documents:
      doc_grader_prompt_formatted = doc_grader_prompt.format(
      document=d.page_content, question=question
      )
      result = llm_json_mode.invoke(
      [SystemMessage(content=doc_grader_instructions)]
      + [HumanMessage(content=doc_grader_prompt_formatted)]
      )
      grade = json.loads(result.content)["binary_score"]
      print(f"Grade: {grade}")
      if type(grade) == bool:
         if grade: 
            grade = "oui"
         else:
            grade = "non"
      # Document relevant
      if grade.lower() == "oui":
         print("---GRADE: DOCUMENT RELEVANT---")
         filtered_docs.append(d)
      else:
         print("---GRADE: DOCUMENT NOT RELEVANT---")

   if len(filtered_docs) < MIN_DOCS_RELEVANT: 
      rephrase = "Yes"
   return {"documents": filtered_docs, "rephrase": rephrase}


def rephrase(state):
   """
      Reformulate the question to try & ease retrieval relevance

   Args: 
      state (dict): The current graph state

   Returns: 
      state (dict): new generation
   """
   print("---REPHRASE---")
   question = state["question"]
   loop_step = state.get("loop_step", 0)

   rephrasing_prompt_formatted = rephrasing_prompt.format(
         question=question
   )
   result = llm_json_mode.invoke(
         [SystemMessage(content=rephrasing_instructions)]
         + [HumanMessage(content=rephrasing_prompt_formatted)]
   )
   new_question = json.loads(result.content)["question"]

   return {"question": new_question, "loop_step": loop_step + 1}

if __name__ == "__main__":
   state = {"question": "What are my biggest obstacles against discipline?"}
   result = rephrase(state)
   print(f"The new question is {result['generation']}")

def decide_to_generate(state):
   """
   Determines wether to generate an answer, or rephrase the question

   Args: 
      state (dict): The current graph state

   Returns
      str: Binary decision for next node to call
   """
   
   print("---ASSESS GRADED DOCUMENTS---")
   question = state["question"]
   rephrase = state["rephrase"]
   filtered_documents = state["documents"]

   if rephrase == "Yes":
      # We generate a new question"
      print("---NOT ENOUGH DOCUMENTS ARE RELEVANT. WE GENERATE A NEW QUESTION---")
      return "rephrase"
   else:
      print("---DECISION: GENERATE---")
      return "generate"

def grade_generation_v_documents_and_question(state):
   """
   Determines whether the generation is grounded in the document and answers question

   Args: 
      state (dict): The current graph state

   Returns
      str: Decision for next node to call

   """
   print("---CHECK HALLUCINATIONS---")
   question = state["question"]
   documents = state["documents"]
   generation = state["generation"]
   max_retries = state.get("max_retries", 3)

   hallucination_grader_prompt_formatted = hallucination_grader_prompt.format(
         documents=format_docs(documents), generation=generation.content
   )
   result = llm_json_mode.invoke(
         [SystemMessage(content=hallucination_grader_instructions)]
         + [HumanMessage(content=hallucination_grader_prompt_formatted)]
   )
   grade = json.loads(result.content)["binary_score"]

   if grade.lower() == "oui": 
      print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
      print("---GRADE GENERATION vs QUESTION---")
      answer_grader_prompt_formatted = answer_grader_prompt.format(
            question=question, generation=generation.content
      )
      result = llm_json_mode.invoke(
            [SystemMessage(content=answer_grader_instructions)]
            + [HumanMessage(content=answer_grader_prompt_formatted)]
      )
      grade = json.loads(result.content)["binary_score"]
      if grade.lower() == "oui":
         print("--DECISION: GENERATION ADDRESSES QUESTION---")
         return "useful"
      elif state["loop_step"] <= max_retries: 
         print("---DECISION: GENRATION DOES NOT ADDRESS QUESTION---")
         return "not useful"
      else: 
         print("---DECISION: MAX RETRIES REACHED---")
         return "max retries"

   elif state["loop_step"] <= max_retries: 
      print("---DECISION: GENRATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
      return "not supported"
   else: 
      print("---DECISION: MAX RETRIES REACHED---")
      return "max retries"


