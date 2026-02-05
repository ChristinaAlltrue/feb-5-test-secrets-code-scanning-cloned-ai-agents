import asyncio
from pathlib import Path
from unittest.mock import Mock

from dotenv import load_dotenv

load_dotenv()


# Mock the required dependencies
class MockActionDeps:
    def __init__(self):
        self.control_info = Mock()
        self.control_info.control_execution_id = "test-audit-123"
        self.working_dir = "test_suite/sample_files/GAM"

    async def add_log(self, log):
        print(f"LOG: {log}")


class MockRunContext:
    def __init__(self):
        self.deps = MockActionDeps()


async def test_audit_analysis_agent():
    # Import after setting up mocks
    from app.core.agents.action_prototype.GHCO_auditor.tools.audit_analysis_agent import (
        audit_analysis_agent,
    )

    # Create mock context
    ctx = MockRunContext()

    # Test parameters
    report_instructions = """
            Here is the mapping of the frequency and sample size, you have to use it when you generate the report.
                FREQUENCY_MAPPING = {
                "> 260": "Multiple Times Per Day",
                "53-260": "Daily",
                "13-52": "Weekly",
                "5-12": "Monthly",
                "3-4": "Quarterly",
                "2": "Semi-Annual",
                "1": "Annual"
                }

                SAMPLE_SIZE_MAPPING = {
                    "Multiple Times Per Day": 20,
                    "Daily": 15,
                    "Weekly": 3,
                    "Monthly": 1,
                    "Quarterly": 1,
                    "Semi-Annual": 1,
                    "Annual": 1
                }
            """
    softwares = ["AC2"]

    # Use existing sample files
    # test_files = [
    #     "test_suite/sample_files/1 GAM/Google-Ad_ManagerUsers-071124_(3) (1).csv",
    #     "test_suite/sample_files/2 ARCS/EPM3_-_RoleAssignmentReport_110624_(4).csv",
    #     "test_suite/sample_files/2 ARCS/Oracle-EPM3-RoleAssignmentReport-071024_(1).csv",
    #     "test_suite/sample_files/3 Wide Orbit/WO-UserList-AllUsers-Application-20240703_(1).xlsx",
    #     "test_suite/sample_files/3 Wide Orbit/WO-UserList-AllUsers-Application-20241104_(2).xlsx",
    #     "test_suite/sample_files/1 GAM/Google-Ad_Manager_Users-110624_(11) (1).csv"
    # ]

    test_files = [
        "app/core/agents/action_prototype/GHCO_auditor/tools/scripts_template/Detailed Testing Table - Access Provisioning.xlsx",
    ]
    test_files.extend(
        [
            str(p)
            for p in Path("test_suite/sample_files/13 AC2 Dekko provisioning").glob("*")
        ]
    )
    # print(f"Using test files: {test_files}")
    # exit()
    print(f"Testing audit analysis agent with:")
    print(f"- Softwares: {softwares}")
    print(f"- Files: {test_files}")
    print(f"- Instructions: {report_instructions}")

    try:
        result = await audit_analysis_agent(
            ctx=ctx,
            report_instructions=report_instructions,
            software_list=softwares,
            files_to_upload=test_files,
        )

        print(f"\nResult:")
        print(f"- Successful: {result.successful}")
        print(f"- Feedback: {result.feedback}")
        print(f"- Generated file: {result.generated_file}")

    except Exception as e:
        print(f"Error testing agent: {e}")


if __name__ == "__main__":
    asyncio.run(test_audit_analysis_agent())
