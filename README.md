# DTCC Core

DTCC Core is the common database and API for the DTCC Platform.

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

## tmux

Split screen vertically: Ctrlb and Shift 5
Split screen horizontally: Ctrlb and Shift "
Toggle between panes: Ctrl b and o
Close current pane: Ctrl b and x


## Run fast api test

- dtcc-docker: 
    - docker-compose up -d rabbitmq
- dtcc-core:
    - python3 -m pip install -r src/requirements.txt
    - python3 src/test_fast_api.py

docs page: 
- http://localhost:8070/docs 
- start
Stream logs:
- http://localhost:8070/task/stream-logs