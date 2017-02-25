import argparse
import sys
import requests
from bs4 import BeautifulSoup
import html.parser
import re
import json
import os
import datetime
import time
from multiprocessing import Pool


#Get article links list from specific board.
def getArticleLinks(board, index_num):

    board_url = 'https://www.ptt.cc/bbs/' + board + '/index.html'

    board_dir = board + '/'
    if not os.path.exists(board_dir):
        os.makedirs(board_dir)

    link_list_file = open(board_dir + board + '_article_links','w')
    result = []

    #For each index, parse it and get every article link. This will save as a text file.
    for index in range(0, index_num):
        target = requests.get(board_url, cookies={'over18': '1'}, verify=True)
        soup = BeautifulSoup(target.text.encode("utf-8"), "html.parser")
        link_list = soup.find_all('div',{'class': 'title'})

        for article_link in link_list:
            if article_link.a is not None:
                link = str(article_link.a.get('href'))
                if link:
                    link_list_file.write('https://www.ptt.cc' + link + '\n')
                    result.append('https://www.ptt.cc' + link)

        #Find the link of next index if index_num > 1.
        if index > 0:
            next_index = soup.find_all('a',{'class':'btn wide'}, {'href': True})[1]
            next_index = str(next_index.get('href'))
            next_index = re.search(r"[0-9]+", next_index).group()
            board_url = 'https://www.ptt.cc/bbs/' + board + '/index' + next_index + '.html'

        time.sleep(0.1)

    link_list_file.close()

    return result


#Crawl each article.
#For each article, parse it and separate into meta, content, and pushes.
def getArticle(article_link):

    get_push = main.get_push
    board = main.board

    target = requests.get(article_link, cookies={'over18': '1'}, verify=True)
    soup = BeautifulSoup(target.text.encode("utf-8"), "html.parser")

    article_id = article_link.split('/')[len(article_link.split('/')) - 1][:-6]

    article_path = board + '/' + article_id
    if not os.path.exists(article_path):
        os.makedirs(article_path)

    article_meta = soup.find_all('span', {'class': 'article-meta-tag'})

    if not article_meta:
        return None

    author = None
    title = None
    publish_time = None

    for meta_tag in article_meta:
        author = meta_tag.next_sibling.string if meta_tag.string == '作者' else author
        title = meta_tag.next_sibling.string if meta_tag.string == '標題' else title
        publish_time = meta_tag.next_sibling.string if meta_tag.string == '時間' else publish_time

    #If meta doesn't exist, this article may not have any content.
    if author is None and title is None and publish_time is None:
        return None

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

    if get_push:
        push_position = soup.find_all('span', {'class': 'f2'})
        push_position = push_position[len(push_position) - 1]
        push_list = push_position.find_all_next('div', {'class': 'push'})
        push_id = 1
    else:
        push_list = []

    push_count = 0
    bad_count = 0
    arrow_count = 0

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

            push_file = open(article_path + '/Push' + str(push_id) + '.json', 'w')
            push_file.write(json.dumps(push, indent=4, sort_keys=True, ensure_ascii=False))
            push_file.close()

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

    article_file = open(article_path + '/' + article_id + '.json', 'w')
    article_file.write(json.dumps(article, indent=4, sort_keys=True, ensure_ascii=False))
    article_file.close()

    time.sleep(0.1)


def main():

    #Read and set parameters.
    parser = argparse.ArgumentParser()

    parser.add_argument("board", help="Set the board you want to crawling. Ex: Gossiping,cat")
    parser.add_argument("num", type = int, help="Set the number of index you want to crawling.")
    parser.add_argument("-p", "--push", help="Collect pushes or not. Default is yes.")

    args = parser.parse_args()

    main.board = str(args.board)
    index_num = int(args.num)

    if args.push == 'yes' or args.push == None:
        main.get_push = True
    elif args.push == 'no':
        main.get_push = None
    else:
        print('--push is not correct!\nPlease input yes or no.')
        sys.exit()

    #Create a directory to restore the result.
    result_dir = 'Result/'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    os.chdir(result_dir)

    print('Start to Crawling...\nPlease be patient.')
    print('Getting article list...')
    link_list = getArticleLinks(main.board, index_num)

    #Get message, comments and reactions from feed.
    print('Crawling article in multi-processing...')
    target_pool = Pool()
    target_pool.map(getArticle, link_list)
    target_pool.close()

    print('Crawling is done.')


if __name__ == "__main__":
    main()
