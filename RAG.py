import ollama
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pdfExtractor import extractText

client = ollama.Client()
embeddingModel = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
chromaClient = chromadb.Client()

def getOrCreateCollection(name="ragDocuments"):
    existingCollections = chromaClient.list_collections()
    for col in existingCollections:
        if col.name == name:
            return chromaClient.get_collection(name=name)
    return chromaClient.create_collection(name=name, embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction())

def loadDocument(file):
    filePath = file.name
    return extractText(filePath)

def chunkText(text, chunkSize=300):
    words = text.split()
    chunks = [' '.join(words[i:i + chunkSize]) for i in range(0, len(words), chunkSize)]
    return chunks

collection = getOrCreateCollection()

def addDocumentToVectorDb(docId, text):
    chunks = chunkText(text)
    embeddings = embeddingModel.encode(chunks)
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        collection.add(
            documents=[chunk],
            embeddings=[embedding.tolist()],
            ids=[f"{docId}chunk{i}"]
        )
    print(f"Document '{docId}' has been added to the vector database with {len(chunks)} chunks.")

def retrieveRelevantChunks(query, topK=3):
    queryEmbedding = embeddingModel.encode([query])[0]
    records = collection.get(include=["embeddings", "documents"])
    if len(records["embeddings"]) == 0 or len(records["documents"]) == 0:
        print("No documents are present in the vector database. Please add a document first.")
        return []
    embeddings = np.array(records["embeddings"])
    similarities = cosine_similarity([queryEmbedding], embeddings)[0]
    topIndices = np.argsort(similarities)[-topK:][::-1]
    topChunks = [records["documents"][idx] for idx in topIndices]
    return topChunks

def generateResponse(conversationHistory, question):
    relevantChunks = retrieveRelevantChunks(question)
    combinedText = ' '.join(relevantChunks)
    if not combinedText:
        return "No relevant information found in the document."

  


    prompt = f"HISTORY: {conversationHistory} \nONLY Use the following context to answer the question:\n\n{combinedText}\n\nQuestion: {question}"
    response = client.generate(
        model="llama3.2:3b", 
        prompt=prompt
    )['response']

    print(f"Generated response: {response}")  # Debugging statement
    return response