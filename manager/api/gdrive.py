import google_auth_oauthlib
from aiohttp import web
from aiohttp_session import get_session

from manager.api.links import get_client_id_file, SCOPES


async def authorize(request):
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        get_client_id_file(), scopes=SCOPES)

    flow.redirect_uri = request.scheme + '://' + request.host + \
                        str(request.app.router['oauth2callback'].url_for())

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session = await get_session(request)
    session['state'] = state

    return web.HTTPFound(authorization_url)


async def oauth2callback(request):
    session = await get_session(request)

    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = session.get('state')

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        get_client_id_file(), scopes=SCOPES, state=state)
    flow.redirect_uri = request.scheme + '://' + request.host + \
                        str(request.app.router['oauth2callback'].url_for())

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = str(request.url)

    flow.fetch_token(authorization_response=authorization_response)
    # flow.fetch_token(code=request.query.get('code'))

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    # return web.json_response(data=session['credentials'])

    raise web.HTTPFound(request.app.router['main'].url_for())


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}
