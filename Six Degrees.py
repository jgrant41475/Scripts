from html.parser import HTMLParser
from urllib.request import urlopen

page = "https://en.wikipedia.org/wiki/Star_Trek:_Discovery"

class SixDegrees(HTMLParser):
    SINGLE_TAGS = ["area", "base", "br", "col", "embed", "frame", "hr", "i", "img",
                   "input", "link", "meta", "param", "source", "track", "wbr"]

    def __init__(self, url):
        super().__init__()

        self.url = url
        self.identifier = ["class", "mw-parser-output"]
    
    def fetch(self):
        with urlopen(self.url) as response:
            resp = response.read().decode("UTF-8")
            self.container = ""
            self.log = False
            self.counter = 0

            self.feed(resp)

            if self.container:
                print(self.container)
    
    def handle_starttag(self, tag: str, attributes: list) -> None:
        self.log = any(any(i.lower() == self.identifier[1].lower() for i in val.split(" "))
                        for key, val in attributes
                        if self.identifier[0].lower() == key.lower())

        if self.log:
            print("{} :: {}".format(self.log, self.counter))
            if tag not in self.SINGLE_TAGS:
                self.counter += 1
                form = '<{}>'

            else:
                form = '<{}/>'

            self.container += form.format(" ".join([tag, *['{}="{}"'.format(k, v) for k, v in attributes]]))

    def handle_data(self, data: str) -> None:
        if self.log:
            self.container += data.strip()

    def handle_endtag(self, tag: str) -> None:
        if self.log:
            if tag not in self.SINGLE_TAGS:
                self.container += "</{}>".format(tag)
                self.counter -= 1

            self.log = self.counter > 0

    def error(self, message: str) -> None:
        print("HTMLParserError: {}".format(message))

if __name__ == "__main__":
    print("hello")
    SixDegrees(page).fetch()
    print("Good Bye")
