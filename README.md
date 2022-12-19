# DTCC Core

Common Rest API, PubSub and database handlers for DTCC Platform.

This project is part the
[Digital Twin Platform (DTCC Platform)](https://gitlab.com/dtcc-platform)
developed at the
[Digital Twin Cities Centre](https://dtcc.chalmers.se/)
supported by Sweden’s Innovation Agency Vinnova under Grant No. 2019-421 00041.

## Documentation

* [Introduction](./doc/introduction.md)
* [Installation](./doc/installation.md)
* [Usage](./doc/usage.md)
* [Development](./doc/development.md)

## Authors (in order of appearance)

* [Vasilis Naserentin](https://www.chalmers.se/en/Staff/Pages/vasnas.aspx)
* [Siddhartha Kasaraneni](https://chalmersindustriteknik.se/sv/medarbetare/siddhartha-kasaranemi/)
* [Anders Logg](http://anders.logg.org)
* [Dag Wästerberg](https://chalmersindustriteknik.se/sv/medarbetare/dag-wastberg/)

## License

DTCC Core is licensed under the
[MIT license](https://opensource.org/licenses/MIT).

Copyright is held by the individual authors as listed at the top of
each source file.


## API test

- curl -X POST localhost:8090/tasks/generateTest/start
- curl -X POST localhost:8090/tasks/generateCityModel/start
- curl -X GET localhost:8090/tasks/generateTest/get-result

## Poetry 
- install poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- create venv: `poetry shell`
- activate venv: `source $(poetry env info --path)/bin/activate`
- install libs: `poetry install`