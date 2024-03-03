import os
import google.generativeai as genai
import requests
import json
import sys


import gpt_functions



api_key=os.getenv('API_KEY')
#genai.configure(api_key=os.getenv('API_KEY'))


def parse_function_response(message):
    function_call = message[0]["functionCall"]
    function_name = function_call["name"]

    print("GPT: Called function " + function_name )

    try:
        arguments = function_call["args"]

        if hasattr(gpt_functions, function_name):
            function_response = getattr(gpt_functions, function_name)(**arguments)
        else:
            function_response = "ERROR: Called unknown function"
    except:
        function_response = "ERROR: Invalid arguments"

    return (function_name, function_response)


def run_conversation(message, messages = []):
    messages.append(message)

    with open("messages.json", "w") as f:
        f.write(json.dumps(messages, indent=4))

    data={
        "contents": [messages],
        "tools":[{
            "functionDeclarations": gpt_functions.definitions,
        }]

    }    

    response =  requests.post("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key="+api_key , json=data)
    print(response)
    if response.status_code != 200:
        print("Error calling Gemini API:", response.text)
        # Consider logging the error or retrying
        sys.exit(1)
    response = response.json()
    
    message = response["candidates"][0]["content"]["parts"]
    messages.append({
        "role": "model",
        "parts": message
    })
    print(message)
    if "functionCall" in message[0]:
        function_name, function_response = parse_function_response(message)

        message = {
            "role": "function",
            "parts": [{
                "functionResponse": {
                    "name": function_name,
                    "response":{
                        "name": function_name,
                        "content": function_response
                    }
                }
                   
               }]
        }
    else:
        print("GPT: " + message[0]["text"])
        user_message = input("GPT: " + message[0]["text"] + "\nYou: ")
        message = {
            "role": "user",
            "parts": [{"text":user_message}]
        }       

    run_conversation(message, messages)
messages = []

system_message = "You are an AI bot that can do everything using function calls. When you are asked to do something, use the function call you have available and then respond with a message confirming what you have done."

user_message = input("GPT: What do you want to do?\nYou: ")
message = {
    "role": "user",
    "parts": [{"text":system_message + "\n\n" +user_message}]
}

run_conversation(message, messages)
