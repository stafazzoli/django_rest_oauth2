## A Journey into the Realm of OAuth2 with Django REST Framework

The OAuth 2.0 authorization framework enables a third-party application to obtain limited access to an HTTP service. OAuth 2.0 APIs can be used for both authentication and authorization. 
In this note, I want to review and document how to set up OAuth2 for a Django REST project. Using OAuth2 for JSON-based API can be challenging.  

### Register Your Application with the OAuth Provider 
Google:
- Create a project in [Google API Console](https://console.developers.google.com/) 
- Create "OAuth client ID" to obtain OAuth 2.0 credentials
    - Choose the "Web application" type and give it a name
    - Add authorized redirect URI(s)<sup>*</sup> such as `http://localhost:8000/complete/google-oauth2/`
- Google generates client ID and client secret for your app as a client to gain access to Google's APIs

<sup>*</sup> The redirect URI is where Google sends responses to your authentication requests.

Facebook:
- Create an app/ product in the [Facebook platform for developers](https://developers.facebook.com/apps/)
- Go to Settings | Basic
    - Set the App Domains to the valid domain(s) such as localhost (not 127.0.0.1)
    - Add a website as a platform and set the site URL to `http://localhost:8000/`
- Facebook generates app ID and app secret for your app as a client to gain access to FB's APIs   

### OAuth 2.0 Flow 
1. The user goes to your web-server/ application to login and is presented with a "Login with Google" button.
2. The user clicks on the button which has a link similar to the following:
    ```
    http://api.google.com/oauth/v2/auth
    ?client_id=CLIENT_ID
    &redirect_uri=https://mywebsite.com/signinwithgoogle
    &scope=email,profile
    &response_type=code  
    ```
    - client_id: you get client_id when you register the application with the OAuth provider
    - response_type=code: 'code' is one of the most common response types
    - redirect_uri: URI that you configure with the OAuth provider which is an approved location for redirecting back to.
    - scope: it contains the information you want to request access to.

3. A consent form with a callback-URL is displayed to the user that describes the information that the user is releasing (e.g., email address) and the terms that apply. The consent screen also contains your branding information like product name, logo, etc.
4. If the user is already logged in and already confirmed the particular application and scope, the OAuth provider will not show any confirmation page but will redirect immediately back with the approval information.
5. If the user has not done so already, the OAuth provider presents a question like "Do you want to login to this site..." type of information and asks for user confirmation.
6. The user either confirms or denies the auth request.
7. If the user denies the request, the OAuth provider will redirect them back to the redirect URI provided in the request (redirect_uri).
    ```
    http://mysite.com/comeBack.cgi
       ?error=access_denied
    ```
8. If the user confirms the request, the OAuth provider redirects the user back to your web-server with a `code` using the callback URL provided.
9. Web-server calls the OAuth provider directly and exchange `code` for an `access token` to validate the `code`.
    ```
    POST https://www.googleapis.com/oauth2/v4/token
    ?code=CODE
    &client_id=CLIENT_ID
    &client_secret=CLIENT_SECRET
    &redirect_uri=REDIRECT_URL      # not sure if this is optional
    &grant_type=authorization_code
    ```
10. If the response is successful, the OAuth provider returns an `access token` and an `id token`.
The ID Token is a JWT (JSON Web Token) that contains identity information about the user that is digitally signed by the OAuth provider.
    ```json
    {
      "access_token": ACCESS_TOKEN, 
      "id_token": ID_TOKEN, 
      "expires_in": 3599, 
      "token_type": "Bearer", 
      "scope": "https://www.googleapis.com/auth/userinfo.email openid https://www.googleapis.com/auth/userinfo.profile", 
      "refresh_token": REFRESH_TOKEN
    }
    ```
11. After getting user information from the ID token, `views.py` checks if the user exists based on the email address. It saves the new user and updates the info of the existing user.
12. Then, you should start an application session for that user if all login requirements are met by the API response.

### Installations
I assume that a Django REST project is already set up. Now, we need to install the following modules:
```shell script
pip install django-rest-framework-social-oauth2
pip install djangorestframework-jwt
pip install python-decouple

python manage.py makemigrations
python manage.py migrate
```

### Django Back-end
- Make the following changes to the `setting.py` file:
```python
INSTALLED_APPS = (
    ...
    'rest_framework',
    'oauth2_provider',
    'social_django',
)
```
```python
MIDDLEWARE = [
    ...
    'social_django.middleware.SocialAuthExceptionMiddleware',
]
```
```python
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]
```
```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
}
```
```python
# SOCIAL AUTH
from decouple import config
AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

for key in ['FACEBOOK_KEY',
            'FACEBOOK_SECRET',
            'GOOGLE_OAUTH2_KEY',
            'GOOGLE_OAUTH2_SECRET']:
    exec("SOCIAL_AUTH_{key} = config('{key}', '')".format(key=key))

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
FACEBOOK_EXTENDED_PERMISSIONS = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id, name, email'}

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username', 'first_name', 'email']
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)
```
- Create a .env file that contains the values for the for FACEBOOK_KEY, FACEBOOK_SECRET, GOOGLE_OAUTH2_KEY, and GOOGLE_OAUTH2_SECRET that you got when you registered the app with OAuth provider.
- Include the `serializers.py`, `views.py`, and `urls.py` in your project. You can find them in the `accounts` app under the `api` folder.

### Test the API
To test the backend using Postman, you can get an `access token` for the test from the OAuth provider. 
Then, you can call the following API by providing the parameters in the request body. The `access token` will expire and you cannot use it in your code.
```http://127.0.0.1:8000/api/accounts/oauth/login/```

Google:
- In [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/):
    - Step 1: I used Google+ APIs for email and profile info. Click on 'Authorize APIs' and then, confirm the consent form. It will return an `Authorization code` which is the `code` that is supposed to return using the callback URL. 
    - Step 2: Click on 'Exchange authorization code for token'. It will return an `access token` that you can use to call the API using the back-end.
```json
{
"provider":"google-oauth2",
"access_token":"YOUR_ACCESS_TOKEN"
}
```

Facebook:
- You can use `User Token` from [this link](https://developers.facebook.com/tools/accesstoken) as an `access token`.
```json
{
"provider":"facebook",
"access_token":"YOUR_ACCESS_TOKEN"
}
```

### References
- https://www.toptal.com/django/integrate-oauth-2-into-django-drf-back-end
- https://medium.com/@katherinekimetto/simple-facebook-social-login-using-django-rest-framework-e2ac10266be1
- https://developers.google.com/identity/protocols/oauth2/openid-connect?hl=en
- https://256stuff.com/gray/docs/oauth2.0/
