# barlamane-bot

Source code for [barlabot](https://twitter.com/barlabot) Twitter bot.\
The code is pretty much self-documented. But this repository mainly contains the following scripts:

### questions.py

This script fetches new questions (oral or written, based on the command line) and regularly tweets
new items.
It used to take a screenshot of the question text  and tweet it as an image but I disabled it when I had trouble setting up geckodriver on my rpi0w (see `clip_question_verbatim_screenshot` in utils.py file).

### jarida.py

This program looks for new updates of the BO (Bulletin Officiel) from sgg.gov.ma. It tweets the first page when a new release is published.

### stats.py

This is a fun utility program to perform (and tweet) statistics of questions asked by MPs in the previous weeks or month.

## Getting started

If you want to use this project on your own as-is, make sure you follow the steps below:

* The bot uses the [Twitter API](https://developers.twitter.com/) to publish updates. To use it, you'll need to have a config.py file at the root of the project with the following definitions:

```python
twitter_oauth_consumer_key = ''
twitter_oauth_consumer_secret = ''
twitter_oauth_access_token_key = ''
twitter_oauth_access_token_secret = ''
```

* Install the required Python packages:

```bash
$ pip install -r requirements
``` 

* The code uses some file name defined in config.py to save logs. You'll need to have **at least** the following variables definitions:
    * `jarida_index_file`: This file is used to store the number of the latest BO.
    * `questions_log_file`: Where questions.py logs are sent
    * `jarida_log_file`: Where jardia.py logs are sent

> To get an exhaustive list, you can run this command: `grep -Rn "config\."` 

* `questions.py` relies on a MongoDB collection to read and write question items.\
You'll need to either:
    * Create one yourself. The fields correspond to barlapy's [Question class fields](https://github.com/openbarlamane/barlapy/blob/master/barlapy/question.py#L10).
    * Remove db calls.

* The programs use [barlapy](https://github.com/openbarlamane/barlapy), which is provided as a Git submodule.
When you clone, make sure you add `--recurse-submodules` to be able to use it without any additional action.
Otherwise, you can clone it separately and copy it at the root of this project.

## Contributing

This repository is home for the source code I wrote for a side project I had fun working on.\
Contributions are welcome. If you notice something noteworthy, please open an issue or a pull request and let me take a look at it.
