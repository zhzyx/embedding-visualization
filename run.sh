#! /bin/bash
# if you are going to use an url to access, add the option follow with 
# your url. E.g.
# --allow-websocket-origin your.domain.com[:port]
nohup bokeh serve --show embedding_visualization --port 8890 > ./app_log.log 2>&1 &