# fcrepo-searcher

Python 3 Flask application to search Fcrepo/Archelon; provides a backend searcher to a Bento Box style search
which expects a REST interface following the Quick Search model.

## Requires

* Python 3

## Running the Webapp

```bash
# create a .env file (then manually update environment variables)
$ cp .env-template .env
```

### Running locally

```bash
# install requirements
$ pip install -r requirements.txt

# run the app with Flask
$ flask run
```

### Running in Docker

```bash
$ docker build -t fcrepo-searcher .
$ docker run -it --rm -p 5000:5000 --env-file=.env --read-only fcrepo-searcher
```

### Endpoints

This will start the webapp listening on the default port 5000 on localhost
(127.0.0.1), and running in [Flask's debug mode].

Root endpoint (just returns `{status: ok}` to all requests):
<http://localhost:5000/>

/ping endpoint (just returns `{status: ok}` to all requests):
<http://localhost:5000/ping>

/search endpoint: `http://localhost:5000/search?q={query}&page={page number?}&per_page={results per page?}`

Example:

```bash
curl 'http://localhost:5000/search?q=henson&per_page=3&page=0'

```

[Flask's debug mode]: https://flask.palletsprojects.com/en/2.0.x/quickstart/#debug-mode

## License

See the [LICENSE](LICENSE.txt) file for license rights and limitations.
