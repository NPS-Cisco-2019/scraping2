import scrapy
import json
import re
import tldextract
import urllib.request
import os
import json
import datetime
import requests


class QuotesSpider(scrapy.Spider):
    name = "spider"

    def __init__(self, question=None, *args, **kwargs):
        super(QuotesSpider, self).__init__(*args, **kwargs)
        self.question = question
        self.isAnswerThere = True

        self.log(self.question)
        self.answer = {"answer": [], "domain": [], "success": []}

    def start_requests(self):

        q = self.question
        self.urls = self.return_links(q)["link"][:5]
        self.log("[LINKS GOT IN START_REQUESTS]")
        self.log(str(self.urls))
        self.isAnswerThere = bool(self.urls)
        if self.isAnswerThere:
            for url in self.urls:
                listt = tldextract.extract(url)
                website = listt.domain
                if website == 'brainly':
                    yield scrapy.Request(url=url, callback=self.parsebrainly)
                elif website == 'askiitians':
                    yield scrapy.Request(url=url, callback=self.parseaskiitians)
                elif website == 'doubtnut':
                    yield scrapy.Request(url=url, callback=self.parsedoubtnut)
                elif website == 'stackexchange':
                    yield scrapy.Request(url=url, callback=self.parsestackexchange)

        else:
            self.writetheanswer(False)

    def return_links(self, user_query):
        self.log("RETURN LINKS CALL")
        self.link_to_be_parsed = {}
        self.user_query = user_query

        google_search = "https://www.google.com/search?q=" + self.user_query
        self.rq = requests.get(google_search).text

        self.urls = re.findall(r'href=[\'"]?([^\'" >]+)', self.rq)
        self.useful_domains = ["doubtnut", "brainly",
                               "askiitians", "topperlearning", "stackexchange"]

        self.default_username = "bob"
        self.current_time = datetime.datetime.now().time()

        self.link_to_be_parsed["username"] = self.default_username
        self.link_to_be_parsed["current_time"] = str(self.current_time)
        self.link_to_be_parsed["link"] = []
        self.link_to_be_parsed["domain"] = []

        for url in self.urls:
            # string format url based on how google's internal system works
            self.urlx = url[7:url.find(';') - 4]

            if tldextract.extract(self.urlx).domain in self.useful_domains:
                self.link_to_be_parsed["link"].append(str(self.urlx))
                self.link_to_be_parsed["domain"].append(
                    str(tldextract.extract(self.urlx).domain))
        self.log(str(self.link_to_be_parsed))

        return self.link_to_be_parsed

    def parsebrainly(self, response):
    
        ans = response.xpath(
            "//div[@class='sg-text js-answer-content brn-rich-content']").extract()

        imgsrc = response.xpath(
            "//section[@id='answers']//img[@title='Attachment']/@src").getall()
        
        ans = self.janitor(ans)
        self.log("[ANSWER]"+ str(ans))
        self.answer["domain"].append("brainly")
        self.answer["success"] = 1
        if imgsrc:
            self.answer["answer"].append([*ans, imgsrc])
        else:
            self.answer["answer"].append([*ans, 0])
        self.writetheanswer(True)

        # self.writetheanswer(False)

            # self.log(self.answer)

        """ def downloadImage(self,urll, urllname):
            
            urllib.request.urlretrieve(self.urll, self.urllname) """

    def parseaskiitians(self, response):
        try:
            self.log("WWW>ASKIITIANS.COM STARTED")
            l = response.xpath(
                '//*[@id="rptAnswers_ctl01_pnlAnswer"]').extract()
            l = self.janitor(l)

            img = response.xpath(
                '//div[@id="rptAnswers_ctl01_pnlAnswer"]//img/@src').extract()

            self.answer["domain"].append("askiitans")
            self.answer["success"] = 1
            if img:
                self.answer["answer"].append([*l, img])
            else:
                self.answer["answer"].append([*l, 0])

            self.writetheanswer(True)
        except:
            self.writetheanswer(False)
    

    def parsestackexchange(self, response):
        try:
            answer = response.xpath("//div[@class='post-text']/p/text()").extract()
            links = self.convertLinks(response.xpath(
                "//div[@class='post-text']//a/@href").extract())
            for i in range(len(answer)):
                answer[i] = answer[i].replace("$$", "$")

                # print(f"\n\n\n\n[LINKS] {links}\n\n\n\n")

            self.answer["answer"].append([*answer, *links, 0])
            self.answer["domain"].append("Stack Exchange")
            self.answer["success"] = 1
            # with open("ans.txt", "w") as f:
            #     for dom in self.answer["domain"]:
            #         if dom == "Stack Exchange":

            self.writetheanswer(True)
        except:
            self.writetheanswer(False)

    def parsedoubtnut(self, response):
        try:
            self.log("D FOR DOUBTNUT")

            htmls = str(response.text)
            i_ans_text = htmls.find("Answer Text")

            htmls = htmls[i_ans_text:]

            p_indexes = [m.start() for m in re.finditer('</p>', htmls)][2]
            half_almost_answer = htmls[:p_indexes]
            ind_almost_answer = half_almost_answer[::-1].find('>')
            answer = half_almost_answer[-ind_almost_answer:]
            answer = self.janitor(answer)
            self.answer["success"] = 1

            self.answer["domain"].append("doubtnut")
            self.answer["answer"].append([*answer, 0])
            self.writetheanswer(True)
        except:
            self.writetheanswer(False)

    def janitor(self, html_list):
    # try:
        if type(html_list) != list:
            html_list = [html_list]

        ans_list = []

        for raw_html in html_list:
            split_str = '##SPLIT##'
            # self.log("[TYPE]" + str(type(raw_html)))

            # self.log(str(raw_html))

            # cleanr = re.compile('<.*?>')
            # self.log("[]")
            # self.log("[UNCLEANED TEXT]")
            # self.log(str(cleanr))
            cleantext = re.sub('<br/?>', split_str, raw_html)
            cleantext = re.sub('&lt;br&gt;', split_str, cleantext)
            cleantext = re.sub('<p.*?>', split_str, cleantext)
            cleantext = re.sub('&gt;', '>', cleantext)
            cleantext = re.sub('<.*?>', ' ', cleantext)
            cleantext = re.sub('\\\\xa0', ' ', cleantext)
            

            cleantext = re.sub('\\\\[A-Za-z]', ' ', cleantext)
            cleantext = re.sub("\\n", split_str, cleantext)

            self.log("[DATA]")
            
            cleantext = str(cleantext).rstrip(" []'")
            cleantext = str(cleantext).lstrip("[] '")
            i = 0
            while i < len(cleantext) -1 :
                if cleantext[i] == '$' and cleantext[i+1] != "$"  :
                    cleantext = cleantext[:i] + "$$" + cleantext[i+1:]
                    i+=2
                    self.log("[WORKS]")
                i+=1

            i = 0
            spaceFound = False
            while i < len(cleantext):

                if cleantext[i] == " " and spaceFound == False:
                    temp = i
                    spaceFound = True
                if cleantext[i] != " " and spaceFound == True:
                    spaceFound = False
                    cleantext = cleantext[:temp] + " " + cleantext[i:]
                i += 1
            

           
            l = cleantext.split(split_str)
            self.log("[CLEANED TEXT]")
            self.log(str(l))
            # l = [*l, cl]ean
            i = 0
            
            while i < len(l) :
                if l[i] == ' ' or l[i] == '' :
                    l.pop(i)
                i += 1

            ans_list+=l

        return ans_list
        

    def convertLinks(self, links):
        newLinks = []
        for link in links:
            newLinks.append("link"+link)
        return newLinks

    # def unicode_to_mathjax(self, string):
    #     for i in range(len(string)):
    #         if string[i]

    def writetheanswer(self, works):
        if works:
            a = open("ans.txt", "a+")
            a.close()
            with open("ans.txt", "w") as f:
                f.write(str(self.answer))
        else:
            self.answer = {"answer": ['Couldn\'t fetch answer, please try again'], "domain": ['Error'], "success": 0}
            a = open("ans.txt", "a+")
            a.close()
            with open("ans.txt", "w") as f:
                f.write(str(self.answer))