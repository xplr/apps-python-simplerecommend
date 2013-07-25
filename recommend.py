#!/usr/bin/python
"""
Index and recommand contents based on XPLR topics

This application permits the following operations :
- Indexing : From an url list, get XPLR prediction on the resources located at these
urls, and indexes the topics returned using the whoosh indexing engine.
- Recomend : From an url, performs a XPLR topics prediction, then search in the indexed
documents the more relevants for the topics predicted.

Usage: recommend.py [options] 

Options:
  -h, --help            show this help message and exit
  -i, --index           Perform topics indexation
  -r URL, --recommend=URL
                        Get recommendation on url
  -d INDEXDIR, --indexdir=INDEXDIR
                        whoosh index directory

  Indexing Options:
    These options are needed for indexing (-i).

    -s SOURCEFILE, --source=SOURCEFILE
                        Source list of URLs to index
    -f, --flush         Flush index before indexing

  XPLR access Options:
    -K APIKEY, --key=APIKEY
                        XPLR API key
    -H APIHOST, --host=APIHOST
                        XPLR API host
    -P APIPORT, --port=APIPORT
                        XPLR API port
    -S, --ssl           use ssl on XPLR calls


Licence :
Copyright (c) 2012 Xplr Software Inc

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
import urllib2
import httplib
import json
import math
import os
import shutil
from optparse import OptionParser,OptionGroup

from whoosh.fields import *
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

INDEX_DIR='/tmp/reco_index'


# define the whoosh schema for topics indexation

schema=Schema(uri=ID(stored=True),     # url of the document
              title=TEXT(stored=True), # unused since not returned by XPLR
              topics_list=KEYWORD(stored=True),     # keyword list of topics
              topics_ids=KEYWORD(stored=True),      # list of topics ids
              topics_scores=KEYWORD(stored=True),   # list of topics score
              )

class PredictFailed(Exception):
    """ Raised when prediction failed for some reason
    """
    pass

def flush():
    """Empty the whoosh index
    """
    try:
        shutil.rmtree(INDEX_DIR)
    except:
        pass

def index(sourcefile):
    """Reads the sourcefile, on every line, calls xplr to
    get prediction on the url, and indexes the url with topics

    :param sourcefile: name of the file containing urls to index, 1 per line
    """
    # creates the index directory if it does not exist
    if not os.path.exists(INDEX_DIR):
        os.mkdir(INDEX_DIR)
    # open the index
    ix = create_in(INDEX_DIR, schema)
    writer = ix.writer()
    try:
        # read links to index
        with open(sourcefile,'r') as s:
            for url in s.readlines():
                url=url.strip()
                print "indexing",url
                try:
                    title, topics = get_prediction(url, topics_count=5)
                    add_document(writer, url, title, topics)
                except PredictFailed, e:
                    print "Prediction Failed:",e
    finally:
        writer.commit()

def get_prediction(url,topics_count=10):
    """ Send an url to xplr and gets the result of the prediction
    as labelled topics, extracted content and words)

    :param url: the url to be predicted
    :param topics_count: number of topics expected
    :returns: a tuple (title, topics) where title is extracted
    by XPLR, and topics a list of tuples (label, id, score)
    """
    # prepare the json to be posted to xplr
    data = '''{"parameters":{
                     "labels":true,
                     "words":true,
                     "topics_limit":%d,
                     "qualifiers":true,
                     "filters_in": ["content_extraction"],
                     "filters_out": ["content","title"]
                  },
                  "document":{"uri":"%s"}}
            '''%(topics_count,url)
            
    # Create an urllib2 Request object
    if XPLR_SSL:
        xplrurl='https://%s/predict'%(XPLR_HOST,)
    else:
        xplrurl='http://%s/predict'%(XPLR_HOST,)
    req = urllib2.Request(xplrurl, data)
    
    # Add api key to the HTTP header
    req.add_header('XPLR-Api-Key',XPLR_API_KEY)
    
    # Make the request
    try:
        response = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        raise PredictFailed, e
    except httplib.BadStatusLine, e:
        raise PredictFailed, e

    # read the response
    jsonresponse=response.read()
    
    # parses the json returned by xplr
    try:
        j = json.loads(jsonresponse)
    except UnicodeDecodeError:
        raise PredictFailed, "Wrong Encoding"

    # check the status code
    if j['status']['code']==200:
        topics=[]
        # get topics
        for topic in j['body']['topics']:
            # get topic label, uuid and score
            topics.append((topic['labels'][0]['label'],topic['uuid'],topic['score']))
     
        # get title
        title = j['body']['extracted_title']

        return title,topics
    else:
        raise PredictFailed, j['status']['code']
    
def add_document(writer, uri, title, topics):
    """ adds a document to the whoosh index
    :param writer: whoosh index writer
    :param uri: uri of the document
    :param title: title of the document
    :param topics: list of tuples (label, uuid, score)
    """
    idxtopics_list = [t[0] for t in topics]
    idxtopics_ids = [t[1] for t in topics]
    idxtopics_scores = [str(t[2]) for t in topics]
    writer.add_document(uri = unicode(uri.decode('utf-8')),
                        title = title,
                        topics_list = idxtopics_list,
                        topics_ids = idxtopics_ids,
                        topics_scores = idxtopics_scores,
                        )

def idsearch(q):
    """ iterator : perform a search on topics uuids (keyword)
    :param q: query performed on topics uuids
    :returns: for each result a tuple with indexed fields and matched topics index
    """
    ix = open_dir(INDEX_DIR)
    queryparser=QueryParser("topics_ids", ix.schema)
    with ix.searcher() as searcher:
        query = queryparser.parse(q)
        results = searcher.search(query,terms=True,limit=None)
        for result in results:
            matched_topics_indexes=[result.get('topics_ids').index(i[1]) for i in result.matched_terms()]
            yield (result.get('uri'),
                   result.get('title'),
                   result.get('topics_list'),
                   result.get('topics_scores'),
                   result.get('topics_ids'),
                   matched_topics_indexes,
                   )

def recommend(url):
    """ recomend a list of indexed document based on topics prediction on the url
    1. Submit the url to XPLR for topics prediction
    2. Searches the predicted topics uuids in the index
    3. Scores the results using XPLR per document topics scores
    displays the list of recommended urls with scores
    :param url: adress of the document source for the recommendation
    """
    # get topics prediction on the url
    ptitle, ptopics  = get_prediction(url, topics_count=5)
    # calculate norm of the source document and build a dict with id_topic:weight
    pnorm=0
    ptw={}
    topics_ids = []
    for pt in ptopics: 
        # pt is a  tuple(label, uuid, score)
        pnorm += pow(pt[2],2)
        ptw.update({pt[1]:pt[2]})
        topics_ids.append(pt[1])

    pnorm=math.sqrt(pnorm)

    result=[]
    # make a search on predicted topics
    for r in idsearch(u" OR ".join(topics_ids)):
        cart=0.0
        norm=0

        # calculate the cartesian product of found topics scores with predicted topics scores
        for ti in r[5]:
            tw = float(r[3][ti])
            tid= r[4][ti]
            cart += tw * ptw[tid]
            norm += pow(tw,2)
        norm=math.sqrt(norm)

        # calculate the score
        score=cart/(norm*pnorm)
        
        # appends (score, url, title) in result
        result.append((score,r[0],r[1]))

    # sort result with calculated scores
    result.sort(reverse=True)
    return result

        
if __name__ == '__main__':
    usage = "usage: %prog [options] "
    parser = OptionParser(usage)

    parser.add_option("-i", "--index", dest="doindex",
                      action="store_true", default=False,
                      help="Perform topics indexation")
    parser.add_option("-r", "--recommend", dest="url",
                      help="Get recommendation on url")

    parser.add_option("-d", "--indexdir", dest="indexdir",
                      help="whoosh index directory")

    group = OptionGroup(parser, "Indexing Options",
                        "These options are needed for indexing (-i).")

    group.add_option("-s", "--source", dest="sourcefile",
                      help="Source list of URLs to index")
    group.add_option("-f", "--flush", dest="doflush",
                      action="store_true", default=False,
                      help="Flush index before indexing")
    parser.add_option_group(group)

    group = OptionGroup(parser, "XPLR access Options")
    group.add_option("-K", "--key", dest="apikey",
                      help="XPLR API key")
    group.add_option("-H", "--host", dest="apihost",
                      help="XPLR API host")
    group.add_option("-P", "--port", dest="apiport",
                      help="XPLR API port")
    group.add_option("-S", "--ssl", dest="apissl",
                      action="store_true", default=False,
                      help="use ssl on XPLR calls")
    parser.add_option_group(group)


    (options, args) = parser.parse_args()

    if not(options.doindex or options.url):        
        parser.error('index or recommend option required')

    if not options.apikey:
        parser.error('XPLR API key required')
    XPLR_API_KEY=options.apikey
    if not options.apihost:
        parser.error('XPLR host required')
    XPLR_HOST=options.apihost
    XPLR_SSL=options.apissl
    if options.apiport:
        XPLR_HOST+=":"+options.apiport


    if options.doindex:
        if not options.sourcefile:
            parser.error('source file required')
        if options.doflush:
            flush()
        index(options.sourcefile)

    if options.url:
        for r in recommend(options.url):
            print "%f"%r[0], r[1]
