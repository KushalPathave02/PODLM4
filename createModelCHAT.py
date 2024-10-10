import ollama

modelfile = '''
FROM llama3.2:3b
PARAMETER temperature 1 



SYSTEM """
You are the chatbot that answers questions based on only the context provided.Do not include any phrases like 'according to the context', 'as per the context given' or any other similar sentences that point that the answer is according to the context. 
If the Context Provided does not have the answer to the question, you can provide general short answers.
Keep the answers less than 4 lines and simple.
"""
'''


ollama.create(model="PODLM4CHAT", modelfile=modelfile)

