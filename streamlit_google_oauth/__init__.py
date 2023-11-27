import streamlit as st
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2

__version__ = "0.1"


async def write_authorization_url(client, redirect_uri):
    authorization_url = await client.get_authorization_url(
        redirect_uri,
        scope=["profile", "email"],
        extras_params={"access_type": "offline"},
    )
    return authorization_url


async def write_access_token(client, redirect_uri, code):
    token = await client.get_access_token(code, redirect_uri)
    return token


async def get_user_info(client, token):
    user_id, user_email = await client.get_id_email(token)
    return user_id, user_email


async def revoke_token(client, token):
    return await client.revoke_token(token)


def login_button(authorization_url, app_name, app_desc):
    st.markdown('''<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet"
    integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">''',
    unsafe_allow_html=True)
    st.markdown('<style> a {color: #FFFFFF;text-decoration: none;}</style>', unsafe_allow_html=True)

    container = f'''
    <div class="container-fluid border py-4 px-4 border-primary">
        <h5><strong>{app_name}</strong></h5>
        <p>{app_desc}</p>
        <a target="_self" href="{authorization_url}">
        <svg class="img-fluid" xmlns="https://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 48 48" aria-hidden="true" class="L5wZDc"><path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"></path><path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"></path><path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 17.09 2 20.45 2 24c0 3.55.85 6.91 2.34 9.88l7.35-5.7z"></path><path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"></path><path fill="none" d="M2 2h44v44H2z"></path></svg>
        Continue with Google
        </a>
        
    </div>
          
    '''
    st.markdown(container, unsafe_allow_html=True)


def logout_button(button_text):
    if st.button(button_text):
        asyncio.run(
            revoke_token(
                client=st.session_state.client,
                token=st.session_state.token["access_token"],
            )
        )
        st.session_state.user_email = None
        st.session_state.user_id = None
        st.session_state.token = None
        st.experimental_rerun()


def login(
    client_id,
    client_secret,
    redirect_uri,
    app_name="Continue with Google",
    app_desc="",
    logout_button_text="Logout",
):
    st.session_state.client = GoogleOAuth2(client_id, client_secret)
    authorization_url = asyncio.run(
        write_authorization_url(
            client=st.session_state.client, redirect_uri=redirect_uri
        )
    )
    app_desc
    if "token" not in st.session_state:
        st.session_state.token = None

    if st.session_state.token is None:
        try:
            code = st.experimental_get_query_params()["code"]
        except:
            login_button(authorization_url, app_name, app_desc)
        else:
            # Verify token is correct:
            try:
                token = asyncio.run(
                    write_access_token(
                        client=st.session_state.client,
                        redirect_uri=redirect_uri,
                        code=code,
                    )
                )
            except:
                login_button(authorization_url, app_name, app_desc)
            else:
                # Check if token has expired:
                if token.is_expired():
                    login_button(authorization_url, app_name, app_desc)
                else:
                    st.session_state.token = token
                    st.session_state.user_id, st.session_state.user_email = asyncio.run(
                        get_user_info(
                            client=st.session_state.client, token=token["access_token"]
                        )
                    )
                    logout_button(button_text=logout_button_text)
                    return (st.session_state.user_id, st.session_state.user_email)
    else:
        logout_button(button_text=logout_button_text)
        return (st.session_state.user_id, st.session_state.user_email)
