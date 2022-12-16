# fcrepo-searcher

Python 3 Flask application to search Fcrepo/Archelon; provides a backend searcher to a Bento Box style search
which expects a REST interface following the Quick Search model.

## Requires

* Python 3

### Running in Docker

```bash
$ docker build -t fcrepo-searcher .
$ docker run -it --rm -p 5000:5000 --env-file=.env --read-only fcrepo-searcher
```

### Building for Kubernetes

```bash
$ docker buildx build . --builder=kube -t docker.lib.umd.edu/fcrepo-searcher:VERSION --push
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
curl http://localhost:5000/search'?q=jim+henson+works'
{
  "endpoint": "fcrepo-search",
  "module_link": "https://digital.lib.umd.edu/searchnew?query=jim+henson+works",
  "no_results_link": "https://digital.lib.umd.edu/searchnew",
  "page": "0",
  "per_page": "3",
  "query": "jim henson works",
  "results": [
    {
      "description": "",
      "extra": {
        "collection": "UMD Student Newspapers",
        "htmlSnippet": "Mike Wesley Junior Journalism “I feel that “black-on-black” crime diminishes our culture. We <b>worked</b> hard in the past to build a"
      },
      "item_format": "Page",
      "link": "https://digital.lib.umd.edu/result/id/9f48657c-f2af-4349-b8bd-4fccab2b821c",
      "title": "Black explosion (College Park, Md.), 2001-03-15, page 13"
    },
    {
      "description": "",
      "extra": {
        "collection": "UMD Student Newspapers",
        "htmlSnippet": " percentage of minorities at UMCP is not yet equal to the percentage of non-minority students, this ranking shows that UMCP is <b>working</b> towards"
      },
      "item_format": "Page",
      "link": "https://digital.lib.umd.edu/result/id/8c01f5b1-5bee-4d2e-8e3d-2e50829d9d5d",
      "title": "Black explosion (College Park, Md.), 2001-03-15, page 7"
    },
    {
      "description": "",
      "extra": {
        "collection": "UMD Student Newspapers",
        "htmlSnippet": "STAFF MEMBERS <b>Jim</b> Adkins, A1 Perrin and Bob Wilson labor to bring forth a new issue of “The Log.” Brainchild of Alwyn...newspapers for writers, artists, and any others interested in <b>work ing</b> on a newly forming maga zine. No pay was offered but when... articles but <b>Jim</b> Adkins, also a cartoonist for the Dia mondback, is head of the art sec tion and Bob Wilson, a sophomore in... not do any administra tive <b>work.</b>"
      },
      "item_format": "Page",
      "link": "https://digital.lib.umd.edu/result/id/b9cfb5ec-17da-4d27-9097-b5bedcb7c3e8",
      "title": "The diamondback (College Park, Md.), 1967-04-05, page 8"
    }
  ],
  "total": 80571
}
```

[Flask's debug mode]: https://flask.palletsprojects.com/en/2.2.x/cli/?highlight=debug%20mode

## License

See the [LICENSE](LICENSE.txt) file for license rights and limitations.
