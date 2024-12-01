# Author: Borghini Davide (DavideB45 on GitHub)
# This File is a demo of the explainable chat that uses the RAG model
# The model is the one that is going to be used to generate the responses
# The chat is interactive and the user can ask questions to the model
# The model is juat used to generate the explanations
# The answer part is not implemented and is not supposd to be implemented in this file

from RAG import Rag
from StructuredOutput import KPIRequest, KPITrend
#from example_explainability import slowly_print
import os

# CReating the model (Ollama 3.2) that is the latest version of the model
# The model is the one that is going to be used to generate the responses
rag = Rag(model="llama3.2")

def interactive_chat():
    while True:
        # Read the user input
        user_input = input("Enter your query (or type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            print("Exiting the chat.")
            break
        if user_input == "":
            print("Error: The input is empty.")
            continue
        if user_input == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            continue
        destination = "None_str"
        # Try to get the destination 3 times
        for i in range(3):
            try:
                destination = rag.classify_query(user_input)
                object = rag.routing(destination).invoke({"query": user_input})
                # la funzione get_object(destination) controlla la variabile destination ed eventualmente ritorna o KPIRequest o KPITrend o null
                # object = rag.get_object(destination) -> explainableQuery function

                # exp_str = rag.get_explaination(object) -> trasforma in stringa object
                
                # result = rag.compute_query(object) -> chiamata API a gruppo x a seconda di che oggetto abbiamo passato
                # switch object:
                #   case KPIRequest:
                #       result = ApiRequestCallTopic8(KPIRequest)
                #   case KPITrend:
                #       result = ApiRequestCallTopic3(KPITrend)

                result=''
                if isinstance(object,KPIRequest):
                    result = ApiRequestCallTopic8(object)
                elif isinstance(object,KPITrend):
                    result = ApiRequestCallTopic3(object)

                #previous_answer= GET(qualcosa)
                
                # actual_answer = rag.direct_query(object, result, query, previous_answer) -> ritorna final answer che è la risposta data all'utente
                # rag.set_previous_answer(actual_answer)
                # print(exp_str, "\n\n", actual_answer)
            except:
                #print("Error: The model is broken.")
                print("...\r")
                continue
            if destination != "None_str":
                break
        if destination == "None_str":
            print("Error: The model is broken.")
        # If the destination is found, generate the response
        response = rag.explainableQuery(user_input, destination)
        print(f"Response:{response}")
        print("\n")

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Welcome to the Explainable Chat!")
    print("\nUseful prompts to test the model:")
    print("1) Give me the biweekly mean for the energy consumption KPI in 2023 of Large Capacity Cutting Machine when idle and Small Capacity Cutting Machine when working")
    print("2) Get the max of the consumption KPI of the Laser Machine in 2023? ")
    print("3) What is the speed of a plane?\n")
    interactive_chat()