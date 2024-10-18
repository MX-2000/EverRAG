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

with open("keys.json", "r") as f: 
   data = json.loads(f.read())
   journal_directory = data["journal_directory"]

def _get_key(var: str):
   with open("conf.json", "r") as f: 
      data = json.loads(f.read()) 
   result = data[var]    
   return result 

os.environ["TOKENIZERS_PARALLELISM"] = "true"
def get_docs():

   #html_file = "Journaling.html"
   directory = journal_directory
   docs = []
   for filename in os.listdir(directory):
      if filename.endswith("html"):
         file_path = os.path.join(directory, filename)
         loader = BSHTMLLoader(file_path=file_path)
         docs.extend(loader.load())

   return docs

def get_docs_pdf():

   file = "Journaling.pdf"
   #loader = UnstructuredPDFLoader(file_path=file)
   loader = PyPDFLoader(file)
   pages = loader.load_and_split()
   return pages

def get_splits(docs, splitter="recursive"):
   if splitter == "recursive":
      text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
          chunk_size=500, chunk_overlap=100
      )
   else:
      text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=100,
            chunk_overlap=10,
      )
   doc_splits = text_splitter.split_documents(docs)
   
   return doc_splits

def get_embedding():
   embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",model_kwargs={"device":"cpu"})
   #embedding = NomicEmbeddings(model="nomic-embed-text-v1.5", inference_mode="local")
   return embedding

def get_vectorstore(doc_splits, embedding):
   vectorstore = SKLearnVectorStore.from_documents(
         documents=doc_splits,
         embedding=embedding,
   )
   return vectorstore

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


if __name__ == "__main__":

   local_llm = "llama3.2"
   llm = ChatOllama(model=local_llm, temperature=0)
   llm_json_mode = ChatOllama(model=local_llm, temperature=0, format="json")

   docs = get_docs()
   splits = get_splits(docs)
   emb = get_embedding()
   vectorstore = get_vectorstore(splits, emb)
   retriever = vectorstore.as_retriever(search_kwargs={"k":8})

   question = "What are the biggest obstacles I'm facing in maintining discipline?"
   docs = retriever.invoke(question)
   print(f"There are {len(docs)} found")
   print([doc.page_content for doc in docs])
