Troubleshooting
==================

I can't access my repository and/or I'm getting 403 errors.
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Look for the ``Accessing as <user>`` in your logs at the first point you're connecting to DagsHub.

If it's not the user you expect, you might have an old token in your cache. We recommend clearing out the cache with :func:`.clear_token_cache`.

If the user is correct and you're in an organization, ask the administrator of your organization to make sure you have access to the repo.


