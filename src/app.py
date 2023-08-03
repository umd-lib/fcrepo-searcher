import json
import logging
import os
import json
import urllib.parse
import requests
import re

import furl
from flask import Flask, request
from dotenv import load_dotenv
from waitress import serve
from paste.translogger import TransLogger

# Searcher for Fedora Content Repository / Archelon

# Add any environment variables from .env
load_dotenv('../.env')

# Get environment variables
env = {}
for key in ('FCREPO_SOLR_URL', 'FCREPO_SOLR_FILTER_QUERY', 
            'FCREPO_LINK', 'FCREPO_NO_RESULTS_LINK', 'FCREPO_MODULE_LINK'):
    env[key] = os.environ.get(key)
    if env[key] is None:
        raise RuntimeError(f'Must provide environment variable: {key}')

solr_url = furl.furl(env['FCREPO_SOLR_URL'])
search_url = solr_url / 'select'
search_fq = env['FCREPO_SOLR_FILTER_QUERY']
link = env['FCREPO_LINK']
no_results_link = env['FCREPO_NO_RESULTS_LINK']
module_link = env['FCREPO_MODULE_LINK']

debug = os.environ.get('FLASK_DEBUG')

logging.root.addHandler(logging.StreamHandler())

loggerWaitress = logging.getLogger('waitress')
logger = logging.getLogger('fcrepo-searcher')

if debug:
    loggerWaitress.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)

else:
    loggerWaitress.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)

logger.info("Starting the fcrepo-searcher Flask application")

endpoint = 'fcrepo-search'


# Start the flask app, with compression enabled
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/')
def root():
    return {'status': 'ok'}


@app.route('/ping')
def ping():
    return {'status': 'ok'}


def getSnippet(query, item):
    """ Get hit highlight for a single item. """

    id = item['id']
    snippet = ''

    # Execute the search for the highligh on the Annotation
    params = {
        'q': query,
        'rows ': '100',
        'wt ': 'json',
        'version ': '2',
        'fl ': 'id,extracted_text,extracted_text_source',
        'fq ': ['rdf_type:oa\:Annotation',
                'extracted_text_source:(' + id.replace(':', '\\:') + ')'],
        'hl': 'true',
        'hl.fragsize ': '500',
        'hl.fl ': 'extracted_text',
        'hl.simple.pre ': '<b>',
        'hl.simple.post ': '</b>',
    }

    try:
        response = requests.get(search_url.url, params=params)
    except Exception as err:
        logger.error(f'Error submitting search url={search_url.url}, params={params}\n{err}')

        return snippet

    if response.status_code != 200:
        logger.error(f'Received {response.status_code} when submitted {query=}')

        return snippet

    logger.debug(f'Submitted url={search_url.url}, params={params}')
    logger.debug(f'Received response {response.status_code}')
    logger.debug(response.text)

    data = json.loads(response.text)
    logger.debug(data)

    # Iterate over the results
    for aid, h in data['highlighting'].items():
        if 'extracted_text' in h:
            for t in h['extracted_text']:
                if len(snippet) > 0:
                    snippet += "..."

                # Remove end of line character
                t = t.replace('\n', ' ')

                # Remove annotation bounding box information
                t = re.sub(r'\|\d+,\d+,\d+,\d+', '', t)

                snippet += t

    return snippet

def strip_query(query):
    escaped_query = query.translate(str.maketrans({":": "",
                                                  "(": "",
                                                  ")": "",
                                                  "{": "",
                                                  "}": "",
                                                  "]": "",
                                                  "+": "",
                                                  "*": "",
                                                  "%": "",
                                                  "[": ""}))
    escaped_query = escaped_query.strip()
    return escaped_query


