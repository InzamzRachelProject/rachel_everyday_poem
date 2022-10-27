import json
import logging
import os
import time

import requests

TGBOT_TOKEN = ""
TG_CHANNEL = ""
TG_GROUP = ""


# result_dict = {
#     'title': poem_title,
#     'author': {'name': poem_author, 'brief_info': poem_author_info},
#     'background': poem_background_info,
#     'content': poem_context,
#     'translate': poem_translate_list[0],
#     'reference': poem_reference_string,
#     'keyword': poem_translate_list[1],
#     'appreciation': poem_appreciation_list,
#     'famous': famous_sentence,
# }
def tgbot_sent_channel(poem_dict: dict, poem_str: str):
    global TGBOT_TOKEN
    global TG_CHANNEL
    global TG_GROUP
    TGBOT_TOKEN = os.getenv('TGBOT_TOKEN')
    TG_CHANNEL = os.getenv('TG_CHANNEL')
    TG_GROUP = os.getenv('TG_GROUP')

    url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/getUpdates"
    responce = requests.request("Get", url)
    latest_update_id = 0
    for update in responce.json()['result']:
        latest_update_id = max(latest_update_id, update['update_id'])

    poem_main_content = poem_dict['title'] + '\n'
    poem_main_content += poem_dict['author']['name'] + '\n'
    poem_main_content += poem_dict['content'] + '\n'
    poem_main_content += '\n' + poem_dict['translate'].replace('译文', '<b>译文</b>')
    poem_main_content = poem_main_content.replace(
        poem_dict['title'], '<b>' + poem_dict['title'] + '</b>'
    )
    poem_main_content = poem_main_content.replace(
        poem_dict['famous'], '<b>' + poem_dict['famous'] + '</b>'
    )

    url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/sendMessage?chat_id={TG_CHANNEL}&text={poem_main_content}&parse_mode=HTML"
    responce = requests.request("Get", url)
    if not responce.json()['ok']:
        logging.log(
            logging.ERROR,
            f"{responce.json()['error_code']}: {responce.json()['description']}",
        )
        return
    channel_message_id = responce.json()['result']['message_id']
    group_message_id = 0

    # 等待消息的发送，防止立刻获取更新无法得到在Group的消息Update
    time.sleep(5)
    url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/getUpdates?offset={latest_update_id}"
    responce = requests.request("Get", url)
    # print(responce.json())
    for update in responce.json()['result']:
        if (
                str(update['message']['sender_chat']['id']) == TG_CHANNEL
                and update['message']['forward_from_message_id'] == channel_message_id
        ):
            group_message_id = update['message']['message_id']

    # 在Group中回复可以实现Channel中显示为评论，这样大大减少了古诗赏析Channel中的显示面积
    # 你只需要在想要看的时候进入评论区，而不是大段的文字堆积在Channel
    url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/sendMessage?chat_id={TG_GROUP}&text={poem_dict['keyword'].replace('注释', '<b>注释</b>')}&parse_mode=HTML&reply_to_message_id={group_message_id}"
    responce = requests.request("Get", url)
    time.sleep(1)
    url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/sendMessage?chat_id={TG_GROUP}&text={poem_dict['background'].replace('创作背景', '<b>创作背景</b>')}&parse_mode=HTML&reply_to_message_id={group_message_id}"
    responce = requests.request("Get", url)
    time.sleep(1)
    url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/sendMessage?chat_id={TG_GROUP}&text={poem_dict['author']['brief_info'].replace('作者简介', '<b>作者简介</b>')}&parse_mode=HTML&reply_to_message_id={group_message_id}"
    responce = requests.request("Get", url)
    time.sleep(1)
    cnt = 1
    for each in poem_dict['appreciation']:
        each = f'<b>赏析{cnt}</b>\n' + each
        cnt += 1
        url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/sendMessage?chat_id={TG_GROUP}&text={each}&parse_mode=HTML&reply_to_message_id={group_message_id}"
        responce = requests.request("Get", url)
        time.sleep(1)
    url = f"https://api.telegram.org/bot{TGBOT_TOKEN}/sendMessage?chat_id={TG_GROUP}&text={poem_dict['reference'].replace('参考资料', '<b>参考资料</b>')}&parse_mode=HTML&reply_to_message_id={group_message_id}"
    responce = requests.request("Get", url)


def main():
    f = open("../poem/征怨.json")
    poem_str = f.read()
    f.close()
    poem_dict = json.loads(poem_str)
    tgbot_sent_channel(poem_dict, poem_str)


if __name__ == '__main__':
    main()
