# MCP server
## Setup
### Google token
ref: https://developers.google.com/workspace/gmail/api/quickstart/python
#### 1. Create a project
https://console.cloud.google.com/projectcreate
#### 2. Enable API
Browse API library [here](https://console.cloud.google.com/apis/library) or click the link below.
* GMAIL
https://console.cloud.google.com/apis/enableflow;apiid=gmail.googleapis.com
* GOOGLE Drive
https://console.cloud.google.com/apis/enableflow;apiid=drive.googleapis.com
* GOOGLE Spreadsheet
https://console.cloud.google.com/apis/enableflow;apiid=sheets.googleapis.com

#### 3. Configure the OAuth
Go to Branding: https://console.cloud.google.com/auth/branding

If you have already configured the Google Auth platform, you can configure the following OAuth Consent Screen settings in Branding, Audience, and Data Access. If you see a message that says Google Auth platform not configured yet, click Get Started:
1. Under App Information, in App name, enter a name for the app.
2. In User support email, choose a support email address where users can contact you if they have questions about their consent.
3. Click Next.
4. Under Audience, select Internal.
5. Click Next.
6. Under Contact Information, enter an Email address where you can be notified about any changes to your project.
7. Click Next.
8. Under Finish, review the Google API Services User Data Policy and if you agree, select I agree to the Google API Services: User Data Policy.
9. Click Continue.
10. Click Create.

#### 4. Authorize credentials
Go to Clients: https://console.cloud.google.com/auth/clients
1. Click Create Client.
2. Click Application type > Desktop app.
3. In the Name field, type a name for the credential. This name is only shown in the Google Cloud console.
4. Click Create.
5. The newly created credential appears under "OAuth 2.0 Client IDs."
6. Save the downloaded JSON file as credentials.json, and move the file to your working directory.
7. `python google_auth_token_generator.py` to generate the token.json from credentials.json
