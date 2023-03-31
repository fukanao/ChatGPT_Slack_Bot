# ChatGPT_Slack_Bot
- ChatGPT APIとSlack Botを接続するPythonコードです
- 作成時点のAPIは gpt-3.5-turboになります
- システムのロールはリゼロの人。好みに書き換えてOK
- ubuntu上で起動させることが前提
- 8割はChatGPT-4に聞きました
----------------

## インストール

UbuntuでPythonスクリプトを起動時に自動実行するには、systemdを使用してサービスを作成します。以下の手順で進めてください。

まず、Pythonスクリプトを保存しておくディレクトリを作成します。ここでは/opt/slackbotとします。適切な権限を与えるために、以下のコマンドを実行します。

    sudo mkdir /opt/slackbot
    sudo chown $USER:$USER /opt/slackbot
作成したディレクトリに先程のPythonスクリプト（例：Remu_slack_bot.py）を保存します。

Slack Botに必要な環境変数を設定するため、/opt/slackbotディレクトリに.envという名前のファイルを作成し、以下の内容で編集します。


    OPENAI_API_KEY=your_openai_api_key
    SLACK_APP_TOKEN=your_slack_app_token
    SLACK_BOT_TOKEN=your_slack_bot_token
    
ここで、your_*を実際のtokenに置き換えてください。
systemdサービスファイルを作成します。/etc/systemd/systemディレクトリにslackbot.serviceという名前のファイルを作成し、以下の内容で編集します。


    [Unit]
    Description=SlackBot Service
    After=network.target
    
    [Service]
    Type=Simple
    User=your_username
    Group=your_username
    WorkingDirectory=/opt/slackbot
    EnvironmentFile=/opt/slackbot/.env
    ExecStart=/usr/bin/python3 /opt/slackbot/Remu_slack_bot.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
ここで、your_usernameを実際のユーザー名に置き換えてください。

systemdに新しいサービスファイルがあることを認識させ、自動起動を有効にします。


    sudo systemctl daemon-reload
    sudo systemctl enable slackbot.service
サービスを開始します。


    sudo systemctl start slackbot.service
これで、Ubuntuの起動時にPythonスクリプトが自動的に実行されるようになります。サービスの状態を確認するには、以下のコマンドを使用します。



    sudo systemctl status slackbot.service
サービスを停止するには、以下のコマンドを使用します。

    sudo systemctl stop slackbot.service

## Slack API設定

APP管理　-> Create New App -> From Scratch

AppName: アプリ名
WorkSpace: 使用したいワークスペース

App-Level Tokens: connections:write作成
Socket Mode: enable

### Bots
Always Show My Bot as Online: enable

Home Tab: enable

Messages Tab: enable

Allow users to send Slash commands and messages from the messages tab: enable

### Event Subscriptions
Enable Events: enable

Subscribe to bot events

    app_mention
    message:im
    app_home_opened

### OAuth and Permissions
Scopes

    app_mentions:read
    chat:write
    chat:write.customize
    groups:write
    im:history
    im:read
    im:write
