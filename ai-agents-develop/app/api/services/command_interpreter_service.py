from pydantic import BaseModel, Field, SecretStr
from pydantic_ai import Agent

from app.core.llm.pydanticai.openai_model import get_pydanticai_openai_llm


class FailedCommandInterpretationException(Exception):
    """Custom exception raised for errors in the command interpretation."""


class AgentPrompt(BaseModel):
    user_prompt: str
    target_information: str
    check_information: str
    username: str = Field(..., description="Username - handle securely")
    password: SecretStr = Field(..., description="Password - handle securely")
    login_instructions: str
    mfa_secret: SecretStr = Field(
        default="", description="MFA secret - stored as SecretStr"
    )


async def interpreter_llm(user_input: str) -> AgentPrompt:
    try:
        agent_system_prompt = f"""
            Your task is to analyze the input from the user and generate a command based on user's input.
            Users will provide you with a prompt that describes what they want the AI browser agent to do.
            You need to generate a command that the AI agent can execute to fulfill the user's request.
            The command should be in the following format:
            {{
                "user_prompt": "A clear, sequential set of steps that the control agent will execute. It must start with logging into the website, include all user interactions (clicks, searches, etc.), and end with an instruction to verify the check condition. If the user describes downloading a file and doing something with its contents (e.g., checking for values, extracting data, or making comparisons), it must include a reference to using the 'file processing tool' to perform that step. If the Take_Screenshot toggle is set to TRUE then instruct the agent to take a screenshot. These instructions will be passed to the supervisor agent to orchestrate the process. It should not be a list.",
                "target_information": "Describe what the screenshot should capture. This should clearly indicate the visual goal that serves as proof. If the user does not want to take a screenshot, this must be empty",
                "check_information": "Describe what the system should check for to determine if the control has passed or failed. This is a logical or visual confirmation step. If the user does not want to check or verify any information, this must be empty",
                "username": "the username for login the website. If the user does not provide a username, this can be empty",
                "password": "the password of the username to login the website. If the user does not provide a password, this can be empty",
                "login_instructions": "the instructions for the AI agent to login to the website. If the user does not provide login instructions, this can be empty",
                "mfa_secret": "the MFA secret for the username to login the website, this is optional and can be empty",
            }}
            On user_prompt, you should tell the AI agent that when to verify the information on the website based on the user input.
            You should also tell the AI agent when to take a screenshot of the website based on the user input.
            You should not put login instructions in the user_prompt, but rather in the login_instructions. You only need to say "login to the website" in the user_prompt if the login is required.
            `user_prompt` should be very clera and specific about each step the AI agent needs to take.
            DO NOT add or remove any infromation that requires the AI agent to click, scrool, or interact with the website.
            """

        agent = Agent(
            model=get_pydanticai_openai_llm(),
            system_prompt=agent_system_prompt,
            output_type=AgentPrompt,
        )
        sanitized_input = user_input.replace("{", "{{").replace("}", "}}")
        user_prompt = f" \n The information content from user is: {sanitized_input}."
        result = await agent.run(user_prompt)
        return result.output
    except Exception as e:
        raise FailedCommandInterpretationException(
            f"Failed to generate command interpretation: {str(e)}"
        ) from e
