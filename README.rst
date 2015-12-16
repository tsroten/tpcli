.. |---| unicode:: U+2014  .. em dash

==================================
TP - a usable UI for Targetprocess
==================================

    I want to write a poem about "Truth," "Honor," "Dignity," and whether the toilet paper should roll over or under when you pull on it.

    |---| Jarod Kintz

--------------------------------------------------------

Features
========

* No mouse support
* Zero modal windows


Usage
=====

List recent tickets:

.. code-block::

    $ tp ls

       Id  Type       State   Name                                               Owner
    ─────  ─────────  ──────  ─────────────────────────────────────────────────  ──────────
    18928  UserStory  Open    User should be able to log in with GitHub account  John Smith
    18926  Bug        Open    Margin for left sidebar too small in IE 10         Mary Lamb
    18925  Bug        Active  Website shows desktop version on Windows phone     Johnny R.
    [...]

Filter tickets:

.. code-block::

    $ tp ls bug state=active name:user
    
       Id  Type    State    Name                                                  Owner
    ─────  ──────  ───────  ────────────────────────────────────────────────────  ─────────
    18819  Bug     Active   User's profile "Edit" button doesn't show up in IE 9  Jill Ross
    18812  Bug     Active   Mailing address validation throws errors to users     R. Jack
    18810  Bug     Active   Login doesn't work when user reassigned to new org    psmith
    [...]

Show a ticket's details:

.. code-block::

    $ tp show 18819

    User's profile "Edit" button doesn't show up in IE 9
    Bug #18819 by Jill Ross on 2015-12-01 14:45:29
    Active as of 2015-12-05 10:21:35

      When a user navigates to their profile using Internet Explorer 9, the "Edit" button
      is missing from their profile's sidebar.

      It appears to be an issue with the CSS for the parent div.


More Information
================

* GitHub: https://github.com/tsroten/tpcli
* Free software: MIT license
