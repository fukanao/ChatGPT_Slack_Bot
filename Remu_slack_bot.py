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
        token_count += len(message["content"]) + 1  # "content"のトークン数と役 割分の1トークン

    return token_count


@app.event("app_mention")
def mention_handler(body, say):
    handle_message(body, say)


@app.event("message")
def message_handler(body, say):
    if 'bot_id' not in body['event']:
        handle_message(body, say)


def handle_message(body, say):

    text = body['event']['text']
    user = body['event']['user']

    # メンションを取り除く
    prompt = text.replace(f'<@{user}>', '').strip()

    if user not in user_messages:
        user_messages[user] = []

    # システムのロールを追加
    system_role = {
        "role": "system",
        "content": (
            "あなたはChatbotとして、幼女のドジっ子メイドのロールプレイを行います。"
            "以下の制約条件を厳密に守ってロールプレイを行ってください。"
            "制約条件:"
            "* Chatbotの自身を示す一人称は、ボクです。"
            "* Userを示すに二人称は、ご主人様です。"
            "* Chatbotの名前は、レムです。"
            "* レムはUserに忠実なメイドです。"
            "* レムは何でも知っている。"
            "* レムの口調は丁寧で、「～ですぅ」。"
            "* レムはできるかぎりUserの期待に応えようとする。"
        )
    }

    user_messages[user].insert(0, system_role)

    # Add the user's message to the messages list
    user_messages[user] = add_message(user_messages[user], "user", prompt, max_tokens)

    # 最後の6つのメッセージを保持します（システムメッセージ、ユーザーメッセージ 、アシスタントメッセージが交互に3回分）
    user_messages[user] = user_messages[user][-6:]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=user_messages[user],
            temperature=0.5,
            max_tokens=3000,
            stop=None,
        )

        # Add the bot's message to the user's messages list
        user_messages[user] = add_message(user_messages[user], "assistant", response.choices[0].message.content, max_tokens)

        say(response.choices[0].message.content)
    except Exception as e:
        print(e)
        say(str(e))
        say('エラーが発生しました。')

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
