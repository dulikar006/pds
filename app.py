import json
import os
import time

import requests
import streamlit as st
from PIL import Image
from annotated_text import annotated_text

from clients.openai_client import llm

import json
import streamlit as st
import requests
import time
from PIL import Image
from annotated_text import annotated_text
from clients.openai_client import llm

BE_URL = os.environ['BE_URL']#"http://localhost:5000"


# Set up login state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Login Page
if not st.session_state.logged_in:
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        # Replace these with your actual username and password validation
        if username == "admin" and password == "password":
            st.session_state.logged_in = True
            st.success("Logged in successfully")
            st.rerun()  # Reload the app with logged-in state
        else:
            st.error("Incorrect username or password")

    # Main Content: Only visible if logged in
if st.session_state.logged_in:
    st.title("Presidential Debate 2024")

    sjb_keypoints = []
    npp_keypoints = []
    contradicttory = []

    question = st.text_input("Provide the Topic:")
    if st.button("Submit"):
        if question:
            url = f"{BE_URL}/start"
            headers = {'Content-Type': 'application/json'}
            data = {'question': question}

            # Sending POST request
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=1)
            except:
                pass

    #     if response.status_code == 200:
    #         st.success("Message sent successfully!")
    #         st.json(response.json())  # Display the response in JSON format
    #     else:
    #         st.error(f"Failed to send message. Reason: {response.text}")
    # else:
    #     st.warning("Please enter a question before submitting.")


def reset_app():
    st.session_state.clear()
    st.rerun()

    response = requests.get(f"{BE_URL}/clear")
    if response.status_code == 200:
        print("all clear")


if st.sidebar.button('Start New Debate', type="primary"):
    reset_app()

st.sidebar.markdown("---")

st.sidebar.subheader("NPP KeyPoints")
npp_keypoints_placeholder = st.sidebar.empty()  # Create a placeholder for the dynamic keypoints

st.sidebar.markdown("---")

st.sidebar.subheader("SJB KeyPoints")
sjb_keypoints_placeholder = st.sidebar.empty()  # Create a placeholder for the dynamic keypoints

#####################################################################


avatars = {
    "SJB": "opp.png",
    "NPP": "prop.png",
    "Moderator": "mod.png",
}


# Function to fetch messages from the Flask server
def fetch_messages():
    response = requests.get(f"{BE_URL}/messages")
    if response.status_code == 200:
        # print(f'flast return: {response.json()}')
        return response.json()
    return []


def generate_keypoint(content):
    try:
        prompt = f'''
        Below content is response from political party of thier perspective on {question}
        
        [content]
        {content}
        [contetn ends here]
        
        Your job is to generate 
        1. two very short, only few words, noticeable key_points to showcase & highlight their idea.
        2. three hash_tags to showcase & highlight the area and action plan.
        
        always return a json.
        return in below format.
        
         KeypointSections: 
            key_points: [insert key points here],
            hash_tags: [insert hash tags here]
        
        '''
        json_string = llm(prompt)

        first_brace_index = json_string.find('{')
        last_brace_index = json_string.rfind('}')
        extracted_json = json_string[first_brace_index:last_brace_index + 1]
        extracted_json = extracted_json.replace("'", '"')
        result_dict = json.loads(extracted_json)

        return result_dict.get('KeypointSections')
    except:
        pass


def display_keypoints_in_sidebar(party):
    main_list = None

    if party == 'SJB':
        main_list = sjb_keypoints
        placeholder = sjb_keypoints_placeholder
    elif party == 'NPP':
        main_list = npp_keypoints
        placeholder = npp_keypoints_placeholder

    key_points_str = ''
    hash_tags_str = ''

    if main_list:

        for keypoints_data in main_list:
            # Build key points as a markdown list
            key_points_str += "\n".join([f"- {point}" for point in keypoints_data['key_points']])

            # Build hashtags as a single string
            hash_tags_str += " ".join(keypoints_data['hash_tags'])

            # Combine and display in markdown
            formatted_str = f"**Key Points:**\n\n{key_points_str}\n\n**Hashtags:**\n\n{hash_tags_str}"

            # Update the placeholder with the formatted keypoints and hashtags
            # placeholder.markdown(formatted_str)
            annotated_hash_tags = [(tag, "") for tag in keypoints_data['hash_tags']]

            # Display key points and hashtags using annotated_text
            placeholder.markdown(formatted_str)
            annotated_text(*annotated_hash_tags)


def contradictory_keypoints(content_one, content_two):
    pass


# Loop to continuously check for new messages
if 'messages' not in st.session_state:
    st.session_state.messages = []


def stream_response(response):
    for char in response:
        yield char
        time.sleep(0.005)


while True:
    if st.session_state.logged_in:
        print('running')
        new_messages = fetch_messages()
        # print(new_messages)
        if new_messages:

            for msg in new_messages:
                guids = [x['guid'] for x in st.session_state.messages]
                if msg['guid'] not in guids:
                    st.session_state.messages.append(msg)

                    # Update the placeholder in Section 2 with the new keypoints
                    keypoints = generate_keypoint(msg['message'])  # Generate keypoints
                    if keypoints:
                        if msg['person'] == 'SJB':
                            sjb_keypoints.append(keypoints)
                        elif msg['person'] == 'NPP':
                            npp_keypoints.append(keypoints)

                        display_keypoints_in_sidebar(msg['person'])

                    avatar = Image.open(avatars[msg['person']])
                    # Set up the layout to display avatar alongside the message
                    cols = st.columns([1, 9])  # Adjust column width ratios as needed
                    with cols[0]:
                        st.image(avatar, width=50)
                    with cols[1]:
                        st.write_stream(stream_response(msg['message']))
                    st.markdown("---")

        time.sleep(1)  # Wait for a second before checking for new messages
