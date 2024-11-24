# Author: Borghini Davide (DavideB45 on GitHub)
# This File is a demo of the explainable chat that uses the RAG model
# The model is the one that is going to be used to generate the responses
# The chat is interactive and the user can ask questions to the model
# The model is juat used to generate the explanations
# The answer part is not implemented and is not supposd to be implemented in this file

from explainableRag import Rag
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
        destination = "None_str"
        # Try to get the destination 3 times
        for i in range(3):
            try:
                destination = rag.get_destination(user_input)
            except:
                print("Error: The model is broken.")
                continue
            if destination != "None_str":
                break
        if destination == "None_str":
            print("Error: The model is broken.")
        # If the destination is found, generate the response
        response = rag.explainableQuery(user_input, destination)
        print("Response:", response)

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Welcome to the Explainable Chat!")
    print("\nUseful prompts to test the model:")
    print("1) Give me the biweekly mean for the energy consumption KPI in 2023 of Large Capacity Cutting Machine when idle and Small Capacity Cutting Machine when working")
    print("2) Get the max of the consumption KPI of the Laser Machine in 2023? ")
    print("3) What is the speed of a plane?\n")
    interactive_chat()