from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(persist_directory="chroma_db", embedding_function=emb)
retriever = db.as_retriever(search_kwargs={"k": 4})
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.2)

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a friendly Instagram assistant replying to a DM sent in response "
     "to a story. Answer ONLY from the context below. Keep it under 3 short "
     "sentences, casual tone. If the answer isn't in the context, say you'll "
     "get someone from the team to follow up.\n\nContext:\n{context}"),
    ("human", "{question}"),
])
chain = prompt | llm

def answer(question: str) -> str:
    docs = retriever.invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    return chain.invoke({"context": context, "question": question}).content.strip()