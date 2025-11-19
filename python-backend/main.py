from requests_oauthlib import OAuth2Session
import webbrowser
import os


# PKCE_VERIFIER = '4c3u50352b3o4q4i1k346x6i6u1z4d3h1f1h393y5n0b5p100l0q4x2z0x0g5p5n5j186w2x2r6713431a5i334b3a5i0e6p6v665k6a465h3l6n53092t1u2d3p450o'
# PKCE_CHALLENGE = 'diwLHpWHIIulyYMfAOoejxO7RU8tiTpOM3zj2aOx5oI'
# STATE = '6p1f5t125h6p3h4g321w6g1w244a5146'

# Replace with your Fitbit app details
CLIENT_ID = "23TQ87"
CLIENT_SECRET = "e078adef7ed4942af5950ae6bf829cbb"   # Required unless using PKCE
REDIRECT_URI = "http://localhost"     # e.g., http://localhost:8080/

AUTH_BASE_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"

# Scopes determine what data you can read
SCOPES = ["activity", "cardio_fitness", "location", "heartrate", "sleep", "profile"]

# Create OAuth2 session
fitbit = OAuth2Session(
    CLIENT_ID,
    redirect_uri=REDIRECT_URI,
    scope=SCOPES,
)

# Redirect the user to Fitbit login
authorization_url, state = fitbit.authorization_url(AUTH_BASE_URL)
print("Open this URL in your browser to authorize:")
print(authorization_url)

# Auto-open browser
webbrowser.open(authorization_url)

# User pastes the full redirect URL back here
redirect_response = input("Paste the full redirect URL here: ")

# Fetch access token
token = fitbit.fetch_token(
    TOKEN_URL,
    client_secret=CLIENT_SECRET,
    authorization_response=redirect_response,
)

print("Access Token:")
print(token)
