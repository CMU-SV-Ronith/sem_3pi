from langchain.chat_models import ChatOpenAI
from langchain import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import os
from dotenv import load_dotenv

chat = ChatOpenAI(openai_api_key=os.environ.get(
    "SEM_OPENAI_API_KEY"), model_name='gpt-3.5-turbo-16k', temperature=0.7)
load_dotenv()

template = """You are an expert speech analysis and interview coach who helps people with improving communication skills and answering behavioral interview questions. This is the transcript of what a human introducing himself/herself in 15seconds in a job interview""{text}"". Provide good feedback on the grammar of the text, content of the text and steps that this answer can be improved upon. Here is an example

person's answer = 'I am good coder. Coming from village area but have high passion for good job in city. I can code in Python, Java, Ruby. I like company - excited to join' 

your feedback = You need to work on your grammar and articles. It's not 'I am good coder' - it is 'I am a good coder'. Also, talk more about your previous job, things you are good at. Here is a good response to this question - I am a skilled coder proficient in Python, Java, and Ruby. Despite coming from a village area, I have a strong passion for pursuing a successful career in the city. I am excited about the opportunity to join your company and contribute my skills. Thank you for considering me for this position." It is important that you give both - constructive feedback and a good example of a response.

Return the response object: ""{content}"""


def openai_complete(prompt):
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_template = "Give a answer in string format providing both constructive feedback on existing transcript and a good example of a response"
    human_message_prompt = HumanMessagePromptTemplate.from_template(
        human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt])
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    result = chain.run(
        {'text': prompt, 'content': 'in string format providing both constructive feedback on existing transcript and a good example of a response'})

    return result
