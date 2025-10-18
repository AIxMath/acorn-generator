#!/usr/bin/env python3
"""
Main agent logic for the Acorn development agent.
"""

import logging
import os
from datetime import datetime
from typing import List

from agent.git_ops import git_add_commit_push, run_command
from agent.verification import verify_acorn_code
from agent.file_ops import (
    load_acorn_context,
    extract_next_task,
    update_todo_mark_complete,
    apply_implementation
)
from agent.llm_interface import generate_implementation
from agent.log_utils import setup_logging, create_log_entry, log_attempt, save_agent_log

MAX_FIX_ATTEMPTS = 3  # Maximum auto-fix attempts


def run_single_task(
    acornlib_path: str,
    context_file: str,
    model: str,
    task_description: str,
    auto_push: bool = True,
    confirm_before_push: bool = False,
    update_todo: bool = False,
    logger: logging.Logger = None
) -> bool:
    """Run agent for a single task. Returns True if successful."""

    # Initialize logging if not provided
    if logger is None:
        logger = setup_logging()

    # Create log entry for this task
    log_entry = create_log_entry(task_description, mode="single_task")
    start_time = datetime.now()

    task = {'description': task_description, 'type': 'manual'}
    todo_path = os.path.join(acornlib_path, "TODO.md")

    logger.info(f"📋 Starting task: {task['description']}")
    print(f"\n📋 Task: {task['description']}")

    # Load context
    logger.info("📚 Loading context...")
    print("\n📚 Loading context...")
    context = load_acorn_context(acornlib_path, context_file)

    # Try to implement with auto-fix
    error_context = None
    for attempt in range(MAX_FIX_ATTEMPTS):
        if attempt > 0:
            print(f"\n🔧 Auto-fix attempt {attempt}/{MAX_FIX_ATTEMPTS - 1}...")

        # Generate implementation
        logger.info(f"🧠 Generating implementation (attempt {attempt + 1}/{MAX_FIX_ATTEMPTS})...")
        print("\n🧠 Generating implementation with LLM...")
        implementation = generate_implementation(task, context, model, acornlib_path, error_context)

        # Log the attempt
        log_attempt(log_entry, attempt + 1, implementation, error_context)

        print(f"\n📊 Analysis: {implementation.get('analysis', 'No analysis')}")

        if 'raw_response' in implementation:
            logger.warning("⚠️ LLM returned non-JSON response")
            print(f"\n⚠️  LLM returned non-JSON response:")
            print(implementation['raw_response'][:500])
            if attempt < MAX_FIX_ATTEMPTS - 1:
                error_context = "LLM response was not valid JSON. Please respond with valid JSON format."
                continue
            else:
                logger.error("❌ Stopping due to parsing error after max attempts")
                print("\n❌ Stopping due to parsing error after max attempts")
                log_entry["final_status"] = "failed_json_parsing"
                log_entry["error_messages"].append("Failed to parse LLM response as JSON")
                save_agent_log(log_entry)
                return False

        # Apply implementation to actual files
        logger.info(f"📝 Applying implementation to {len(implementation.get('files', []))} files...")
        modified_files = apply_implementation(acornlib_path, implementation)

        if not modified_files:
            logger.info("⚠️ No files were modified")
            print("\n⚠️  No files were modified.")
            # Check if this was intentional (LLM said no changes needed)
            if implementation.get('files') == [] or len(implementation.get('files', [])) == 0:
                logger.info("✅ Task completed (no changes needed)")
                print("   LLM determined no changes are required for this task.")
                if update_todo:
                    update_todo_mark_complete(todo_path, task['description'])
                print("✅ Task completed (no changes needed)!")
                log_entry["final_status"] = "completed_no_changes"
                save_agent_log(log_entry)
                return True
            else:
                logger.error("❌ Stopping due to implementation error")
                print("   Stopping due to implementation error.")
                log_entry["final_status"] = "failed_implementation_error"
                log_entry["error_messages"].append("No files were modified but implementation indicated changes were needed")
                save_agent_log(log_entry)
                return False

        log_entry["files_modified"] = modified_files

        # Verify with ./acorn
        logger.info("🔍 Verifying code with ./acorn...")
        success, output = verify_acorn_code(acornlib_path)

        if not success:
            logger.error(f"❌ Verification failed: {output}")
            log_entry["error_messages"].append(f"Verification error: {output}")
            if attempt < MAX_FIX_ATTEMPTS - 1:
                logger.info("🔄 Rolling back for retry...")
                print(f"\n🔄 Verification failed, rolling back for retry...")
                run_command(["git", "checkout", "."], cwd=acornlib_path, check=False)
                error_context = f"Code verification failed with error:\n{output}\n\nPlease fix the errors."
                continue
            else:
                logger.error("❌ Verification failed after all attempts")
                print("\n❌ Verification failed. Rolling back changes...")
                run_command(["git", "checkout", "."], cwd=acornlib_path, check=False)
                print("🔄 Rolled back changes")
                print(f"\nStopping after {MAX_FIX_ATTEMPTS} failed attempts. Manual intervention needed.")
                log_entry["final_status"] = "failed_verification"
                save_agent_log(log_entry)
                return False

        # Success! Commit and push
        commit_msg = implementation.get('commit_message', f"feat: {task['description'][:50]}")
        logger.info(f"💾 Committing changes: {commit_msg}")
        if git_add_commit_push(acornlib_path, modified_files, commit_msg, push=auto_push, confirm_before_push=confirm_before_push):
            # Mark task as complete if requested
            if update_todo:
                update_todo_mark_complete(todo_path, task['description'])
            logger.info("✅ Task completed successfully!")
            print(f"\n✅ Task completed successfully!")

            # Calculate total time and save log
            end_time = datetime.now()
            log_entry["total_time_seconds"] = (end_time - start_time).total_seconds()
            log_entry["final_status"] = "completed_successfully"
            log_path = save_agent_log(log_entry)
            logger.info(f"📝 Task log saved to: {log_path}")
            return True
        else:
            logger.error("❌ Failed to commit/push")
            print("\n❌ Failed to commit/push.")
            log_entry["final_status"] = "failed_commit"
            log_entry["error_messages"].append("Git commit/push failed")
            save_agent_log(log_entry)
            return False

    # Should not reach here, but just in case
    log_entry["final_status"] = "failed_unknown"
    save_agent_log(log_entry)
    return False


