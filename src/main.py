import os

import bs4
import selenium.webdriver.common.by
from selenium import webdriver

CHROME_DRIVER_PATH = ""


def parse_poem_html(poem_html: str) -> dict:
    result_dict = {}
    soup = bs4.BeautifulSoup(poem_html, 'html.parser')
    poem_title = soup.find('h1').text
    print("poem_title: ", poem_title)
    poem_author = soup.find('p', class_='source').text
    print('poem_author: ', poem_author)
    poem_context_pre = soup.find('div', class_='contson')
    poem_context = ""
    for each in poem_context_pre.contents:
        if isinstance(each, bs4.element.Tag) and each.name == 'br':
            poem_context += '\n'
        else:
            poem_context += each.text.strip()
    print('poem_context: ', poem_context)
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
    poem_shangxi_list = []
    for each in poem_translate_id_list:
        poem_translate_string = ""
        poem_translate_div = main3_div.find('div', id=each)
        translate_part = poem_translate_div.find('div', class_='contyishang')
        translate_context_list = translate_part.find_all('p')
        for context in translate_context_list:
            for subcontext in context.contents:
                if isinstance(subcontext, bs4.element.Tag):
                    if subcontext.name == 'strong':
                        if poem_translate_string != "":
                            poem_translate_list.append(poem_translate_string)
                        poem_translate_string = subcontext.text.strip() + '\n'
                        continue
                    if subcontext.name == 'br':
                        poem_translate_string += '\n'
                if isinstance(subcontext, bs4.element.NavigableString):
                    poem_translate_string += subcontext.strip()
        if poem_translate_string != "":
            poem_translate_list.append(poem_translate_string)
        print("poem_translate_string: ", poem_translate_list)
    return result_dict


def main():
    # home_html = requests.request("GET", url="https://www.gushiwen.cn/").text
    global CHROME_DRIVER_PATH
    f = open("../sample/home_html.html", "r")
    CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")
    home_html = f.read()
    soup = bs4.BeautifulSoup(home_html, 'html.parser')
    famous_sentence = soup.find('div', class_="jucount")
    print(famous_sentence.text)
    poem_title_div = soup.find('div', class_="sourceimg")
    poem_html_link = poem_title_div.find('a').get('href')

    # chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-gpu')
    # chrome_options.add_argument('--no-sandbox')  # 这个配置很重要
    #
    # client = webdriver.Chrome(options=chrome_options,executable_path=CHROME_DRIVER_PATH)
    # client.get(poem_html_link)
    # btn = client.find_elements(selenium.webdriver.common.by.By.LINK_TEXT, "展开阅读全文 ∨")
    # for x in btn:
    #     x.click()
    # poem_html = client.page_source
    # client.quit()
    f = open("../sample/poem_html.html", "r")
    poem_html = f.read()
    parse_poem_html(poem_html)


if __name__ == '__main__':
    main()
