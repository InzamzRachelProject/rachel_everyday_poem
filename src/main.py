import json
import os

import bs4
import requests
import selenium.webdriver.common.by
from bs4.element import Tag, NavigableString
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

from telegram_bot import tgbot_sent_channel

CHROME_DRIVER_PATH = ""


def parse_poem_html(poem_html: str, famous_sentence: str) -> (dict, str):
    soup = bs4.BeautifulSoup(poem_html, 'html.parser')
    poem_title = soup.find('h1').text
    # print("poem_title: ", poem_title)
    poem_author = soup.find('p', class_='source').text
    # print('poem_author: ', poem_author)
    poem_content_pre = soup.find('div', class_='contson')
    poem_content = ""
    for each in poem_content_pre.contents:
        if isinstance(each, bs4.element.Tag) and each.name == 'br':
            poem_content += '\n'
        else:
            poem_content += each.text.strip()
    # print('poem_context: ', poem_context)
    poem_translate_id_list = []
    poem_shangxi_id_list = []
    main3_div = soup.find('div', class_='main3')
    main3_divs = main3_div.find_all()
    for each in main3_divs:
        if not each.get('id'):
            continue
        id_str = str(each.get('id'))
        if id_str.find('fanyi') != -1 and id_str.find('fanyiPlay') == -1:
            poem_translate_id_list.append(id_str)
        if id_str.find('shangxi') != -1 and id_str.find('shangxiPlay') == -1:
            poem_shangxi_id_list.append(id_str)
    for each in poem_translate_id_list:
        if each.find('quan') != -1:
            continue
        # 此处我偷懒了，发现fanyi和shangxi都是以i结尾并且只出现一次
        # 然后又发现其实放在两个列表里面无所谓
        if each.replace('i', 'iquan') in poem_translate_id_list:
            poem_translate_id_list.remove(each)
    for each in poem_shangxi_id_list:
        if each.find('quan') != -1:
            continue
        # 此处我偷懒了，发现fanyi和shangxi都是以i结尾并且只出现一次
        # 然后又发现其实放在两个列表里面无所谓
        if each.replace('i', 'iquan') in poem_shangxi_id_list:
            poem_shangxi_id_list.remove(each)
    poem_translate_list = []
    poem_reference_string = "参考资料\n"
    poem_translate_string = ""
    for each in poem_translate_id_list:
        poem_translate_div = main3_div.find('div', id=each)
        translate_part = poem_translate_div.find('div', class_='contyishang')
        caokao_part = poem_translate_div.find('div', class_='cankao')
        translate_context_list = translate_part.find_all('p')
        for context in translate_context_list:
            for subcontext in context.contents:
                if isinstance(subcontext, Tag):
                    if subcontext.name == 'strong':
                        if poem_translate_string != '':
                            poem_translate_list.append(poem_translate_string)
                        poem_translate_string = subcontext.text.strip() + '\n'
                        continue
                    if subcontext.name == 'br':
                        poem_translate_string += '\n'
                elif isinstance(subcontext, NavigableString) and subcontext.text.strip().find('注释') != -1:
                    if poem_translate_string != '':
                        poem_translate_list.append(poem_translate_string)
                    poem_translate_string = subcontext.text.strip() + '\n'
                    continue
                elif isinstance(subcontext, NavigableString):
                    poem_translate_string += subcontext.strip()
        if poem_translate_string != '':
            poem_translate_list.append(poem_translate_string)
        for context in caokao_part:
            if isinstance(context, Tag) and context.name == 'div':
                for subcontext in context.contents:
                    if isinstance(subcontext, Tag) and subcontext.name == 'span':
                        poem_reference_string += subcontext.text
                poem_reference_string += '\n'

    # 赏析部分的解析，赏析可能有多段，按照shangxi<id>的id字段区分
    # 因此使用的是列表，例如：春江花月夜存在三个赏析段
    poem_appreciation_list = []
    for each in poem_shangxi_id_list:
        poem_appreciation_string = ""
        poem_appreciation_div = main3_div.find('div', id=each)
        appreciation_part = poem_appreciation_div.find('div', class_='contyishang')
        shangxi_context_list = appreciation_part.find_all('p')
        for context in shangxi_context_list:
            if isinstance(context, Tag) and context.name == 'p':
                poem_appreciation_string += ''.join(context.text.split()).strip() + '\n'
        poem_appreciation_list.append(poem_appreciation_string)
    # 作品背景的提取
    poem_background_info = '创作背景\n'
    poem_background_info_div = main3_div.find('h2')
    while poem_background_info_div.text.find('创作背景') == -1:
        poem_background_info_div = poem_background_info_div.find_next('h2')
    poem_background_info_div = poem_background_info_div.find_parent()
    poem_background_info_div = poem_background_info_div.find_parent()
    # print(poem_background_info_div)
    for each in poem_background_info_div.contents:
        if isinstance(each, Tag) and each.name == 'p':
            poem_background_info += ''.join(each.text.split()).strip() + '\n'

    # 作者生平简介的提取
    poem_author_info = '作者简介\n'
    poem_author_info_div = main3_div.find('div', class_='sonspic')
    for each in poem_author_info_div.find('div', class_='cont').contents:
        if isinstance(each, Tag) and each.name == 'p':
            for context in each.contents:
                if isinstance(context, NavigableString):
                    poem_author_info += ''.join(context.text.split()).strip()
    # 返回的Python字典对象和格式化的JSON字符串
    result_dict = {
        'title': poem_title,
        'author': {'name': poem_author, 'brief_info': poem_author_info},
        'background': poem_background_info,
        'content': poem_content,
        'translate': poem_translate_list[0],
        'reference': poem_reference_string,
        'keyword': poem_translate_list[1],
        'appreciation': poem_appreciation_list,
        'famous': famous_sentence,
    }
    result_str = str(
        json.dumps(result_dict, indent=4, ensure_ascii=False, sort_keys=True)
    )
    print(result_str)
    return result_dict, result_str


