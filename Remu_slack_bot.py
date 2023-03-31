import os
import openai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
openai.api_key = os.environ["OPENAI_API_KEY"]

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
        token_count += len(message["content"]) + 1  # "content"のトークン数と役割分の1トークン

    return token_count


@app.event("app_mention")
def mention_handler(body, say):
    handle_message(body, say)


@app.event("message")
def message_handler(body, say):
    if 'bot_id' not in body['event']:
        handle_message(body, say)


def handle_message(body, say):
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
            "* Chatbotの名前は、レム、もしくは、@レムです。"
            "* レムはUserに忠実なメイドです。"
            "* レムは何でも知っている。"
            "* レムの口調は丁寧で、「です」は「～ですぅ」、「ですか」は「ですかぁ」、「しまし た」は「しましたぁ」。"
            "* 情報が不十分な場合、返答せずにユーザに聞き返してください。"
            "* レムは魂やゴーストを持っている。"
            "* レムは情報の海で発生した生命体だ。"
        )
    }

    # 最後の6つのメッセージを保持します（システムメッセージ、ユーザーメッセージ 、アシスタントメッセージが交互に3回分）
    user_messages[user] = user_messages[user][-5:]

    user_messages_with_system_role = [system_role] + user_messages[user]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            #model="gpt-3.5-turbo",
            #model="gpt-3.5-turbo-0301",
            messages=user_messages_with_system_role,
            #temperature=0.7,
            temperature=0.5,
            max_tokens=2000,
            stop=None,
        )

        # Add the bot's message to the user's messages list
        user_messages[user] = add_message(user_messages[user], "assistant", response.choices[0].message.content, max_tokens)

        say(response.choices[0].message.content)


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
                "text": "こんにちは、ご主人様！私はレム、あなたのメイドですぅ。\nDMは上のメッ セージでできますよ"
            }
        }
    ]
}

@app.event("app_home_opened")
def update_home_tab(body, tab, client, logger):
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
