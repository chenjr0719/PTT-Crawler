##########################################################################################################
#Read and set parameters.
import argparse, sys
parser = argparse.ArgumentParser()

parser.add_argument("board", help="Set the board you want to crawling.")
parser.add_argument("num", type = int, help="Set the number of index you want to crawling.")

parser.add_argument("-d", "--dep", help="Install dependency module. Default is no.")
parser.add_argument("-p", "--push", help="Collect pushes or not. Default is yes.")
parser.add_argument("-s", "--stream", help="If yes, this crawler will turn to streaming mode.")

args = parser.parse_args()

board = str(args.board)
index_num = int(args.num)

if args.dep == 'yes':
    import subprocess
    dep = ['requests', 'BeautifulSoup4']
    subprocess.call([sys.executable, '-m', 'pip', 'install'] + dep)
elif not (args.dep == 'no' or args.dep == None):
    print('--dep is not correct!\nPlease input yes or no.')    
    sys.exit()

if args.push == 'yes' or args.push == None:
    push = True
elif args.push == 'no':
    push = None
else:
    print('--push is not correct!\nPlease input yes or no.')
    sys.exit()

if args.stream == 'yes':
    stream = True
elif args.stream == 'no' or args.stream == None:
    stream = None
else:
    print('--stream is not correct!\nPlease input yes or no.')
    sys.exit()

##########################################################################################################
#Import modules.

import requests
from bs4 import BeautifulSoup
import html.parser
import re
import json

import os
import datetime
import time

##########################################################################################################
#Get article links list from specific board.

site_URL = 'https://www.ptt.cc'
site_head = '/bbs/'
site_foot = '/index.html'

#Create a directory to restore the result.
result_dir = 'Result/'
if not os.path.exists(result_dir):
    os.makedirs(result_dir)
os.chdir(result_dir)

link_file = open(board + '_article_links','w')

#For each index, parse it and get every article link. This will save as a text file.
for index in range(0, index_num):
    target = requests.get(site_URL + site_head + board + site_foot, cookies={'over18': '1'}, verify=True)
    soup = BeautifulSoup(target.text.encode("utf-8"), "html.parser")
    link_list = soup.find_all('div',{'class': 'title'})

    for article_link in link_list:
        if article_link.a is not None:
            link = str(article_link.a.get('href'))
            if link:
                link_file.write(site_URL + link + '\n')

    #Find the link of next index if index_num > 1.
    if index > 0:
        next_index = soup.find_all('a',{'class':'btn wide'}, {'href': True})[1]
        next_index = str(next_index.get('href'))
        site_foot = '/index' + re.search(r"[0-9]+", next_index).group() + '.html'
        if not stream:
            print(site_foot)

    time.sleep(0.1)

link_file.close()

##########################################################################################################
#Catch each article.

#Read article link list which restored previously in the text file.
link_file = open(board + '_article_links','r')

#Create a directory to restore the result.
if not os.path.exists(board):
    os.makedirs(board)

os.chdir(board)

#For each article, parse it and separate into meta, content, and pushes.
for link in link_file:

    target = requests.get(link[0:-1], cookies={'over18': '1'}, verify=True)
    soup = BeautifulSoup(target.text.encode("utf-8"), "html.parser")

    article_id = link.split('/')[len(link.split('/')) - 1][:-6]
    if not stream:
        print(article_id)
    if not os.path.exists(article_id):
        os.makedirs(article_id)

    os.chdir(article_id)

    article_meta = soup.find_all('span', {'class': 'article-meta-tag'})

    if not article_meta:
        os.chdir('..')
        continue

    author = None
    title = None
    publish_time = None

    for meta_tag in article_meta:
        author = meta_tag.next_sibling.string if meta_tag.string == '作者' else author
        title = meta_tag.next_sibling.string if meta_tag.string == '標題' else title
        publish_time = meta_tag.next_sibling.string if meta_tag.string == '時間' else publish_time

    #If meta doesn't exist, this article may not have any content.
    if author is None and title is None and publish_time is None:
        os.chdir('..')
        continue

    content_list = meta_tag.next_sibling.next_element.next_elements
    content = ''

    for line in content_list:
        if line.name is None and line.string is not None:
            if line.string[-4:] == '\n--\n':
                content = content + line.string
                break
            else:
                content = content + line.string

    #print(title + '\n' + article_id + '\n' + author + '\n' + publish_time + '\n\n' + content + '\n\n')

    push_position = soup.find_all('span', {'class': 'f2'})
    push_position = push_position[len(push_position) - 1]

    if push:
        push_list = push_position.find_all_next('div', {'class': 'push'})
    else:
        push_list = []

    push_count = 0
    bad_count = 0
    arrow_count = 0

    push_id = 1

    for push in push_list:
        if push is not None and push.find_all('span'):
            push_data = push.find_all('span')

            push_tag = push_data[0].string
            if push_tag[:-1] == u'推':
                push_count += 1
            elif push_tag[:-1] == u'噓':
                bad_count += 1
            else:
                arrow_count += 1

            push_user = push_data[1].string
            push_time = push_data[3].string
            push_content = push_data[2]

            if push_content.find('a') is None:
                push_content = push_content.string[2:]
            else:
                push_content = push_content.a.get('href')

            #print(push_tag + '\n' + push_user + '\n' + push_content + '\n' + push_time + '\n\n')

            push = {
                'Tag': push_tag,
                'User': push_user,
                'Time': push_time,
                'Content': push_content,
                'ID': article_id + '_' + str(push_id)
            }

            push_file = open('Push' + str(push_id) + '.json', 'w')
            push_file.write(json.dumps(push, indent=4, sort_keys=True, ensure_ascii=False))
            push_file.close()

            if stream:
                print(json.dumps(push))

            push_id += 1

    #print('推: ' + str(push_count) + '\n噓: ' + str(bad_count) + '\n→: ' + str(arrow_count))

    article = {
        'Board': board,
        'Article_Title': title,
        'Article_ID': article_id,
        'Author': author,
        'Time': publish_time,
        'Push_num': push_count,
        'Bad_num': bad_count,
        'Arrow_num': arrow_count,
        'Content': content
    }

    article_file = open(article_id + '.json', 'w')
    article_file.write(json.dumps(article, indent=4, sort_keys=True, ensure_ascii=False))
    article_file.close()

    if stream:
        print(json.dumps(article))

    os.chdir('..')
    time.sleep(0.1)

link_file.close()