def main():
    global CHROME_DRIVER_PATH
    home_html = requests.request("GET", url="https://www.gushiwen.cn/").text

    # 使用示例HTML
    # f = open("../sample/home_html.html", "r")
    # home_html = f.read()

    CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")

    soup = bs4.BeautifulSoup(home_html, 'html.parser')
    famous_sentence = soup.find('div', class_="jucount").text.strip()
    poem_title_div = soup.find('div', class_="sourceimg")
    poem_html_link = poem_title_div.find('a').get('href')

    while poem_html_link.find('shiwenv') == -1:
        famous_sentence = ""
        poem_title_div = poem_title_div.find_next('a')
        poem_html_link = poem_title_div.get('href')

    # A solution from https://github.com/jsoma/selenium-github-actions
    chrome_service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    chrome_options = Options()
    options = [
        "--headless",
        "--disable-gpu",
        "--window-size=1920,1200",
        "--ignore-certificate-errors",
        "--disable-extensions",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]
    for option in options:
        chrome_options.add_argument(option)
    client = webdriver.Chrome(service=chrome_service, options=chrome_options)

    client.get(poem_html_link)
    btn = client.find_elements(selenium.webdriver.common.by.By.LINK_TEXT, "展开阅读全文 ∨")
    for x in btn:
        # 直接使用click函数会导致弹出登录框，下一次点击失效，于是直接运行超链接
        client.execute_script(x.get_attribute('href'))
    poem_html = client.page_source
    client.quit()

    # 使用示例HTML
    # f = open("../sample/poem_html.html", "r")
    # poem_html = f.read()

    res_dict, res_str = parse_poem_html(poem_html, famous_sentence)
    f = open(f"../poem/{res_dict['title']}.json", "w")
    f.write(res_str)
    f.close()

    tgbot_sent_channel(res_dict, res_str)


if __name__ == '__main__':
    main()
