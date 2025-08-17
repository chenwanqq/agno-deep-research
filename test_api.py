import os
from openai import OpenAI
from dotenv import load_dotenv

client = OpenAI(
    # 若没有配置环境变量，请用阿里云百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=os.getenv("OPENAI_API_KEY"),  
    base_url=os.getenv("OPENAI_API_BASE_URL"),
)

completion = client.chat.completions.create(
    model="Moonshot-Kimi-K2-Instruct",
    messages=[
        {'role': 'user', 'content': '你是谁'}
    ]
)

print(completion.choices[0].message.content)