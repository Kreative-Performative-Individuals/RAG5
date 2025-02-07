import pickle
import bs4
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader

#### INDEXING ####
# Load Documents
# Load multiple documents
file_paths = [
    "/home/d.borghini/Documents/GitHub/RAG5/Explainability/pdf_files/UG.pdf",
    "/home/d.borghini/Documents/GitHub/RAG5/Explainability/pdf_files/AI_act.pdf",
    "/home/d.borghini/Documents/GitHub/RAG5/Explainability/pdf_files/Machines.pdf",
    "/home/d.borghini/Documents/GitHub/RAG5/Explainability/pdf_files/Upgrade.pdf"
]

docs = []
for file_path in file_paths:
    loader = PyMuPDFLoader(file_path=file_path)
    docs.extend(loader.load())
    print(f'docs loaded from {file_path}')
#CharacterTextSplitter for just text
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=400)
splits = text_splitter.split_documents(docs)
print('splits created')

# Embed
vectorstore = Chroma.from_documents(documents=splits, 
                                    embedding=OllamaEmbeddings(model="llama3.1:8b"),
                                    persist_directory="/home/d.borghini/Documents/GitHub/RAG5/Explainability/vectorstore")

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
