from html.parser import HTMLParser
from os import makedirs, error as os_error
from os.path import exists
from pymsgbox import alert, prompt, confirm
from re import findall, search, IGNORECASE
from sre_constants import error as sre_error
from sys import winver
from time import sleep, strftime
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class WebCrawler(HTMLParser):
    """Web Crawler Class
        Crawls websites for links originating from the same host and exports list as text file in current directory.
        Optionally scans pages for content identifiers or archives entire page if no such identifiers are found.

        Arguments
        ---------
        @url : str
            Complete URL to be crawled, must be in format: http://www.example.com/

        @sitemap : str or None
            If there is a sitemap available, this is the relative path from @url.
            Format of sitemap must be XML https://www.sitemaps.org/protocol.html

        @interval : float
            Amount of time in seconds to pause between connections to prevent spamming.  Default = 1 second

        @codec : str
            The character encoding scheme that should be used to decode HTTP responses with, by default this is UTF-8

        @archive : bool
            If this is True then pages visited will be archived to folder in working directory

        @identifier : list of str or None
            If @archive is True then this is what identifies the main content wrapper of the page.  Given the list item
            ["class", "entry-content"] the parser will search for elements with the class attribute entry-content and
            return only that element and its children.  If no identifier is found on the page or if this value evaluates
            to False, the entire page source is saved.

        @robots : bool
            Sets whether the instance of this class should scan /robots.txt, by default this is whatever the class
            attribute @CHECK_ROBOTS is set to.

        Attributes
        ----------
        @ALLOW_ARCHIVING : bool
            If this is true, prompts user for an HTML attribute and value for page archiving.

        @CHECK_ROBOTS : bool
            Default boolean value that determines whether or not to respect /robots.txt rules.  This can be overridden
            by passing the keyword argument robots with a different boolean value.

        @DEFAULT_CODEC : str
            Default codec to decode responses with, will fall back to @FALLBACK in the event of a decoding error.

        @FALLBACK : str
            Retry decoding using this codec.  If this decoding fails skip page.

        @USER_AGENT : dict of str : str
            Converts dictionary into a HTTP header.
            If the default User-Agent is getting blocked, try Mozilla.

        @MAPPING : int
            This is the mode value for generating a sitemap.

        @ARCHIVING : int
            This is the mode value for archiving pages.

        @LOGGING : int
            This is the mode value for writing log backups.

        @MEDIA_TYPES : list of str
            Paths with these extensions will not be checked, but will still be indexed.

        @SINGLE_TAGS : list of str
            List of HTML elements that do not have closing tags.  Used in parsing HTML responses.

        @IGNORED : list of str
            Any paths listed here will not be added to exclusions list when reading robots file.
        """

    ALLOW_ARCHIVING = True
    CHECK_ROBOTS = True

    DEFAULT_CODEC = "UTF-8"
    FALLBACK = "Windows-1252"
    USER_AGENT = {'User-Agent': 'Python-urllib/{}'.format(winver)}  # Default UA
    # USER_AGENT = {'User-Agent': 'Mozilla/5.0'}    # Mozilla UA

    MAPPING = 0
    ARCHIVING = 1
    LOGGING = 2

    MEDIA_TYPES = ["png", "jpg", "jpeg", "mp4", "mp3", "pdf", "gz", "gif"]
    SINGLE_TAGS = ["area", "base", "br", "col", "embed", "frame", "hr", "i", "img",
                   "input", "link", "meta", "param", "source", "track", "wbr"]
    IGNORED = []

    HEADER = {**USER_AGENT, 'Accept': 'text/html;charset={},{}'.format(DEFAULT_CODEC, FALLBACK)}

    def __init__(self, url, sitemap=None, interval=1.0, codec=DEFAULT_CODEC,
                 archive=True, identifier=None, robots=CHECK_ROBOTS) -> None:
        super().__init__()

        if not url:
            raise ValueError("URL Cannot be empty")

        parsed_url = urlparse(url)

        path = parsed_url.path if parsed_url.path else "/"
        if path[-1] != "/":
            path += "/"

        if sitemap and sitemap[0] != "/":
            sitemap = path + sitemap
        elif not sitemap:
            sitemap = None

        self.checked = set()
        self.unchecked = set()
        self.bad = set()
        self.good = set()
        self.disallow = set()
        self.media_links = set()

        self.host = parsed_url.netloc
        self.domain = "{}://{}".format(parsed_url.scheme, self.host)
        self.path = path
        self.format = codec
        self.sitemap = sitemap
        self.interval = interval

        self.robots = robots
        self.archive = archive
        self.identifier = identifier
        self.log = False
        self.counter = 0
        self.container = ""
        self.log_content = ""

    def start(self) -> None:
        """Begin crawling"""

        self._log("Crawling '{}'".format(self.domain + self.path))

        if self.archive:
            if type(self.identifier) is list and len(self.identifier) == 2:
                self._log("Archiving is scanning for element attribute '{}'".format("=".join(self.identifier)))

            else:
                self._log("Archiving entire page.")

        self._log("Press Ctrl+C to abort.\n")

        try:
            if self.robots:
                self._fetch("/robots.txt")

            if self.sitemap:
                self._fetch(self.sitemap)

            self._fetch(self.path)

            self._loop()

        except KeyboardInterrupt:
            self._log("Cancelling...")

        self.good = self.checked.difference(self.bad, self.media_links)
        self._log("Total links found: {}, with {} errors.".
                  format(len(self.checked) + len(self.unchecked), len(self.bad)))

    def write(self, file_name: str, mode: int=MAPPING, data: str or None=None) -> bool:
        """Attempts to write results of site scanning to disk"""

        try:
            if mode == self.MAPPING:
                self._log("Writing to disk...")
                with open(file_name, "w") as file:
                    file.write("Site mapping of {} on {}\n\nTotal Links found: {}\n"
                               .format(self.domain + self.path, strftime("%m/%d/%Y at %I:%M%p"),
                                       str(len(self.checked) + len(self.unchecked))))

                    if self.good:
                        file.write("\nGood ({})\n".format(len(self.good)))
                        [file.write(path + "\n") for path in sorted(self.good)]

                    if self.bad:
                        file.write("\nBad ({})\n".format(len(self.bad)))
                        [file.write(bad_path + "\n") for bad_path in sorted(self.bad)]

                    if self.media_links:
                        file.write("\nMedia Links ({})\n".format(len(self.media_links)))
                        [file.write(media_path + "\n") for media_path in sorted(self.media_links)]

                    if self.unchecked:
                        file.write("\nUnchecked ({})\n".format(len(self.unchecked)))
                        [file.write(unchecked_path + "\n") for unchecked_path in sorted(self.unchecked)
                         if unchecked_path != ""]

            elif mode == self.ARCHIVING:
                if not data:
                    self._log("Error: Cannot archive '{}' because no response was received.".format(file_name))
                    return False

                if not exists(self.host):
                    makedirs(self.host)

                self._log("Archiving: {}".format(file_name))

                with open("{}/{}".format(self.host, file_name.replace("/", "~")), "w", encoding=self.format) as file:
                    self.log = False
                    self.counter = 0
                    self.container = ""

                    if self.identifier:
                        try:
                            self.feed(data)

                        except UnboundLocalError as emsg:
                            self._log("HTMLParserError: {}".format(str(emsg)))
                            self.reset()
                            self.container = None

                        file.write(self.container if self.container and self.counter == 0 else data)
                    else:
                        file.write(data)

            elif mode == self.LOGGING and self.log_content:
                with open(file_name, "w") as file:
                    file.write(self.log_content)

        except PermissionError:
            if mode == self.MAPPING:
                alert("Unable to create file.")

            elif mode == self.ARCHIVING:
                self._log("Unable to create file.  Archiving is now disabled.")
                self.archive = False

            return False

        except FileNotFoundError as msg:
            self._log("Error: {}".format(str(msg)))

            if mode == self.ARCHIVING:
                self._log("Disabling archiving.")
                self.archive = False

            return False

        except os_error as msg:
            self._log("Unknown error: {}".format(str(msg)))

            if mode == self.ARCHIVING:
                self._log("Disabling archiving.")
                self.archive = False

            return False

        return True

    def _loop(self) -> None:
        """Main service loop"""

        while self.unchecked:
            cur = self.unchecked.pop()
            excluded = False

            # Holder for any invalid patterns @TODO: Replace with a better solution
            bad_pattern = set()
            for pattern in self.disallow:
                try:
                    if findall(pattern, cur, flags=IGNORECASE):
                        self._log("Excluding: " + cur)
                        excluded = True

                except sre_error:
                    self._log("Error in parsing regular expression pattern: " + pattern)
                    bad_pattern.add(pattern)

            if bad_pattern:
                self.disallow = self.disallow.difference(bad_pattern)

            # Path is not a text file
            if not excluded and cur.split("/")[-1].split(".")[-1].lower() in self.MEDIA_TYPES:
                self._log("Skipping media link {}".format(cur))
                self.media_links.add(cur)
                self.checked.add(cur)

            # Path is allowed and unvisited
            elif cur != "" and not excluded and cur not in self.checked:
                # Parse the current page for more links
                self._fetch(cur)

                checked = len(self.checked)
                unchecked = len(self.unchecked)
                ratio = (checked / (checked + unchecked)) * 100
                self._log("Indexed: {} | Unvisited: {} | {:.2f}% Complete.".format(checked, unchecked, ratio))

                sleep(self.interval)

    def _fetch(self, path: str or None = None) -> None:
        """Parses @path for links that originate from @self.host"""

        try:
            page = self.domain + path

            self._log("Scanning: '{}'".format(page))
            with urlopen(Request(page, headers=self.HEADER)) as response:
                resp = response.read()

                try:
                    decoded = resp.decode(self.format)

                except UnicodeDecodeError:
                    if self.format.lower() == self.DEFAULT_CODEC.lower():
                        try:
                            self._log("Error decoding {} with '{}'.  Using '{}'."
                                      .format(path, self.format, self.FALLBACK))
                            decoded = resp.decode(self.FALLBACK)
                            self.format = self.FALLBACK

                        except UnicodeDecodeError:
                            self._log("Decoding failed with {}. Skipping...".format(self.format))
                            decoded = None

                    else:
                        self._log("Error decoding with {} codec. Skipping...".format(self.format))
                        decoded = None

                if decoded:
                    if path == "/robots.txt":
                        for ex in findall('disallow: ?(.+)\n?', decoded, flags=IGNORECASE):
                            ex = ex.strip()

                            if ex != "" and ex not in self.disallow and ex not in self.IGNORED:
                                self._log("Robots.txt added {} to exclusions".format(ex))
                                self.disallow.add(ex)

                        for sm in findall('sitemap: ?(.+)\n?', decoded, flags=IGNORECASE):
                            sm = self._parse(sm.strip(), path)

                            if sm != "" and sm not in self.checked:
                                self._log("Robots.txt added sitemap: {}".format(sm))
                                self.unchecked.add(sm)

                    else:
                        if len(path) > 4 and path[-4:].lower() == ".xml":
                            # Matches pages in sitemaps
                            pattern = '<loc>(.+?)</loc>'

                        else:
                            # Pattern matches all anchor tags with an href attribute.
                            # NOTE: href attribute must be defined on the same line as the start of the tag to be found
                            pattern = '<a\s+(?:[^>]*?\s+)?href=[\"\']([^\"\']+)\s*(?:[^>]*?\s+)?'

                        if self.archive is True:
                            self.write(path, self.ARCHIVING, decoded)

                        [self.unchecked.add(self._parse(match, path))
                         for line in decoded.split("\n")
                         for match in findall(pattern, line.strip())]

        except HTTPError as err_msg:
            self._log("Could not reach {} | {}".format(path, str(err_msg)))
            self.bad.add(path)

        except UnicodeEncodeError as emsg:
            self._log("Encoding path failed.  Skipping page... | {}".format(str(emsg)))
            self.bad.add(path)

        finally:
            self.checked.add(path)

            if path in self.unchecked:
                self.unchecked.remove(path)

    def _parse(self, link: str, path: str or None = None) -> str:
        """Converts raw href data into absolute path."""

        # Pattern validates link and removes additional parameters
        # Https://tools.ietf.org/html/rfc3986#page-50
        parsed = search('^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?$', link)
        proto = parsed.group(2)
        parsed_path = parsed.group(5).replace(" ", "%20").replace("]]>", "").strip()

        # If http protocol data was found, checks to make sure that the link originates from the same server
        if proto and 'http' in proto:
            match = "" if parsed.group(4) != self.host else parsed_path

        # If path is in root directory, match page path and discard any additional parameters
        elif parsed_path and parsed_path[0] == "/":
            match = parsed_path if parsed else ""

        elif parsed_path and parsed_path[0] != "/":
            # Convert link from relative position to its absolute path
            parent = "/".join([x for x in path.split("/")[:-1]]) + "/"
            match = parent + parsed_path if parsed_path and ":" not in link and ".." not in parsed_path else ""

        else:
            match = ""

        if match and match[-1] == "/":
            match = match[:-1]

        # Do not return match if link was already found
        return match if match not in self.checked else ""

    def _log(self, msg: str):
        self.log_content += msg + "\n"
        print(msg)

    def handle_starttag(self, tag: str, attributes: list) -> None:
        if self.identifier is not None and len(self.identifier) == 2 and not self.log:
            self.log = any(any(i.lower() == self.identifier[1].lower() for i in val.split(" "))
                           for key, val in attributes
                           if self.identifier[0].lower() == key.lower())

        if self.log:
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
        self._log("HTMLParserError: {}".format(message))