@app.route('/search')
def search():

    # Get the request parameters
    args = request.args
    if 'q' not in args or args['q'] == "":
        return {
            'endpoint': endpoint,
            'error': {
                'msg': 'q parameter is required',
            },
        }, 400
    query = args['q']

    per_page = 3
    if 'per_page' in args and args['per_page'] != "":
        per_page = args['per_page']

    page = 0
    if 'page' in args and args['page'] != "" and args['page'] != "%":
        page = args['page']

    start = int(page) * int(per_page)
    rows = per_page

    quotes_pattern = r'"([^"]*)"'

    escaped_query = query
    if re.search(quotes_pattern, query) is None:
        escaped_query = strip_query(escaped_query)

    if escaped_query is None or len(escaped_query) == 0:
        return {
            'endpoint': endpoint,
            'error': {
                'msg': 'Invalid query parameters',
            },
        }, 400

    completed_query = '(text:((' + escaped_query + '))^2 ' + ' text_ja:((' + escaped_query + '))^1 ' + ' text_ja_latn:((' + escaped_query + '))^1)'
    # base_query = '_query_:{!type=graph from=id to=extracted_text_source maxDepth=1 q.op=AND}' + strip_query(query).replace("\"", "\\\"") + ' ' + completed_query
    base_query = '_query_:{!type=graph from=id to=extracted_text_source maxDepth=1 q.op=AND}' + strip_query(query).replace("\"", "") + ' ' + completed_query

    # Execute the search
    params = {
        'df': 'text',
        'TZ': 'UTC',
        'fl': 'containing_issue,extracted_text_source,collection,id,component_not_tokenized,page_number,display_title,date,collection_title_facet,score,hash,annotation_source_type:[subquery],files:[subquery]',
        'f.collection_title_facet.facet.missing': 'false',
        'issue_title.q': '{!terms f=id v=$row.containing_issue}',
        'annotation_source_type.q': '{!terms f=id v=$row.annotation_source}',
        'q.op': 'OR',
        'facet.missing': 'false',
        'fq': search_fq, # filter query
        'issue_title.fl': 'display_title',
        'annotation_source_title.fl': 'id,display_title',
        'files.fq': 'mime_type:application/pdf',
        'f.date_decade.facet.missing': 'false',
        'wt': 'json', # get JSON format results
        'annotation_source_type.fl': 'id,component',
        'issue_title.rows': '1',
        'files.fl': 'id,title,filename,mime_type',
        'sort': 'score desc',
        'q': base_query,
        'rows': rows,  # number of results
        'start': start,  # starting at this result (0 is the first result)
        'version': '2',
    }

    try:
        response = requests.get(search_url.url, params=params)
    except Exception as err:
        logger.error(f'Error submitting search url={search_url.url}, params={params}\n{err}')

        return {
            'endpoint': endpoint,
            'error': {
                'msg': f'Error submitting search',
            },
        }, 500

    if response.status_code != 200:
        logger.error(f'Received {response.status_code} when submitted {query=}')

        return {
            'endpoint': endpoint,
            'error': {
                'msg': f'Received {response.status_code} when submitted {query=}',
            },
        }, 500

    logger.debug(f'Submitted url={search_url.url}, params={params}')
    logger.debug(f'Received response {response.status_code}')
    logger.debug(response.text)

    data = json.loads(response.text)

    # Gather the search results into our response
    results = []
    response = {
        'endpoint': endpoint,
        'query': query,
        "per_page": str(per_page),
        "page": str(page),
        "total": int(data['response']['numFound']),
        "module_link": module_link.replace('{query}',
                                           urllib.parse.quote_plus(query)),
        "no_results_link": no_results_link,
        "results": results
    }

    if 'docs' in data['response']:
        for item in data['response']['docs']:
            id = str(furl.furl(item['id']).path).split('/')[-1]

            collection_id = None
            if len(item['collection']) > 0:
                collection = item['collection'][0]
                colid_parsed = urllib.parse.urlsplit(collection)
                if colid_parsed.path.find('pcdm/') == -1:
                    collection_id = colid_parsed.path.replace('/fcrepo/rest/', 'relpath=')

            if 'component_not_tokenized' in item:
                item_format = item['component_not_tokenized']

            issue_id = None
            if 'containing_issue' in item:
                issue_id = str(furl.furl(item['containing_issue']).path).split('/')[-1]

            item_link = None
            if item_format == 'Article' and issue_id is not None:
                item_link = link.replace('{id}', urllib.parse.quote_plus(issue_id))
            else:
                item_link = link.replace('{id}', urllib.parse.quote_plus(id))

            htmlSnippet = getSnippet(completed_query, item)

            safe_query = None
            if query is not None:
                safe_query = 'query=' + urllib.parse.quote_plus(escaped_query)

            if safe_query is not None or collection_id is not None:
                item_link += '?'
                if safe_query is not None:
                    item_link += safe_query
                    if collection_id is not None:
                        item_link += '&'
                if collection_id is not None:
                    item_link += collection_id


            results.append({
                'title': item['display_title'],
                'link': item_link,
                'description': item['description'] if 'description' in item else htmlSnippet,
                'item_format': item['component_not_tokenized'],
                'extra': {
                    'collection': item['collection_title_facet'][0],
                    'htmlSnippet': htmlSnippet,
                },
            })

    return response


if __name__ == '__main__':
    # This code is not reached when running "flask run". However the Docker
    # container runs "python app.py" and host='0.0.0.0' is set to ensure
    # that flask listens on port 5000 on all interfaces.

    # Run waitress WSGI server
    serve(TransLogger(app, setup_console_handler=True),
          host='0.0.0.0', port=5000, threads=10)
