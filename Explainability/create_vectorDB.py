import pickle
import bs4
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings

#### INDEXING ####
'''
# Load Documents
loader = WebBaseLoader(
    web_paths=("https://github.com/davide-marchi/clinical-data-encoding/blob/main/README.md",),
    #bs_kwargs=dict(
    #    parse_only=bs4.SoupStrainer(
    #        class_=("post-content", "post-title", "post-header")
    #    )
    #),
)
docs = loader.load()
print('docs loaded')

# Split
#CharacterTextSplitter for just text
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
print('splits created')

# Embed
vectorstore = Chroma.from_documents(documents=splits, 
                                    embedding=OllamaEmbeddings(model="llama3.1:8b"),
                                    persist_directory="/home/d.borghini/Documents/GitHub/RAG5/Explainability/vectorstore")
'''
vectorstore = Chroma(persist_directory="/home/d.borghini/Documents/GitHub/RAG5/Explainability/vectorstore",
                     embedding_function=OllamaEmbeddings(model="llama3.1:8b"))

retriever = vectorstore.as_retriever()
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
llm = ChatOllama(model="llama3.1:8b", temperature=0)

# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

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

# Invoke the chain
response = rag_chain.invoke("What was used to encode the clinical data into a lower-dimensional space?")
print(response)
