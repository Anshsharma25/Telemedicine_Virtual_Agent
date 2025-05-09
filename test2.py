import openai

openai.api_key = "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"
openai.api_base = "https://openrouter.ai/api/v1"

# Initial system message
messages = [
    {"role": "system", "content": "You are a helpful medical assistant."}
]

while True:
    user_input = input("User: ")
    
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat.")
        break

    messages.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        model="mistralai/mistral-7b-instruct",
        messages=messages
    )

    assistant_reply = response['choices'][0]['message']['content']
    messages.append({"role": "assistant", "content": assistant_reply})

    print(f"Assistant: {assistant_reply}\n")



