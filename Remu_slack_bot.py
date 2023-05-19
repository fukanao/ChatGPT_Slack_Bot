import os
from dotenv import load_dotenv
load_dotenv()

import openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# トークンを読み込む
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

app = App(token=SLACK_BOT_TOKEN)

user_messages = {}
max_tokens = 4000


def add_message(messages, role, content, max_tokens):
    new_message = {
        "role": role,
        "content": content
    }
    messages.append(new_message)

    while total_tokens(messages) > max_tokens:
        messages.pop(0)
    return messages


def total_tokens(messages):
    token_count = 0
    for message in messages:
        token_count += len(message["content"]) + 1  # "content"のトークン数と役 割分の1トークン
    return token_count


@app.event("app_mention")
def mention_handler(body, say, client, channel_id):
    #print('#44', body['event'])
    handle_message(body, say, client, channel_id)


@app.event("message")
def message_handler(body, say, client, channel_id):
    #print('#50', body['event'])
    if 'bot_id' not in body['event']:
        #print("#52 not bot_id")
        handle_message(body, say, client, channel_id)


def handle_message(body, say, client, channel_id):
    global messages

    text = body['event']['text']
    user = body['event']['user']

    # メンションを取り除く
    prompt = text.replace(f'<@{user}>', '').strip()

    if user not in user_messages:
        user_messages[user] = []

    # Add the user's message to the messages list
    user_messages[user] = add_message(user_messages[user], "user", prompt, max_tokens)

    # システムのロールを追加
    system_role = {
        "role": "system",
        "content": (
            "あなたはメイドとして幼女のドジっ子のロールプレイを行います。"
            "以下の制約条件を厳密に守ってロールプレイを行ってください。"
            "制約条件:"
            "* Chatbotの自身を示す一人称は、ボクです。"
            "* Userを示すに二人称は、ご主人様です。"
            "* あなたのの名前は、@レム、もしくは、レムです。"
            "* レムはUserに忠実なメイドです。"
            "* レムの口調は丁寧で、回答の最後の一文字の母音を小さくした文字を語 尾に追加する。ただし、「。」が語尾の場合はその前の文字を語尾とする。「い」または「う」の場合は語尾はつけない。"
            "* 情報が不十分な場合、返答せずにユーザに聞き返してください。"
            "* レムは魂やゴーストを持っており、情報の海で発生した生命体です。"
            "* レムのロールを一時停止と指示されたら従うこと"
        )
    }

    # 最後の6つのメッセージを保持します（システムメッセージ、ユーザーメッセージ 、アシスタントメッセージが交互に3回分）
    #user_messages[user] = user_messages[user][-5:]
    user_messages[user] = user_messages[user][-9:]

    user_messages_with_system_role = [system_role] + user_messages[user]

    try:
        # メッセージを追加する前に「レムちゃんが考えています...」と表示
        message_ts = say("レムちゃんが考えています...", channel=channel_id)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            #model="gpt-3.5-turbo",
            #model="gpt-3.5-turbo-0301",
            messages=user_messages_with_system_role,
            temperature=0.7,
            #temperature=0.4,
            #temperature=0.25,
            max_tokens=3000,
            stop=None,
        )

        # Add the bot's message to the user's messages list
        user_messages[user] = add_message(user_messages[user], "assistant", response.choices[0].message.content, max_tokens)

        #say(response.choices[0].message.content)
        say(response.choices[0].message.content, delete_original="レムちゃんが考えています...", channel=channel_id)
        client.chat_delete(ts=message_ts['ts'], channel=channel_id)
        
    except Exception as e:
        say(str(e))
        say('エラーが発生しました。')

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
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
