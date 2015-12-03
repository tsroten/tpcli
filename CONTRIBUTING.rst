============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given. 

If you want to contribute, but don't know how, or want some help
getting started, `let me know <https://github.com/tsroten>`_!
I'm happy to lend a hand.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/tsroten/tp/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

TP could always use more documentation, whether as part of the 
official TP docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/tsroten/tp/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `tp` for local development.

1. Fork the `tp` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/tp.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv tp
    $ cd tp/
    $ pip install -r requirements.txt
    $ python setup.py develop

4. Add a git remote that points to TP's upstream repository::

    $ git remote add upstream git@github.com:tsroten/tp.git

5. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature
   
   Now you can make your changes locally. Make sure that you commit often
   so that your commits are descriptive and small. Also, write tests
   for your bugfix/feature.

6. Periodically merge the upstream repository with your's::

    $ git checkout develop
    $ git pull upstream develop
    $ git checkout name-of-your-bugfix-or-feature
    $ git merge develop

7. When you're done making changes, check that your changes pass flake8 and the tests, including testing other Python versions with tox::

    $ flake8 tp
    $ python setup.py test
    $ tox

   If you can't get tox to run through all it's Python versions, that's fine,
   but it is nice if you can run it through one version of Python 2 and one
   version of Python 3.

8. Commit any changes and push your branch to GitHub::

    $ git add .
    $ git commit
    $ git push origin name-of-your-bugfix-or-feature

   Make sure that your commit message has a good description of your changes.

9. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring.
3. The pull request should work for Python 2.7/3.3/3.4/3.5 and for PyPy. Check 
   https://travis-ci.org/tsroten/tp/pull_requests
   and make sure that the tests pass for all supported Python versions.
4. If you want to receive credit, add your name to `AUTHORS.rst`.
