#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
