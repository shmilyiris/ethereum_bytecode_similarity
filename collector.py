import requests
from bs4 import BeautifulSoup
import os
import csv
import time


def printtime():
    print(time.strftime("%Y-%m-%d %H:%M:%S:", time.localtime()), end=' ')
    return 0


def getsccodecore(address):

    sol_path = './dataset_/sol/' + address + '.sol'
    info_path = './dataset_/addr2info.csv'

    if (os.path.exists(sol_path)):
        printtime()
        print(sol_path + ' already exists！')
        return 0

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'
    }
    proxies = {
        'http': 'http://127.0.0.1:7890',
        'https': 'http://127.0.0.1:7890'
    }

    failedTimes = 100
    while True:

        if (failedTimes <= 0):
            printtime()
            print("TOO many failed times, check your internet conditions!")
            break

        failedTimes -= 1
        try:
            printtime()
            url = 'https://etherscan.io/address/' + address + '#code'
            print('crawling.. ' + url)
            response = requests.get(url, headers=headers, timeout=5, proxies=proxies)
            break

        except requests.exceptions.ConnectionError:
            printtime()
            print('ConnectionError！Wait for 3 seconds!')
            time.sleep(3)

        except requests.exceptions.ChunkedEncodingError:
            printtime()
            print('ConnectionError！Wait for 3 seconds!')
            time.sleep(3)

        except:
            printtime()
            print('Unfortunately, unknown failures！Wait for 3 seconds！')
            time.sleep(3)

    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")
    # js-sourcecopyarea editor ace_editor ace-dawn
    targetPRE = soup.find_all('pre', 'js-sourcecopyarea editor')
    # h6 fw-bold mb-0
    targetINFO = soup.find_all('span', 'h6 fw-bold mb-0')

    fo = open(sol_path, "w+", encoding="utf-8")
    for eachpre in targetPRE:
        fo.write(eachpre.text)
    fo.close()
    printtime()
    print(sol_path + ' success！')

    if len(targetINFO) > 0:
        with open(info_path, 'a+', encoding='utf_8_sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([address, targetINFO[0].text, targetINFO[1].text])

    return 0


def get_addresses():
    addrs = os.listdir('./dataset/sol/')
    for i in range(len(addrs)):
        addrs[i] = addrs[i][:-4]
    return addrs


if __name__ == '__main__':
    address_list = get_addresses()
    for addr in address_list:
        getsccodecore(addr)
