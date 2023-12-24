Authentication
================

In order to interact with most DagsHub features you need to authenticate using a user token.

**For basic every day use cases no specific setup is required**,
the client will prompt you to authenticate via OAuth if there were no valid tokens found.
The functions on this page are only relevant for advanced use cases and/or CI environments.


Using a long lived app token
++++++++++++++++++++++++++++++

You can generate a long lived app token with no expiry date
from your `User Settings <https://dagshub.com/user/settings/tokens>`_.

After generating it, you can make the client use it by doing any of the following:

- Setting the ``DAGSHUB_USER_TOKEN`` environment variable to the value of the token.
- Using a CLI command ``dagshub login --token <token>``. This will store the token in the token cache.
- Calling the :func:`.add_app_token` function. This will store the token in the token cache.

.. autofunction:: dagshub.auth.add_app_token

.. note::
    App tokens are always prioritized over OAuth tokens when using :func:`.get_token` and :func:`.get_authenticator`.

Getting a token for use in other places
++++++++++++++++++++++++++++++++++++++++

.. autofunction:: dagshub.auth.get_token

.. autofunction:: dagshub.auth.get_authenticator

Triggering the OAuth flow explicitly
+++++++++++++++++++++++++++++++++++++

.. autofunction:: dagshub.auth.add_oauth_token

You can also trigger the OAuth flow by doing ``dagshub login`` in CLI.

Connecting to a hosted DagsHub instance
++++++++++++++++++++++++++++++++++++++++++++++

If you are a self-serve customer of DagsHub, set ``DAGSHUB_CLIENT_HOST`` environment variable
to the url of the DagsHub deployment. All client functions will automatically connect to the hosted instance.

