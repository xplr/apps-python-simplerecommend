Simple Recommender
==================

Recommender based on [XPLR topics API](https://xplr.com/developers/), using the python [whoosh](https://bitbucket.org/mchaput/whoosh/wiki/Home) index and search engine.

[Dedicated page](https://xplr.com/apps/apps-python-simplerecommend)

Browse [all software from XPLR](https://xplr.com/apps).

Description
-----------

This application allows the following operations :

* *Index* a set of documents : From an URL list, get XPLR prediestimate topics from each URL content with XPLR API and indexes the topics returned using the whoosh indexing engine.

* *Recommend* : Takes a URL as input and recommends the most relevant indexed URLs according to the underlying topics, predicted with XPLR API.


Licence 
-------

This application is released under the MIT licence.

> 
> Copyright (c) 2012 Xplr Software Inc
> 
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
> 
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
> 
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
> 

Prerequisites
-------------

- Get an XPLR account and API key on https://www.xplr.com, the API key is to be passed as an argument to the script.

Usage
-----

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

### Examples

Indexing urls contained	in ~/my_url_list into a whoosh index in /tmp/index_dir with XPLR predicted topics:

    python recommend.py  -i -d /tmp/index_dir -s ~/my_url_list -S -K 46eb069e-3d2b-11e2-9eeb-080027752be2 -H api.xplr.com

Getting recommendations for the page located at http://www.usa.gov/topics/science/communications/internet/spam.shtml

    python recommend.py  -d /tmp/index_dir -r "http://www.usa.gov/topics/science/communications/internet/spam.shtml" -S -K 46eb069e-3d2b-11e2-9eeb-080027752be2 -H api.xplr.com






