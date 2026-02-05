#!/usr/bin/env python3
"""
Test script to verify CodeInterpreterManager's ability to read image files
and process them with OCR/image analysis capabilities.
"""

import asyncio
from pathlib import Path

# Set up logfire
import logfire
from logfire import ConsoleOptions

# Configure logfire for standalone testing
logfire.configure(
    send_to_logfire=False,  # Don't send to cloud for testing
    scrubbing=False,
    console=ConsoleOptions(),  # Enable console output
)

from app.core.agents.utils.openai_utils.response_with_tool_code_interpreter import (
    CodeInterpreterResponseManager,
)


async def test_image_processing():
    """Test the code interpreter's image processing capabilities."""

    # Look for sample image files in the project
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
    sample_dirs = [
        "test_suite/sample_files",
        "test_suite/sample_files/GAM",
        "app/core/agents/action_prototype/GHCO_auditor/tools/scripts_template",
    ]

    # Find available image files
    image_files = []
    for sample_dir in sample_dirs:
        dir_path = Path(sample_dir)
        if dir_path.exists():
            for file_path in dir_path.rglob("*"):
                if file_path.suffix.lower() in image_extensions and file_path.is_file():
                    image_files.append(str(file_path))
                    print(f"Found image: {file_path}")

    if not image_files:
        raise FileNotFoundError("No image files found for testing.")

    # Now test image processing with OCR
    output_dir = Path("test_suite/sample_files/output")

    image_analysis_prompt = """Tell me what the images shown. Don't use OCR libraries, use your own visual capability"""

    try:
        print(f"\n🔍 Testing image processing with {len(image_files)} image(s)...")

        async with CodeInterpreterResponseManager("test_image_processing") as manager:
            # Upload image files
            print("📤 Uploading image files...")
            await manager.upload_files(image_files)

            # Execute image analysis
            print("🤖 Running image analysis...")
            response = await manager.execute_code(
                image_analysis_prompt,
                save_output_to=output_dir / "response_output.json",
            )

            if response.status == "completed":
                print("✓ Image analysis completed successfully")
                print(f"Response: {response.output_text[:500]}...")

                # Download all generated files
                print("📥 Downloading all results...")
                await manager.download_all_files(output_dir, exclude_file_ids=[])

                print(f"\n🎉 Test completed successfully!")
                print(f"📁 Results saved to: {output_dir}")

                # List what was created
                if output_dir.exists():
                    output_files = list(output_dir.glob("*"))
                    if output_files:
                        print(f"\n📋 Generated files:")
                        for file_path in sorted(output_files):
                            size_kb = file_path.stat().st_size / 1024
                            print(f"  - {file_path.name} ({size_kb:.1f} KB)")

            else:
                print(f"✗ Image analysis failed: {response.status}")

    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("🧪 Testing CodeInterpreterManager Image Processing Capabilities")
    print("=" * 60)

    asyncio.run(test_image_processing())
