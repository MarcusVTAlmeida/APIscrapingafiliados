import requests
from bs4 import BeautifulSoup
import re

l=[]
o={}
specs_arr=[]
specs_obj={}

target_url="https://www.amazon.com.br/Geonav-Carregador-Universal-Carregamento-PB20K20WSG/dp/B0CNHBV6W5/?_encoding=UTF8&ref_=pd_hp_d_atf_ci_mcx_mr_ca_hp_atf_d"

headers={"accept-language": "en-US,en;q=0.9","accept-encoding": "gzip, deflate, br","User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36","accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}

resp = requests.get(target_url, headers=headers)
print(resp.status_code)
if(resp.status_code != 200):
    print(resp)
soup=BeautifulSoup(resp.text,'html.parser')


try:
    o["title"]=soup.find('h1',{'id':'title'}).text.lstrip().rstrip()
except:
    o["title"]=None


images = re.findall('"hiRes":"(.+?)"', resp.text)
o["images"]=images

try:
    o["price"]=soup.find("span",{"class":"a-price"}).find("span").text
except:
    o["price"]=None

try:
    o["rating"]=soup.find("i",{"class":"a-icon-star"}).text
except:
    o["rating"]=None


specs = soup.find_all("tr",{"class":"a-spacing-small"})

for u in range(0,len(specs)):
    spanTags = specs[u].find_all("span")
    specs_obj[spanTags[0].text]=spanTags[1].text


specs_arr.append(specs_obj)
o["specs"]=specs_arr
l.append(o)


print(l)


[{'title': 'Apple 2023 MacBook Pro Laptop with Apple M2 Pro chip with 12‑core CPU and 19‑core GPU: 16.2-inch Liquid Retina XDR Display, 16GB Unified Memory, 1TB SSD Storage. Works with iPhone/iPad; Space Gray', 'images': ['https://m.media-amazon.com/images/I/61fd2oCrvyL._AC_SL1500_.jpg', 'https://m.media-amazon.com/images/I/71ZAeHYYlHL._AC_SL1500_.jpg', 'https://m.media-amazon.com/images/I/61C9irOOQVL._AC_SL1500_.jpg', 'https://m.media-amazon.com/images/I/81j1XDaqcML._AC_SL1500_.jpg', 'https://m.media-amazon.com/images/I/81OBjqVEGwL._AC_SL1500_.jpg', 'https://m.media-amazon.com/images/I/61FhAanYdhL._AC_SL1500_.jpg'], 'price': None, 'rating': '', 'specs': [{'Brand': 'Apple', 'Model Name': 'MacBook Pro', 'Screen Size': '16.2 Inches', 'Color': 'Space Gray', 'Hard Disk 
Size': '1 TB', 'CPU Model': 'Unknown', 'Ram Memory Installed Size': '16 GB', 'Operating System': 'Mac OS', 'Special Feature': 'Anti Glare Coating', 'Graphics Card Description': 'Integrated'}]}] 
PS C:\Users\MarcusVinicius\Desktop\Afiliado>