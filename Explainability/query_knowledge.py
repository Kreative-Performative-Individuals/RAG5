import pickle
import time
import bs4
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings

vectorstore = Chroma(persist_directory="/home/d.borghini/Documents/GitHub/RAG5/Explainability/vectorstore",
                     embedding_function=OllamaEmbeddings(model="llama3.1:8b"))

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={'k': 7, 'fetch_k': 21}
)

print('retriever created')

#### RETRIEVAL and GENERATION ####

# Prompt
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a knowledgeable AI assistant. Use the provided context to answer the question.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    )
)
# LLM
llm = ChatOllama(model="llama3.1:8b")

print('creating chain')
# Chain

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print('chain created')


# Retrieve and generate answer
#question = "What are the system requirements?"
#question = "What is mensa martiri menu retrieval?"
#question = "What was added in the last update?"
#question = " Tell me something about metal cutting machine?"
question = "what is the risk level of the application according to the Ai act?"
print(question + '\n')
print(format_docs(retriever.invoke(question)))
exit()
# Invoke the chain
start = time.time()
response = rag_chain.invoke("What are the system requirements?")
end = time.time()
print(f"Time elapsed: {end - start}")
print(response)
