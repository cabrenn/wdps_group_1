# Group 1 - Web Data Processing Systems
[Please describe briefly how your system works, which existing tools you have used and why, and how to run your solution.]

## How to use WDPS application

### Requirements

Python 3+

### Installation and Execution

You have to create virtual environment first:

```bash
    python -m venv venv
    source venv/bin/activate
    python -m pip install -r requirements.txt
    python -m spacy download en_core_web_sm
    deactivate

    pushd venv/
    zip -rq ../venv.zip *
    popd

```

Afterwards just run ```./run_app.sh [INPUT HDFS FILE] [OUTPUT HDFS FILE]``` i.e. ```./run_app.sh /user/wdps1801/sample/warc/gz /user/wdps1801/freebase_ids```
