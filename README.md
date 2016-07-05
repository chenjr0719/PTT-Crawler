# PTT-Crawler

A Python Crawler Implement for PTT

## What is PTT?

**PTT** is the biggest BBS site in Taiwan.

It is also a good place to gather information, which means: I can collect information and take analysis like Text Mining, Topic models, and others.


## Requirement

**PTT-Crawler** is build by **Python 3** and using BeautifulSoup4, requests, html.parser to gather post from PTT, then it will restore those posts into JSON files.

Make sure you already have **BeautifulSoup4**, **requests**, or you can use pip to instal them.
```s
pip install requests
pip install BeautifulSoup4
```


## How to Use?

You need to determine which board and how many index page you want to gather.

So, modify parameters named **board** and **index_num** to do this.

Then, run the command in terminal:

```s
python PTT_Crawler.py
```


## Output Data Format

In .json file, article looks like:

```s
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
```

And push is:

```s
push = {
  'Tag': push_tag,
  'User': push_user,
  'Time': push_time,
  'Content': push_content,
  'ID': article_id + '_' + str(push_id)
}
```