def setup(fail: tuple) -> tuple or None:
    site = prompt("Enter URL to crawl", "WebCrawler", "http://example.com/")
    archive = False
    selector = None

    if not site:
        return fail

    try:
        parsed_site = urlparse(site)
        if 'http' not in parsed_site.scheme:
            alert("Missing http")
            return fail

    except URLError:
        alert("Not a valid URL")
        return fail

    sitemap = prompt("Enter path to sitemap if available", "WebCrawler", "sitemap.xml")
    if type(sitemap) is not str or sitemap == "":
        sitemap = None

    if WebCrawler.ALLOW_ARCHIVING and confirm("Archive pages?", "WebCrawler", ["Yes", "No"]) == "Yes":
        archive = True

        raw_input = prompt("Enter the element attribute and value that identifies the content wrapper separated " +
                           "by '=' or Cancel to import entire page.\nExample: class=entry-content",
                           "WebCrawler", "class=entry-content")

        if raw_input and raw_input.count("=") == 1:
            selector = raw_input.split("=")

        else:
            selector = None
            alert("Invalid identifier, page parsing is disabled.")

    return site, sitemap, archive, selector


def main() -> None:
    (url, sitemap, archive, identifier) = setup((None, None, None, None))

    if url:
        crawler = WebCrawler(url=url, sitemap=sitemap, interval=1.0, archive=archive, identifier=identifier)
        crawler.start()

        if crawler.good:
            filename = 'Sitemap - {}.txt'.format(crawler.host)

            alert("Crawler indexed {} pages, with {} errors.  Exporting list to '{}'".
                  format(len(crawler.checked) + len(crawler.unchecked), len(crawler.bad), filename), "WebCrawler")

            if crawler.write(filename):
                alert("Done.")

            else:
                alert("Unable to write to file.")

            if crawler.log_content:
                crawler.write("{}.log.txt".format(crawler.host), mode=WebCrawler.LOGGING)

        else:
            alert("Nothing found...", "WebCrawler")


if __name__ == '__main__':
    main()
