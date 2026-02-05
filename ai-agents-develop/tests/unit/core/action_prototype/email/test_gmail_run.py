import pytest

from app.core.agents.action_prototype.email.email_reader.email_connection import (
    GmailConnection,
)


@pytest.mark.asyncio
async def test_gmail_agent_real_run():
    all_business_units = {
        "Asana": ["ACME", "Gamma", "Oracle"],
        "Gavin": ["Wide Orbit", "GAM", "ARCS"],
    }
    sender_names = ["Asana", "Gavin"]
    connection = GmailConnection()
    # extract_email_data will extract the email data from the unread_list
    # the result is a list of EmailData
    # class EmailData(BaseModel):
    #     sender: str
    #     subject: str
    #     snippet: str
    msg_list = connection.list_unread_messages()
    # list_unread_messages_by_keywords will filter the emails by sender names and the keywords. For example, it will only get the emails containing "ACME", "Gamma", "Oracle" for Asana and "Wide Orbit", "GAM", "ARCS" for Gavin
    result = await connection.list_unread_messages_by_keywords(
        sender_names=sender_names, key_words_for_each_sender=all_business_units
    )
    # response_text is a list of EmailInfo objects, unread_list is a dict of unread emails (used to mark emails as read later, it has the specific format used by google api)
    # class EmailInfo(BaseModel):
    #     business_unit: list[str]
    #     has_attachment: bool
    #     sender: str
    response_text, unread_list = result if result else ([], {})
    # This will mark the emails as read for the sender "Gavin" in all the unread_list
    connection.mark_emails_as_read(sender="Gavin", unread_list=unread_list)
