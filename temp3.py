import requests
import re

def get_quote(stock):
    url = "https://www.google.com/search?q=bvmf:"+stock
    info = []
    with requests.Session() as s:
        try:
            content = str(s.get(url).content)
            name_start = content.find('<div class="ZINbbc xpd O9g5cc uUPGi"><div class="kCrYT"><span><span class="BNeawe tAd8D AP7Wnd">')+96
            name_end = content.find('</span></span><span class="BNeawe s3v9rd AP7Wnd"> /')
            print(content, name_end, name_start)
            if name_end - name_start > 60:
                return "ERROR_01"
            info.append(content[name_start:name_end])
            stock_quotation = re.findall('\d\d*,\d\d <', content)
            info.append(stock_quotation[0][:-2])

        except Exception as e:
            print(e)
            return "ERROR_02"
        return info

print(get_quote("sapr11"))