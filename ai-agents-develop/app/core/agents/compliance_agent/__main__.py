#!/usr/bin/env python3
"""
Compliance Agent Module - Simple Demo

This module demonstrates the core functionality:
1. Compliance validation with evidence files
2. Report generation using validation results

Usage:
    python -m app.core.agents.compliance_agent
"""

import asyncio
from pathlib import Path
from typing import List

import logfire

from app.core.agents.compliance_agent.agent import ComplianceAgent
from app.core.agents.compliance_agent.models import ComplianceInput, EvidenceItem


async def test_simplified_compliance_agent():
    """Test the simplified compliance agent flow."""

    # Create test data
    test_compliance_instruction = """
    Verify that the system has proper access controls in place.
    Check that user authentication is required for all sensitive operations.
    Ensure that role-based access control (RBAC) is implemented.
    """

    # Create sample compliance input with evidence
    test_evidence = [
        ComplianceInput(
            evidence=[
                EvidenceItem(
                    object_type="file", path="./test_evidence/access_control_policy.txt"
                )
            ],
            audit_result="Access control policy reviewed",
            is_passed=True,
            reason="All access controls are properly configured",
        )
    ]

    # Create test evidence file
    test_evidence_dir = Path("./test_evidence")
    test_evidence_dir.mkdir(exist_ok=True)

    test_file = test_evidence_dir / "access_control_policy.txt"
    test_file.write_text(
        """
    Access Control Policy:
    1. All users must authenticate before accessing the system
    2. Role-based access control is implemented
    3. Sensitive operations require additional authorization
    4. Audit logs are maintained for all access attempts
    """
    )

    try:
        # Test the simplified compliance agent
        agent = ComplianceAgent()

        print("Testing simplified compliance agent flow...")
        print(
            "Flow: create container → load evidence → request response → parse judgement → upload evidence → optionally generate report → update status"
        )

        # Test with report generation
        generated_files: List[Path] = []
        print("\n1. Testing with report generation:")
        compliance_result, report_result = await agent.validate_compliance_with_report(
            compliance_instruction=test_compliance_instruction,
            control_output=test_evidence,
            generated_files=generated_files,
            generate_report=True,
            report_title="Access Control Compliance Report",
        )

        print(f"✓ Compliance Result: {compliance_result.answer}")
        print(f"✓ Reasoning: {compliance_result.reasoning[:100]}...")
        print(f"✓ Feedback: {compliance_result.feedback}")
        print(
            f"✓ Compliant Evidence: {len(compliance_result.compliant_evidence)} files"
        )
        print(
            f"✓ Non-Compliant Evidence: {len(compliance_result.non_compliant_evidence)} files"
        )

        if report_result:
            print(f"✓ Report Generated: {report_result.report_generated}")
            print(f"✓ Report Filename: {report_result.response_text}")
            print(f"✓ Container ID: {report_result.container_id}")
            print(f"✓ Uploaded Files: {len(report_result.uploaded_files)}")

            # Download the report
            output_path = f"./test_output/{compliance_result.answer.lower()}_report"
            downloaded_path = await agent.download_generated_report(
                container_id=report_result.container_id,
                report_filename=report_result.response_text.strip(),
                output_path=output_path,
            )
            print(f"✓ Report downloaded to: {downloaded_path}")

        # Test without report generation
        print("\n2. Testing without report generation:")
        generated_files = []
        compliance_result_only, _ = await agent.validate_compliance_with_report(
            compliance_instruction=test_compliance_instruction,
            control_output=test_evidence,
            generated_files=generated_files,
            generate_report=False,
        )

        print(f"✓ Compliance Result (no report): {compliance_result_only.answer}")
        print(f"✓ Reasoning (no report): {compliance_result_only.reasoning[:100]}...")

        print("\n✓ All tests completed successfully!")

    except Exception as e:
        print(f"✗ Error during testing: {e}")
        logfire.error(f"Test failed: {e}")

    finally:
        # Clean up
        if agent is not None:
            await agent.cleanup()

        # Remove test files
        if test_file.exists():
            test_file.unlink()
        if test_evidence_dir.exists():
            test_evidence_dir.rmdir()


if __name__ == "__main__":
    print("Testing Simplified Compliance Agent")
    print("=" * 50)
    asyncio.run(test_simplified_compliance_agent())
    print("\n" + "=" * 50)
    print("All tests completed!")
