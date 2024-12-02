import re
import sys
import mmh3
import codecs
import hashlib
import urllib3
import requests
from bs4 import BeautifulSoup
from colorama import init, Fore
from urllib.parse import urlparse, urljoin, urlunparse
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


headers = {
	'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
}


def is_absolute(url):
	return bool(urlparse(url).netloc)


def check_default(url):
	parsed_url = urlparse(url)
	favicon_url = urlunparse((parsed_url.scheme, parsed_url.netloc, 'favicon.ico', '', '', ''))
	fr = requests.head(favicon_url, headers=headers, allow_redirects=True, verify=False)
	if fr.status_code == 200:
		icons.add(favicon_url)


def collect_icons(url):
	r = requests.get(url, headers=headers, allow_redirects=True, verify=False)
	soup = BeautifulSoup(r.text, features='html.parser')

	links = soup.find_all('link', {'rel': re.compile("icon*"), 'href': True})
	metas = soup.find_all('meta', {'property': re.compile("image*"), 'content': True})

	for link in links:
		href = link.get('href')
		if is_absolute(href):
			icons.add(href)
		else:
			href = urljoin(r.url, href)
			icons.add(href)

	for meta in metas:
		content = meta.get('content')
		if is_absolute(content):
			icons.add(content)
		else:
			content = urljoin(r.url, content)
			icons.add(content)


def calculate_hash():
	mmh3s = set()
	md5s = set()
	for icon in icons:
		ri = requests.get(icon, verify=False)
		bri = codecs.encode(ri.content,"base64")
		mmh3_hash = mmh3.hash(bri)
		# print(icon, mmh3_hash)
		mmh3s.add(str(mmh3_hash))
		md5s.add(hashlib.md5(ri.content).hexdigest())
	return mmh3s, md5s


def shodan_generator(hashes):
	print(Fore.RED + "[Shodan] " + Fore.RESET, end="")
	shodan_url = "https://www.shodan.io/search?query=http.favicon.hash%3A{}".format(','.join(hashes))
	print(shodan_url)


def censys_generator(hashes):
	print(Fore.RED + "[Censys] " + Fore.RESET, end="")
	censys_url = "https://search.censys.io/search?resource=hosts&q=services.http.response.favicons.md5_hash%3A%7B{}%7D".format(','.join(hashes))
	print(censys_url)


def zoomeye_generator(hashes):
	print(Fore.RED + "[Zoomeye] " + Fore.RESET, end="")
	zoomeye_url = "https://www.zoomeye.hk/searchResult?q={}".format('%20'.join(["iconhash%3A%22"+h+"%22" for h in hashes]))
	print(zoomeye_url)


try:
	url = sys.argv[1]
except:
	print("Usage: python {} URL".format(sys.argv[0]))
	sys.exit(0)


init(strip=False)
icons = set()
check_default(url)
collect_icons(url)
mmh3s, md5s = calculate_hash()
shodan_generator(mmh3s)
censys_generator(md5s)
zoomeye_generator(mmh3s)
