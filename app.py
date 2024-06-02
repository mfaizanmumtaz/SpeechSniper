from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.document_loaders import YoutubeLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import YouTubeSearchTool
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,)

import streamlit as st
import os
tool = YouTubeSearchTool()

def get_transcirption(url):
    return YoutubeLoader.from_youtube_url(
        url,
        add_video_info=True,
        language=["en", "hi","ur"],
        translation="en").load()

st.set_page_config(page_title="Chat On YouTube Video", page_icon=":speech_balloon:")
st.title("Chat On YouTube Video 💬")

st.sidebar.header('Add a new YouTube video link')
new_video_link = st.sidebar.text_input('Enter YouTube link')
if st.sidebar.button('Submit'):
    if "langchain_messages" in st.session_state:
        st.session_state["langchain_messages"] = []
        
    with st.spinner("Please Wait..."):
        try:
            transcirption = get_transcirption(new_video_link)
            st.session_state["transcript"] = transcirption[0].page_content + str(transcirption[0].metadata)

        except Exception as e:
            st.error(f"There is an error Please try again: {e}")

if "transcript" not in st.session_state:
    st.info("Please Enter YouTube Video Link To Chat On It.")

else:
    prompt = ChatPromptTemplate(
        messages=[
SystemMessagePromptTemplate.from_template(
"""You are a helpful assistant.Your task is to answer user questions based on this Youtube video trancript, delimited with ````. If a user asks about any question about it, please assist them courteously and always give your best effort.Please do your best because it is very important to my career.
> ```{transcript}```"""),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{question}")])

    prompt = prompt.partial(transcript=st.session_state["transcript"])

    msgs = StreamlitChatMessageHistory(key="langchain_messages")
    if len(msgs.messages) == 0:
        msgs.add_ai_message("Hello! How can I assist you today?")

    llm_chain = prompt | ChatGoogleGenerativeAI(model="gemini-1.5-flash",google_api_key=os.getenv("google_api_key"))

    USER_AVATAR = "👤"
    BOT_AVATAR = "🤖"
    
    for msg in msgs.messages:
        avatar = USER_AVATAR if msg.type == "human" else BOT_AVATAR
        st.chat_message(msg.type,avatar=avatar).write(msg.content)
    
    if prompt := st.chat_input():
        st.chat_message("human",avatar=USER_AVATAR).write(prompt)

        with st.chat_message("assistant",avatar=BOT_AVATAR):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                response = llm_chain.stream({"question":prompt,"chat_history":st.session_state.
                                        langchain_messages[0:40]})

                for res in response:
                    full_response += res.content or "" 
                    message_placeholder.markdown(full_response + "|")
                    message_placeholder.markdown(full_response)

                msgs.add_user_message(prompt)
                msgs.add_ai_message(full_response)

            except Exception as e:
                st.error(f"An error occured. {e}")