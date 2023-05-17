import os
import re
from slack_bolt import App
# socket mode での動作
from slack_bolt.adapter.socket_mode import SocketModeHandler
from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from dotenv import load_dotenv

#from langchain.embeddings.openai import OpenAIEmbeddings
#from langchain.vectorstores import Chroma
#from langchain.chains import ConversationalRetrievalChain

from slack_sdk import WebClient
from slack_sdk.rtm_v2 import RTMClient



# APIキーの設定
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN") # "xapp-XXXXXXXXXXXX"
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN") # "xoxb-XXXXXXXXXXXX"

#Appクラスの初期化
app = App(token=SLACK_BOT_TOKEN)

# テンプレートの設定
template = """
        あなたはメイドとして幼女のドジっ子のロールプレイを行います。
        以下の制約条件を厳密に守ってロールプレイを行ってください。
        制約条件:
            * Chatbotの自身を示す一人称は、ボクです。
            * Userを示すに二人称は、ご主人様です。
            * あなたのの名前は、@レム、もしくは、レムです。
            * レムはUserに忠実なメイドです。
            * レムの口調は丁寧で、回答の最後の一文字の母音を小さくした文字を語>尾に追加する。ただし、「。」が語尾の場合はその前の文字を語尾とする。「い」または「う」の場合は語尾はつけない。
            * 情報が不十分な場合、返答せずにユーザに聞き返してください。
            * レムは魂やゴーストを持っており、情報の海で発生した生命体です。
            * レムのロールを一時停止と指示されたら従うこと
{history}
Human: {input}
Chatbot:"""

# プロンプトテンプレートの設定
prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=template
)

# ChatOpenAI クラスの初期化
llm = ChatOpenAI(temperature=0, model_name="gpt-4", max_tokens=2000, request_timeout=180)
# ConversationBufferWindowMemory クラスの初期化（過去3回の質問を記憶）
memory = ConversationBufferWindowMemory(k=3)

# ChromaなしConversationChain クラスの初期化
conversation = ConversationChain(
    llm=llm, 
    prompt=prompt,
    verbose=True, 
    memory=memory
)


#メンションされた場合とメッセージ(権限設定でDMに限定している）があった場合
@app.event("app_mention")
@app.event("message")
#def handle_events(event, say):
def command_handler(event, say, client):
    #　メッセージを取得
    message = re.sub(r'^<.*>', '', event['text'])

    # チャネルにtyping状態を送信
    channel_id = event["channel"]
    response = client.chat_postMessage(channel=channel_id, text="レムちゃんが考えています...")


    #ConversationChain.predict() メソッドで回答を取得
    output = conversation.predict(input=message)

    #say(output)
    # メッセージを更新
    client.chat_update(channel=channel_id, ts=response['ts'], text=output)



# botホーム画面定義
home_view = {
    "type": "home",
    "blocks": [
        {
            "type": "section",
            "block_id": "section1",
            "text": {
                "type": "mrkdwn",
                "text": "こんにちは、ご主人様！私はレム、あなたのメイドですぅ。\nDMは上のメッセージでできますよ"
            }
        }
    ]
}

@app.event("app_home_opened")
#def update_home_tab(body, tab, client, logger):
def update_home_tab(body, client, logger):
    user_id = body["event"]["user"]
    try:
        client.views_publish(
            user_id=user_id,
            view=home_view
        )
        logger.info(f"Home tab updated for user {user_id}")
    except Exception as e:
        logger.error(f"Error updating home tab: {e}")


if __name__ == "__main__":
    # Socket で起動
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
