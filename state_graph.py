import operator
from typing_extensions import TypedDict
from typing import List, Annotated
from langchain.schema import Document
from langgraph.graph import END, START
from langgraph.graph import StateGraph
from IPython.display import Image, display

from nodes import * 

class GraphState(TypedDict):
    """
    Graph state is a dictionary that contains information we want to propagate to, and modify in, each graph node.
    """

    question: str  # User question
    generation: str  # LLM generation
    web_search: str  # Binary decision to run web search
    max_retries: int  # Max number of retries for answer generation
    answers: int  # Number of answers generated
    loop_step: Annotated[int, operator.add]
    documents: List[str]  # List of retrieved documents


def main():
   workflow = StateGraph(GraphState)

   workflow.add_node("retrieve", retrieve)
   workflow.add_node("generate", generate)
   workflow.add_node("grade_documents", grade_documents)
   workflow.add_node("rephrase", rephrase)
   
   workflow.add_edge(START, "retrieve")
   workflow.add_edge("retrieve", "grade_documents")
   workflow.add_conditional_edges(
         "grade_documents",
         decide_to_generate,
         {
            "rephrase": "rephrase",
            "generate": "generate",
         },
   )

   workflow.add_edge("rephrase", "retrieve")

   workflow.add_conditional_edges(
         "generate",
         grade_generation_v_documents_and_question,
         {
            "not supported": "generate",
            "useful": END, 
            "not useful": "rephrase",
            "max retries": END,
         },
   )

   graph = workflow.compile()
   #img = Image(graph.get_graph().draw_mermaid_png())
   #with open("workflow_graph.png", "wb") as f:
    #f.write(img.data)

   with open("conf.json", "r") as f: 
      data = json.loads(f.read())
      question = data["question"]

   inputs = {"question": question, "max_retries": 3}
   for event in graph.stream(inputs, stream_mode="values"):
      print(event)

if __name__ == "__main__":
   main()
