# Nansen Legacy label printing

Author: [paalge](https://github.com/paalge) (Pål Ellingsen), [lhmarsden](https://github.com/lhmarsden/) (Luke Marsden)(\
README updated: 2023-07-13 by Luke Marsden

This repository contains the flask application for label printing developed as a part of the
Nansen Legacy project.

## Setup and Installation

This application was developed with Python version 3.8.10.

```
git clone <repo-url>

pip install -r requirements.txt
```
The application can be run using WSGI (flaskapp.wsgi) and has been developed using apache2.

Please add the IP addresses of your printer in the config.json file.
