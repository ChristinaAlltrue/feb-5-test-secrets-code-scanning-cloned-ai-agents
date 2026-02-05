#  Copyright 2023-2024 AllTrue.ai Inc
#  All Rights Reserved.
#
#  NOTICE: All information contained herein is, and remains
#  the property of AllTrue.ai Incorporated. The intellectual and technical
#  concepts contained herein are proprietary to AllTrue.ai Incorporated
#  and may be covered by U.S. and Foreign Patents,
#  patents in process, and are protected by trade secret or copyright law.
#  Dissemination of this information or reproduction of this material
#  is strictly forbidden unless prior written permission is obtained
#  from AllTrue.ai Incorporated.
"""
On launch, redirect to starter page
"""
import dotenv
import logfire
import streamlit as st

dotenv.load_dotenv()

logfire.configure(
    send_to_logfire="if-token-present",
    scrubbing=False,
)
logfire.instrument_httpx(capture_all=True)
logfire.instrument_requests()
logfire.instrument_aiohttp_client()


STARTER_PAGE = "pages/1_🤖_Basic_Chat_Bot.py"

st.switch_page(STARTER_PAGE)
