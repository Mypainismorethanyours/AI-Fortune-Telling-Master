# AI Fortune-Telling Master
## Overview
AI Fortune-Telling Master is an AI agent proficient in Chinese Feng Shui, capable of calculating Ba Zi (the Eight Characters), casting hexagrams, interpreting dreams, and more. Currently, the agent supports deployment on Telegram.
Through this project, you can easily transform it into any type of AI assistant, such as an e-commerce customer service agent, by integrating various APIs or local knowledge bases

## Prerequisites
1. Required packages
```shell
pip install -r requirements.txt
```
2. [OpenAI API Key](https://openai.com/blog/openai-api)
3. [Yuanfenju API Key](https://doc.yuanfenju.com/overview/index.html)
Yuanfenju API provides research on traditional Chinese culture.
4. Microsoft TTS API
5. Telegran HTTP API

## Run
1. Start the Redis:
```shell
redis-server
```
2. Start the server:
```shell
python server.py
```

## Feature
* Fortune-telling
* Real-time search
* Memory
* Professional knowledge base
* /chat, POST request
* /add_urls, Learn knowledge from the URL

## Deployment
* On Telegram: First use BotFather(https://t.me/BotFather) to create new bot accounts.
```shell
python tele.py
```


## Demo
https://github.com/Mypainismorethanyours/AI-Fortune-Telling-Master/assets/109569168/e9bb8fc2-b37b-4edc-868b-ef60fedb9211