def run_agent(
    acornlib_path: str,
    context_file: str,
    model: str,
    max_iterations: int = 10,
    auto_push: bool = True,
    confirm_before_push: bool = False,
    manual_task: str = None,
    interactive: bool = False
) -> None:
    """Run the autonomous development agent."""

    # Set up logging
    logger = setup_logging()

    print("🤖 Acorn Autonomous Development Agent Starting...")
    print(f"📂 Working directory: {acornlib_path}")
    print(f"📤 Auto-push: {auto_push}")
    if auto_push and confirm_before_push:
        print(f"⏸️  Confirmation required before push")

    # Manual task mode
    if manual_task:
        logger.info(f"🎯 Manual task mode: {manual_task}")
        print(f"🎯 Manual task mode")
        run_single_task(acornlib_path, context_file, model, manual_task, auto_push, confirm_before_push, update_todo=False, logger=logger)
        return

    # Interactive mode
    if interactive:
        logger.info("💬 Starting interactive mode")
        print(f"💬 Interactive mode - Enter tasks manually (type 'quit' or 'exit' to stop)")
        while True:
            try:
                task_input = input("\n📝 Enter task (or 'quit'): ").strip()
                if task_input.lower() in ['quit', 'exit', 'q']:
                    logger.info("👋 Exiting interactive mode")
                    print("👋 Exiting interactive mode")
                    break
                if not task_input:
                    continue

                run_single_task(acornlib_path, context_file, model, task_input, auto_push, confirm_before_push, update_todo=False, logger=logger)
            except KeyboardInterrupt:
                logger.info("👋 Interrupted - exiting interactive mode")
                print("\n\n👋 Exiting interactive mode")
                break
        return

    # TODO.md mode (original behavior)
    logger.info("📋 Starting TODO.md mode")
    print(f"📋 TODO.md mode")
    print(f"🔄 Max iterations: {max_iterations}")
    todo_path = os.path.join(acornlib_path, "TODO.md")

    for iteration in range(max_iterations):
        logger.info(f"🔄 Starting iteration {iteration + 1}/{max_iterations}")
        print(f"\n{'='*60}")
        print(f"🔄 Iteration {iteration + 1}/{max_iterations}")
        print(f"{'='*60}")

        # Extract next task
        task = extract_next_task(todo_path)
        if not task:
            logger.info("✅ No more tasks found in TODO.md")
            print("✅ No more tasks found in TODO.md!")
            print("🎉 All tasks completed!")
            break

        success = run_single_task(acornlib_path, context_file, model, task['description'], auto_push, confirm_before_push, update_todo=True, logger=logger)
        if not success:
            logger.error("❌ Task failed - stopping")
            print("\n❌ Task failed. Stopping.")
            break

    logger.info("🏁 Agent finished")
    print(f"\n{'='*60}")
    print("🏁 Agent finished")
    print(f"📝 Logs are saved in the 'logs' directory")
    print(f"{'='*60}")