# Author: Borghini Davide (DavideB45 on GitHub)
# This File is a demo of the explainable chat that uses the RAG model
# The model is the one that is going to be used to generate the responses
# The chat is interactive and the user can ask questions to the model
# The model is juat used to generate the explanations
# The answer part is not implemented and is not supposd to be implemented in this file

from explainableRag import Rag
from example_explainability import slowly_print
import os

# CReating the model (Ollama 3.2) that is the latest version of the model
# The model is the one that is going to be used to generate the responses
rag = Rag(model="llama3.1:8b")

def interactive_chat():
    while True:
        # Read the user input
        user_input = input("\033[94mEnter your query (or type 'exit' to quit): \033[0m")
        print()
        if user_input.lower() == 'exit':
            print("Bye.")
            rag.close()
            break
        if user_input == "":
            print("Error: The input is empty.")
            continue
        if user_input == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            rag.reset()
            continue
        destination = "None_str"
        # Try to get the destination 3 times
        for i in range(3):
            try:
                destination = rag.get_destination(user_input)
            except:
                #print("Error: The model is broken.")
                slowly_print("...\r", delay=0.1)
                continue
            if destination != "None_str":
                break
        if destination == "None_str":
            print("Error: The model is broken.")
        # If the destination is found, generate the response
        try:
            response = rag.explainableQuery(user_input, destination)
            print("\n")
        except:
            print("An error occurred, sorry, try again.\n")
            continue
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Welcome to the Explainable Chat!")
    print("\nUseful prompts to test the model:")
    print("1) Translate the last message in french.")
    print("2) Get the max of the consumption KPI of the Laser Machine in 2023? ")
    print("3) What is there for lunch on monday?\n")
    interactive_chat()